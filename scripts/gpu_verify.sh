#!/bin/bash
# Harness verification on a GPU box. Answers, with evidence written to ./evidence/:
#   1. Does the reference model (qwen3:14b) emit structured tool calls at num_ctx 4096 vs 32768?
#   2. Does a real Type B regeneration through the sandbox produce an entry point?
#   3. What is the generation rate on this GPU?
#   4. If (1) fails even at 32k, does the fallback ($ALT) emit tool calls?
# Idempotent; safe to re-run. Expects the framework repo at $REPO (default ~/framework).
set -uo pipefail
REPO="${REPO:-$HOME/framework}"
EV="$REPO/evidence-gpu"; mkdir -p "$EV"
MODEL="${MODEL:-qwen3:14b}"
ALT="${ALT:-qwen3:8b}"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$EV/log.txt"; }

# ---------- 0. environment ----------
log "== environment"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>&1 | tee "$EV/gpu.txt"
if ! command -v ollama >/dev/null; then
  log "installing ollama"; curl -fsSL https://ollama.com/install.sh | sh >/dev/null 2>&1
fi
sudo systemctl enable --now ollama >/dev/null 2>&1 || (nohup ollama serve >/tmp/ollama.log 2>&1 &)
until curl -s http://127.0.0.1:11434/api/tags >/dev/null; do sleep 2; done
ollama --version | tee "$EV/ollama-version.txt"
if ! command -v docker >/dev/null; then
  log "installing docker"; curl -fsSL https://get.docker.com | sh >/dev/null 2>&1; sudo usermod -aG docker "$USER"
fi
sudo systemctl enable --now docker >/dev/null 2>&1
log "pulling $MODEL"; ollama pull "$MODEL" 2>&1 | tail -1
ollama show "$MODEL" | sed -n '/Capabilities/,/^$/p' | tee "$EV/capabilities-$MODEL.txt"

# ---------- 1. tool calling vs context size ----------
tooltest() { # model num_ctx label
  local m="$1" ctx="$2" label="$3" ok=0
  for i in 1 2 3 4 5; do
    r=$(curl -s http://127.0.0.1:11434/api/chat -d "{
      \"model\":\"$m\",\"stream\":false,\"options\":{\"num_ctx\":$ctx},
      \"messages\":[{\"role\":\"user\",\"content\":\"Use the read_file tool to read SPEC.md. Attempt $i.\"}],
      \"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"read_file\",\"description\":\"Read a file\",
        \"parameters\":{\"type\":\"object\",\"properties\":{\"path\":{\"type\":\"string\"}},\"required\":[\"path\"]}}}]}")
    if echo "$r" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("message",{}).get("tool_calls") else 1)'; then
      ok=$((ok+1)); echo "  $i: TOOL_CALL" >> "$EV/tooltest-$label.txt"
    else
      echo "  $i: text-only: $(echo "$r" | python3 -c 'import json,sys;print((json.load(sys.stdin).get("message",{}).get("content") or "")[:80].replace("\n"," "))')" >> "$EV/tooltest-$label.txt"
    fi
  done
  log "tooltest $m num_ctx=$ctx -> $ok/5 structured tool calls"
  echo "$ok"
}
log "== 1. tool calling"
: > "$EV/tooltest-4k.txt";  R4=$(tooltest "$MODEL" 4096 4k)
: > "$EV/tooltest-32k.txt"; R32=$(tooltest "$MODEL" 32768 32k)

# ---------- 2. throughput ----------
log "== 2. throughput"
curl -s http://127.0.0.1:11434/api/generate -d "{\"model\":\"$MODEL\",\"prompt\":\"Write a Python function that reverses a string and explain it.\",\"stream\":false,\"options\":{\"num_predict\":300,\"num_ctx\":32768}}" \
 | python3 -c 'import json,sys; d=json.load(sys.stdin); e=d["eval_count"]; t=d["eval_duration"]/1e9; p=d.get("prompt_eval_duration",0)/1e9; print(f"eval_count={e} eval_s={t:.1f} tok_per_s={e/t:.2f} prompt_s={p:.2f}")' | tee "$EV/throughput.txt"
