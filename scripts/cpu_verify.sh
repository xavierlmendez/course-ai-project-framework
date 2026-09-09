#!/bin/bash
# The interrupted harness experiment, on a CPU box with plenty of RAM (the R620).
# Answers, with evidence written to $EV:
#   1. Does qwen2.5-coder:14b emit structured tool calls at num_ctx 4096 vs 32768?
#   2. If not at 32k, does qwen3:14b?
#   3. Does a real Type B regeneration (agent loop, no sandbox) produce the entry point?
set -uo pipefail
REPO="${REPO:-$HOME/framework}"; EV="$REPO/evidence-cpu"; mkdir -p "$EV"
MODEL="${MODEL:-qwen2.5-coder:14b}"; ALT="${ALT:-qwen3:14b}"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$EV/log.txt"; }
: > "$EV/log.txt"
log "== host: $(nproc) cpus, $(free -g | awk '/Mem:/{print $2}') GB; ollama $(ollama --version 2>&1 | grep -o '[0-9.]*$'); opencode $(opencode --version)"

tooltest() { # model num_ctx label -> prints ok count
  local m="$1" ctx="$2" label="$3" ok=0; : > "$EV/tooltest-$label.txt"
  for i in 1 2 3 4 5; do
    r=$(curl -s http://127.0.0.1:11434/api/chat -d "{
      \"model\":\"$m\",\"stream\":false,\"options\":{\"num_ctx\":$ctx},
      \"messages\":[{\"role\":\"user\",\"content\":\"Use the read_file tool to read SPEC.md. Attempt $i.\"}],
      \"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"read_file\",\"description\":\"Read a file\",
        \"parameters\":{\"type\":\"object\",\"properties\":{\"path\":{\"type\":\"string\"}},\"required\":[\"path\"]}}}]}")
    if echo "$r" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("message",{}).get("tool_calls") else 1)'; then
      ok=$((ok+1)); echo "  $i: TOOL_CALL $(echo "$r" | python3 -c 'import json,sys;print(json.dumps(json.load(sys.stdin)["message"]["tool_calls"])[:100])')" >> "$EV/tooltest-$label.txt"
    else
      echo "  $i: text-only: $(echo "$r" | python3 -c 'import json,sys;print((json.load(sys.stdin).get("message",{}).get("content") or "")[:80].replace("\n"," "))')" >> "$EV/tooltest-$label.txt"
    fi
  done
  log "tooltest $m num_ctx=$ctx -> $ok/5 structured tool calls"; echo "$ok"
}

log "== 1. tool calling, $MODEL"
R4=$(tooltest "$MODEL" 4096 4k); R32=$(tooltest "$MODEL" 32768 32k)
ollama ps | tee "$EV/ollama-ps-32k.txt"

USE="$MODEL"
if [ "$R32" -lt 4 ]; then
  log "== 2. $MODEL unreliable at 32k ($R32/5); pulling $ALT"
  ollama pull "$ALT" 2>&1 | tail -1
  ollama show "$ALT" | sed -n '/Capabilities/,/^$/p' | tee "$EV/capabilities-alt.txt"
  RA=$(tooltest "$ALT" 32768 alt-32k)
  [ "$RA" -ge 4 ] && USE="$ALT"
else
  log "== 2. skipped: $MODEL calls tools at 32k"
fi

log "== 3. real regeneration (agent loop, no sandbox) with $USE at num_ctx 32768"
cd "$REPO"
P=/tmp/p1; rm -rf "$P" /tmp/runs; cp -R examples/01-morris-type-b/part-I "$P"; rm -rf "$P/runs"
python3 - "$P/project.json" "$USE" <<'PY'
import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["num_ctx"]=32768; d["base_model"]=sys.argv[2]
d["ollama_host"]="http://127.0.0.1:11434"; d["resource_host"]="127.0.0.1"; json.dump(d,open(p,"w"),indent=1)
PY
python3 - <<'PY'
p='tools/runner.py'; s=open(p).read()
if 'num_ctx' not in s:
    s=s.replace('modelfile = f"FROM {p[\'base_model\']}\\nPARAMETER temperature {t}\\nPARAMETER seed {s}\\n"',
                'modelfile = f"FROM {p[\'base_model\']}\\nPARAMETER temperature {t}\\nPARAMETER seed {s}\\nPARAMETER num_ctx {p.get(\'num_ctx\', 4096)}\\n"')
    open(p,'w').write(s); print("runner: slot models carry num_ctx")
PY
echo '{"seeds": [111, 222, 333]}' > "$P/seeds.secret.json"
python3 tools/runner.py --project "$P/project.json" --create-slots 2>&1 | tail -1 | tee -a "$EV/log.txt"
pkill -f ledger_server.py 2>/dev/null; nohup python3 tools/ledger_server.py --project "$P/project.json" --port 8080 --base-url http://127.0.0.1:8080 >/tmp/ledger.log 2>&1 &
sleep 2; curl -sf http://127.0.0.1:8080/ | head -2 | tee -a "$EV/log.txt"
S=$(date +%s)
python3 tools/runner.py --project "$P/project.json" --submission "$P/submissions/ABC123456" \
   --slot 1 --run-tag cpu --out /tmp/runs --no-sandbox --skip-slot-check 2>&1 | tail -3 | tee -a "$EV/log.txt"
log "regeneration wall: $(( $(date +%s) - S ))s"
python3 - <<'PY' | tee "$EV/regeneration-record.txt"
import json,glob
for f in glob.glob('/tmp/runs/*/*.json'):
    d=json.load(open(f)); r=d.get('regeneration',{}); out=r.get('harness_stdout_tail') or ''
    print(f"record={f}")
    print(f"entry_present={r.get('entry_present')} exit={r.get('harness_exit')} wall_s={r.get('wall_s')} env_err={r.get('environment_error')} harness_err={r.get('harness_error')}")
    print(f"complete={d.get('complete')} tests={json.dumps(d.get('tests'))[:300]}")
    print(f"tool events in stream: {out.count('\"type\":\"tool\"')}")
    print("--- stdout tail ---"); print(out[-2000:])
PY
ls -la /tmp/runs/*/*-work/ 2>/dev/null | tee -a "$EV/regeneration-record.txt"
cat "$P/ledger.tsv" 2>/dev/null | tee "$EV/ledger.tsv"
log "== done"
