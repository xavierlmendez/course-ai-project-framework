#!/usr/bin/env python3
"""TA regeneration runner. Standard library + Docker + Ollama.

Type B: for each submission, run K regenerations of SPEC.md through the
reference harness in a sandbox, then run the hidden tests on each result.
Type A: run the hidden tests once on the submitted solution, in a sandbox.

    runner.py --project project.json (--submissions DIR | --submission DIR)
              [--out runs/] [--status status.csv] [--run-tag grading]
              [--slot N] [--tests DIR] [--type A|B] [--dry-run] [--no-sandbox]
    runner.py --project project.json --create-slots

Records: <out>/<submission_id>/k<N>.json (Type B) or <out>/<id>/a.json (Type A).
A record with "complete": true is skipped on rerun, so an interrupted batch
resumes with the same command.

project.json keys (see tools/README.md for the full schema):
  type, entry, python, resource_host, ollama_host, base_model, k, temperatures,
  seeds_file, regeneration_timeout_s, test_timeout_s, hidden_tests, public_tests,
  categories, wrapper_prompt, sandbox_image, variants{generator}
"""
import argparse
import csv
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WRAPPER = (
    "Read SPEC.md in the current directory and carry out its instructions exactly. "
    "The finished program must be a file named {entry} in the current directory. "
    "Do not ask questions; make reasonable choices and finish."
)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def load_project(path):
    with open(path) as fh:
        p = json.load(fh)
    p["_dir"] = os.path.dirname(os.path.abspath(path))
    p.setdefault("type", "B")
    p.setdefault("entry", "solve.py")
    p.setdefault("python", "python3")
    p.setdefault("k", 3)
    p.setdefault("temperatures", [0.2, 0.6, 1.0])
    p.setdefault("seeds_file", "seeds.secret.json")
    p.setdefault("regeneration_timeout_s", 1200)
    p.setdefault("test_timeout_s", 10)
    p.setdefault("hidden_tests", "tests/hidden")
    p.setdefault("sandbox_image", "harness-sandbox")
    p.setdefault("ollama_host", "http://host.docker.internal:11434")
    p.setdefault("wrapper_prompt", DEFAULT_WRAPPER)
    p.setdefault("slot_prefix", "ref-" + p.get("name", "project") + "-slot")
    return p


def rel(p, key):
    return os.path.join(p["_dir"], p[key])


def load_seeds(p):
    path = os.path.join(p["_dir"], p["seeds_file"])
    if not os.path.exists(path):
        sys.exit(f"seeds file missing: {path} (create {{\"seeds\": [s1, s2, s3]}}; keep it secret until grades are out)")
    with open(path) as fh:
        seeds = json.load(fh)["seeds"]
    if len(seeds) != p["k"] or len(p["temperatures"]) != p["k"]:
        sys.exit("k, temperatures and seeds must all have the same length")
    return seeds


def load_status(path):
    """status.csv: student_id,status,grad,note -> {id: row}. Missing file = everyone eligible."""
    if not path:
        return {}
    with open(path, newline="") as fh:
        return {r["student_id"]: r for r in csv.DictReader(fh)}


def sh(cmd, timeout=None, cwd=None, dry=False):
    if dry:
        print("  $ " + " ".join(cmd))
        return 0, "", "", 0.0
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr, time.time() - t0
    except subprocess.TimeoutExpired as e:
        return None, (e.stdout or "") if isinstance(e.stdout, str) else "", (e.stderr or "") if isinstance(e.stderr, str) else "", time.time() - t0


# ---------- slot models ----------

def create_slots(p, dry):
    seeds = load_seeds(p)
    for i, (t, s) in enumerate(zip(p["temperatures"], seeds), 1):
        name = f"{p['slot_prefix']}{i}"
        modelfile = f"FROM {p['base_model']}\nPARAMETER temperature {t}\nPARAMETER seed {s}\n"
        print(f"creating {name}: temperature={t} seed=<secret>")
        if dry:
            print(modelfile)
            continue
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".Modelfile") as tf:
            tf.write(modelfile)
        code, out, err, _ = sh(["ollama", "create", name, "-f", tf.name])
        os.unlink(tf.name)
        if code != 0:
            sys.exit(f"ollama create failed for {name}: {err}")
    print("slots ready. Do not commit seeds.secret.json.")


# ---------- sandbox ----------