ollama ps | tee "$EV/ollama-ps.txt"

# ---------- 3. real Type B regeneration through the sandbox ----------
log "== 3. real regeneration (sandbox), example 01 part-I-opening"
cd "$REPO"
sudo docker build -q -t harness-sandbox tools/sandbox/ >/dev/null 2>&1 && log "sandbox image built" || log "sandbox build FAILED"
P=/tmp/p1; rm -rf "$P" /tmp/runs; cp -R examples/01-morris-type-b/part-I-opening "$P"; rm -rf "$P/runs"
# use 32k context in the slot models so the harness has room for its tool schemas
python3 - "$P/project.json" <<'PY'
import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["num_ctx"]=32768; json.dump(d,open(p,"w"),indent=1)
PY
python3 - <<'PY'
import re,io
p='tools/runner.py'; s=open(p).read()
if 'num_ctx' not in s:
    s=s.replace('modelfile = f"FROM {p[\'base_model\']}\\nPARAMETER temperature {t}\\nPARAMETER seed {s}\\n"',
                'modelfile = f"FROM {p[\'base_model\']}\\nPARAMETER temperature {t}\\nPARAMETER seed {s}\\nPARAMETER num_ctx {p.get(\'num_ctx\', 4096)}\\n"')
    open(p,'w').write(s); print("runner: slots carry num_ctx")
PY
echo '{"seeds": [111, 222, 333]}' > "$P/seeds.secret.json"
python3 tools/runner.py --project "$P/project.json" --create-slots 2>&1 | tail -1 | tee -a "$EV/log.txt"
# serve the resource for the harness
nohup python3 tools/ledger_server.py --project "$P/project.json" --port 8080 --base-url http://host.docker.internal:8080 >/tmp/ledger.log 2>&1 &
sleep 2
S=$(date +%s)
sudo -E python3 tools/runner.py --project "$P/project.json" --submission "$P/submissions/ABC123456" \
   --slot 1 --run-tag gpu --out /tmp/runs --skip-slot-check 2>&1 | tail -3 | tee -a "$EV/log.txt"
log "regeneration wall: $(( $(date +%s) - S ))s"
python3 - <<'PY' | tee "$EV/regeneration-record.txt"
import json,glob
for f in glob.glob('/tmp/runs/*/*.json'):
    d=json.load(open(f)); r=d.get('regeneration',{})
    print(f"record={f}")
    print(f"entry_present={r.get('entry_present')} exit={r.get('harness_exit')} wall_s={r.get('wall_s')} env_err={r.get('environment_error')} harness_err={r.get('harness_error')}")
    print(f"complete={d.get('complete')} tests={json.dumps(d.get('tests'))[:300]}")
    out=r.get('harness_stdout_tail') or ''
    print(f"tool events in stream: {out.count('\"type\":\"tool\"')}")
    print("--- stdout tail ---"); print(out[-1500:])
PY
ls -la /tmp/runs/*/*-work/ 2>/dev/null | tee -a "$EV/regeneration-record.txt"
cp /tmp/ledger.log "$EV/" 2>/dev/null; cat "$P/ledger.tsv" 2>/dev/null | tee "$EV/ledger.tsv"

# ---------- 4. alternative model if needed ----------
if [ "${R32:-0}" -lt 5 ]; then
  log "== 4. $MODEL unreliable at 32k ($R32/5); trying $ALT"
  ollama pull "$ALT" 2>&1 | tail -1
  : > "$EV/tooltest-alt-32k.txt"; RA=$(tooltest "$ALT" 32768 alt-32k)
  log "$ALT num_ctx=32768 -> $RA/5"
fi
log "== done"; ls -la "$EV"