def docker_base(p, workdir, extra_env=None, network=True, tests_dir=None):
    cmd = ["docker", "run", "--rm", "-i",
           "-v", f"{os.path.abspath(workdir)}:/work", "-w", "/work",
           "-v", f"{HERE}:/tools:ro"]
    if tests_dir:
        cmd += ["-v", f"{os.path.abspath(tests_dir)}:/tests:ro"]
    if network:
        allow = ",".join(dict.fromkeys(h for h in [p.get("resource_host"), host_of(p["ollama_host"])] + p.get("extra_allow_hosts", []) if h))
        cmd += ["--cap-add", "NET_ADMIN", "--add-host", "host.docker.internal:host-gateway",
                "-e", f"ALLOW_HOSTS={allow}", "-e", f"OLLAMA_HOST={p['ollama_host']}"]
    else:
        cmd += ["--network", "none"]
    for k, v in (extra_env or {}).items():
        cmd += ["-e", f"{k}={v}"]
    cmd += ["--memory", p.get("sandbox_memory", "2g"), "--pids-limit", "256", p["sandbox_image"]]
    return cmd


def host_of(url):
    return url.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]


def write_opencode_config(p, workdir, slot_model):
    """OpenCode config so the sandbox talks to the pinned slot model with tools auto-approved.
    Shape follows opencode.ai/docs/providers (Ollama via openai-compatible); verify during calibration."""
    cfg = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            "ollama": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Ollama (reference)",
                "options": {"baseURL": p["ollama_host"].rstrip("/") + "/v1"},
                "models": {slot_model: {"name": slot_model}},
            }
        },
        "model": f"ollama/{slot_model}",
        "permission": {"edit": "allow", "bash": "allow", "webfetch": "allow"},
        "share": "disabled",
    }
    with open(os.path.join(workdir, "opencode.json"), "w") as fh:
        json.dump(cfg, fh, indent=2)


# ---------- tests ----------

def resolve_tests(p, sub_dir, override, dry):
    """Hidden tests dir, generating per-variant tests if the project uses variants."""
    if override:
        return override, None
    base = rel(p, "hidden_tests")
    v = p.get("variants")
    if not v:
        return base, None
    vf = os.path.join(sub_dir, "variant.txt")
    if not os.path.exists(vf):
        return None, "variant.txt missing in submission"
    variant = open(vf).read().strip()
    gen_out = tempfile.mkdtemp(prefix="hidden-")
    code, out, err, _ = sh([p["python"], os.path.join(p["_dir"], v["generator"]), "--variant", variant, "--out", gen_out], dry=dry)
    if code not in (0, None) and not dry:
        return None, f"generator failed: {err[-300:]}"
    return gen_out, None


def run_tests(p, workdir, tests_dir, sandbox, dry):
    if sandbox:
        cmd = docker_base(p, workdir, network=False, tests_dir=tests_dir) + [
            "python3", "/tools/run_tests.py", "--solution", "/work", "--tests", "/tests",
            "--entry", p["entry"], "--timeout", str(p["test_timeout_s"]), "--json"]
    else:
        cmd = [p["python"], os.path.join(HERE, "run_tests.py"), "--solution", workdir, "--tests", tests_dir,
               "--entry", p["entry"], "--timeout", str(p["test_timeout_s"]), "--json"]
    code, out, err, wall = sh(cmd, timeout=3600, dry=dry)
    if dry:
        return {"dry_run": True}
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return {"solution_started": False, "categories": {}, "error": (err or out)[-500:]}


# ---------- regeneration ----------

def regenerate(p, sub_dir, workdir, slot, seed, run_tag, sandbox, dry):
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    shutil.copytree(sub_dir, workdir, ignore=shutil.ignore_patterns("PROCESS.md", "WRITTEN.md", ".git"))
    slot_model = f"{p['slot_prefix']}{slot}"
    write_opencode_config(p, workdir, slot_model)
    prompt = p["wrapper_prompt"].format(entry=p["entry"])
    env = {"RUN_TAG": run_tag, "SLOT_MODEL": slot_model, "PROMPT": prompt}
    if sandbox:
        cmd = docker_base(p, workdir, extra_env=env, network=True) + ["regenerate"]
    else:
        cmd = ["opencode", "run", "-m", f"ollama/{slot_model}", "--format", "json", prompt]
    code, out, err, wall = sh(cmd, timeout=p["regeneration_timeout_s"], cwd=None if sandbox else workdir, dry=dry)
    timed_out = code is None
    if timed_out and sandbox and not dry:
        subprocess.run(["docker", "ps", "-q", "--filter", f"volume={os.path.abspath(workdir)}"], capture_output=True)
    return {"harness_exit": code, "timed_out": timed_out, "wall_s": round(wall, 1),
            "harness_stdout_tail": out[-3000:], "harness_stderr_tail": err[-1500:],
            "entry_present": os.path.exists(os.path.join(workdir, p["entry"]))}


def record_path(out, sid, name):
    d = os.path.join(out, sid)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def already_done(path):
    if not os.path.exists(path):
        return False
    try:
        return json.load(open(path)).get("complete") is True
    except Exception:
        return False


def process_type_b(p, sid, sub_dir, out, seeds, run_tag, slots, tests_override, sandbox, dry):
    tests_dir, why = resolve_tests(p, sub_dir, tests_override, dry)
    if why:
        print(f"  {sid}: SKIP ({why})")
        return
    for slot in slots:
        rp = record_path(out, sid, f"k{slot}.json")
        if already_done(rp):
            print(f"  {sid} k{slot}: done, skipping")
            continue
        workdir = os.path.join(out, sid, f"k{slot}-work")
        print(f"  {sid} k{slot}: temperature={p['temperatures'][slot-1]} tag={run_tag}-k{slot}")
        rec = {"submission": sid, "type": "B", "slot": slot, "temperature": p["temperatures"][slot - 1],
               "seed": seeds[slot - 1], "run_tag": f"{run_tag}-k{slot}", "started": now()}
        rec["regeneration"] = regenerate(p, sub_dir, workdir, slot, seeds[slot - 1], f"{run_tag}-k{slot}", sandbox, dry)
        rec["tests"] = run_tests(p, workdir, tests_dir, sandbox, dry) if rec["regeneration"]["entry_present"] or dry \
            else {"solution_started": False, "categories": {}, "error": "no entry point produced"}
        rec["ended"] = now()
        rec["complete"] = not dry
        with open(rp, "w") as fh:
            json.dump(rec, fh, indent=2)


def process_type_a(p, sid, sub_dir, out, tests_override, sandbox, dry):
    rp = record_path(out, sid, "a.json")
    if already_done(rp):
        print(f"  {sid}: done, skipping")
        return
    tests_dir, why = resolve_tests(p, sub_dir, tests_override, dry)
    if why:
        print(f"  {sid}: SKIP ({why})")
        return
    workdir = os.path.join(out, sid, "a-work")
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    shutil.copytree(sub_dir, workdir, ignore=shutil.ignore_patterns(".git"))
    print(f"  {sid}: hidden tests")
    rec = {"submission": sid, "type": "A", "started": now()}
    rec["tests"] = run_tests(p, workdir, tests_dir, sandbox, dry)
    rec["ended"] = now()
    rec["complete"] = not dry
    with open(rp, "w") as fh:
        json.dump(rec, fh, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--submissions", help="directory of submission directories")
    ap.add_argument("--submission", help="one submission directory")
    ap.add_argument("--out", default="runs")
    ap.add_argument("--status", help="status.csv; only rows with status 'graded' or 'appeal' are run")
    ap.add_argument("--run-tag", default="grading")
    ap.add_argument("--slot", type=int, help="run only this slot (1..k); appeals use the middle slot")
    ap.add_argument("--tests", help="override the tests directory (e.g. tests/public for a practice run)")
    ap.add_argument("--type", choices=["A", "B"])
    ap.add_argument("--create-slots", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print commands, write nothing complete")
    ap.add_argument("--no-sandbox", action="store_true", help="run on the host (practice only; never for grading)")
    a = ap.parse_args()

    p = load_project(a.project)
    if a.create_slots:
        return create_slots(p, a.dry_run)
    ptype = a.type or p["type"]
    sandbox = not a.no_sandbox
    if not sandbox:
        print("WARNING: --no-sandbox is for student practice runs only", file=sys.stderr)

    if a.submission:
        subs = [(os.path.basename(os.path.abspath(a.submission)), os.path.abspath(a.submission))]
    elif a.submissions:
        subs = sorted((d, os.path.join(a.submissions, d)) for d in os.listdir(a.submissions)
                      if os.path.isdir(os.path.join(a.submissions, d)))
    else:
        sys.exit("give --submissions or --submission")
    status = load_status(a.status)
    if status:
        subs = [(s, d) for s, d in subs if status.get(s, {}).get("status") in ("graded", "appeal")]

    os.makedirs(a.out, exist_ok=True)
    seeds = load_seeds(p) if ptype == "B" else None
    slots = [a.slot] if a.slot else list(range(1, p["k"] + 1))
    print(f"{len(subs)} submissions, type {ptype}, sandbox={'on' if sandbox else 'OFF'}, out={a.out}")
    for sid, d in subs:
        if ptype == "B":
            process_type_b(p, sid, d, a.out, seeds, a.run_tag, slots, a.tests, sandbox, a.dry_run)
        else:
            process_type_a(p, sid, d, a.out, a.tests, sandbox, a.dry_run)
    print("done")


if __name__ == "__main__":
    main()
