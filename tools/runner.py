#!/usr/bin/env python3
"""TA regeneration runner. Standard library + Docker + Ollama.

Type B: for each submission, run K regenerations of SPEC.md through the
reference harness in a sandbox, then run the hidden tests on each result.
Type A: run the hidden tests once on the submitted solution, in a sandbox.

    runner.py --project project.json (--submissions DIR | --submission DIR)
              [--out runs/] [--status status.csv] [--run-tag grading]
              [--slot N] [--tests DIR] [--type A|B] [--dry-run] [--no-sandbox]
    runner.py --project project.json --submission DIR --practice
    runner.py --project project.json --create-slots

--practice is the student command. It needs no TA secret and no prepared machine:
it runs on the host, tags the run "practice", runs the project's public suite
instead of the hidden one, writes seeds.practice.json if the secret seeds are not
there, and creates the pinned slot models if the model server does not have them.

Records: <out>/<submission_id>/k<N>.json (Type B) or <out>/<id>/a.json (Type A).
A record with "complete": true is skipped on rerun, so an interrupted batch
resumes with the same command. --dry-run writes <tag>-k<N>.dry.json beside a
<tag>-k<N>-dry-work directory; nothing downstream reads a *.dry.json record.

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
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WRAPPER = (
    "Read {spec} in the current directory and carry out its instructions exactly. "
    "The finished program must be a file named {entry} in the current directory. "
    "Do not ask questions; make reasonable choices and finish."
)

# How many environment failures in a row before the batch stops. An isolated failure
# leaves that slot incomplete and the batch continues; a run of them means the machine
# is broken and continuing would score a whole cohort against a dead model server.
CONSECUTIVE_FAILURE_LIMIT = 3

# stderr fragments that mean "the environment is broken", not "the specification failed".
ENVIRONMENT_MARKERS = (
    "cannot connect to the docker daemon", "docker: error response from daemon",
    "no such host", "connection refused", "connection reset by peer",
    "no space left on device", "cannot allocate memory",
    "error: model", "pull model manifest", "ollama", "executable file not found",
)


class SubmissionError(Exception):
    """The submission path is not something that may be handed to the harness."""


class BatchAborted(Exception):
    """Too many consecutive environment failures; the batch stopped."""


class NothingGraded(Exception):
    """Every submission was skipped. Almost always a roster or status mismatch."""


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def load_project(path):
    with open(path) as fh:
        p = json.load(fh)
    p["_dir"] = os.path.dirname(os.path.abspath(path))
    p["_path"] = os.path.abspath(path)
    p.setdefault("type", "B")
    p.setdefault("entry", "solve.py")
    p.setdefault("python", "python3")
    p.setdefault("k", 3)
    p.setdefault("temperatures", [0.2, 0.6, 1.0])
    p.setdefault("seeds_file", "seeds.secret.json")
    p.setdefault("regeneration_timeout_s", 1200)
    p.setdefault("test_timeout_s", 10)
    p.setdefault("hidden_tests", "tests/hidden")
    p.setdefault("public_tests", "tests/public")
    p.setdefault("sandbox_image", "harness-sandbox")
    p.setdefault("ollama_host", "http://host.docker.internal:11434")
    # The agent loop's tool schemas do not fit Ollama's 4096-token default context, and a
    # slot that overflows it silently truncates the prompt (measured 2026-09-08/09).
    p.setdefault("num_ctx", 32768)
    p.setdefault("spec", "SPEC.md")
    p.setdefault("wrapper_prompt", DEFAULT_WRAPPER)
    p.setdefault("slot_prefix", "ref-" + p.get("name", "project") + "-slot")
    return p


def rel(p, key):
    return os.path.join(p["_dir"], p[key])


def wrapper_prompt(p):
    """The instruction handed to the harness. Identical for every student in a part."""
    return p["wrapper_prompt"].format(entry=p["entry"], spec=p["spec"])


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


# A missing binary raises FileNotFoundError deep inside subprocess, which reached the
# student as a raw traceback after "slots ready". Each one gets the sentence that says
# what to install.
MISSING_TOOL = {
    "opencode": "opencode is not installed or not on PATH; see templates/student-primer.md",
    "docker": "docker is not installed or not on PATH; a sandboxed run needs it "
              "(build the image with `docker build -t harness-sandbox tools/sandbox/`), "
              "or use --practice to run on the host",
    "ollama": "the ollama CLI is not installed or not on PATH; see templates/student-primer.md",
}


def missing_tool_message(cmd):
    exe = os.path.basename(cmd[0]) if cmd else ""
    return MISSING_TOOL.get(exe, f"{exe or 'the command'} is not installed or not on PATH")


def require_binary(exe):
    """Stop before anything is written if a binary the run needs is not on PATH.

    A student's practice run used to write seeds.practice.json, create three slot
    models and print "slots ready" before the first subprocess call reported that
    opencode was missing. The check the run depends on belongs first.
    """
    if shutil.which(exe) is None:
        sys.exit(missing_tool_message([exe]))


def require_run_binaries(ptype, sandbox):
    """The binaries a regeneration run cannot proceed without, checked in one place."""
    if sandbox:
        require_binary("docker")
        return
    if ptype == "B":
        require_binary("opencode")
        require_binary("ollama")


def sh(cmd, timeout=None, cwd=None, dry=False, env=None):
    if dry:
        print("  $ " + " ".join(cmd))
        return 0, "", "", 0.0
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr, time.time() - t0
    except FileNotFoundError:
        sys.exit(missing_tool_message(cmd))
    except subprocess.TimeoutExpired as e:
        return None, (e.stdout or "") if isinstance(e.stdout, str) else "", (e.stderr or "") if isinstance(e.stderr, str) else "", time.time() - t0


# ---------- slot models ----------

def slot_parameters(p, slot):
    """Ask the model server what a slot model's effective parameters actually are."""
    url = host_side_ollama(p).rstrip("/") + "/api/show"
    body = json.dumps({"name": f"{p['slot_prefix']}{slot}"}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    params = {}
    for line in (data.get("parameters") or "").splitlines():
        bits = line.split(None, 1)
        if len(bits) == 2:
            params[bits[0].strip()] = bits[1].strip()
    return params


def verify_slots(p, seeds):
    """Fail loudly if the best-of-K schedule is not actually reaching the model.

    The schedule is pinned in each slot's Modelfile. Measurement on 2026-09-08 showed the
    harness sends no sampling parameters of its own, so the Modelfile governs, but that is
    a property of one harness version. If a future release starts sending a default, every
    slot would run at the same temperature and best-of-K would be three seeds at one
    temperature while the handout claimed 0.2 / 0.6 / 1.0. Checked before every batch.
    """
    problems = []
    seen = {}
    for i, want in enumerate(p["temperatures"], start=1):
        try:
            params = slot_parameters(p, i)
        except Exception as e:
            problems.append(f"slot {i}: could not read parameters from the model server ({e})")
            continue
        got_t, got_s = params.get("temperature"), params.get("seed")
        if got_t is None:
            problems.append(f"slot {i}: model has no temperature parameter")
        elif abs(float(got_t) - float(want)) > 1e-6:
            problems.append(f"slot {i}: effective temperature {got_t}, schedule says {want}")
        if got_s is None:
            problems.append(f"slot {i}: model has no seed parameter")
        elif seeds and str(got_s) != str(seeds[i - 1]):
            problems.append(f"slot {i}: effective seed does not match seeds.secret.json")
        want_ctx = p.get("num_ctx", 32768)
        got_c = params.get("num_ctx")
        if got_c is None:
            problems.append(f"slot {i}: model has no num_ctx parameter; it will run at Ollama's "
                            f"4096 default, which the agent loop's tool schemas do not fit "
                            f"(project says {want_ctx}). Re-run --create-slots.")
        else:
            try:
                mismatch = int(got_c) != int(want_ctx)
            except (TypeError, ValueError):
                mismatch = str(got_c) != str(want_ctx)
            if mismatch:
                problems.append(f"slot {i}: effective num_ctx {got_c}, project says {want_ctx}")
        seen[i] = got_t
    distinct = {v for v in seen.values() if v is not None}
    if len(seen) > 1 and len(distinct) == 1:
        problems.append(f"every slot reports temperature {distinct.pop()}: the schedule is not reaching the model")
    return problems


def ollama_env(p):
    """Environment for the `ollama` CLI so it talks to *this project's* model server.

    Without OLLAMA_HOST the CLI targets whatever it defaults to, so a project pointing at
    a shared box silently created its slot models on the student's own laptop instead.
    """
    return dict(os.environ, OLLAMA_HOST=host_side_ollama(p))


def model_server_reachable(p):
    url = host_side_ollama(p).rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=10):
            return True
    except Exception:
        return False


def unreachable_message(p):
    return (f"cannot reach the model server at {host_side_ollama(p)} "
            f"(project.json ollama_host={p['ollama_host']!r}, "
            f"ollama_host_local={p.get('ollama_host_local')!r}). "
            "Start Ollama (`ollama serve`), or set `ollama_host` / `ollama_host_local` in "
            "project.json to the address this machine can reach it on.")


def require_model_server(p):
    if not model_server_reachable(p):
        sys.exit(unreachable_message(p))


def create_slots(p, dry):
    seeds = load_seeds(p)
    num_ctx = p.get("num_ctx", 32768)
    if not dry:
        # Both checks come before the first Modelfile is written: a missing CLI or an
        # unreachable server used to surface halfway through creating the slots.
        require_binary("ollama")
        require_model_server(p)
    for i, (t, s) in enumerate(zip(p["temperatures"], seeds), 1):
        name = f"{p['slot_prefix']}{i}"
        modelfile = (f"FROM {p['base_model']}\nPARAMETER temperature {t}\n"
                     f"PARAMETER seed {s}\nPARAMETER num_ctx {num_ctx}\n")
        print(f"creating {name}: temperature={t} seed=<redacted> num_ctx={num_ctx}")
        if dry:
            print(f"FROM {p['base_model']}\nPARAMETER temperature {t}\n"
                  f"PARAMETER seed <redacted>\nPARAMETER num_ctx {num_ctx}")
            continue
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".Modelfile") as tf:
            tf.write(modelfile)
        code, out, err, _ = sh(["ollama", "create", name, "-f", tf.name], env=ollama_env(p))
        os.unlink(tf.name)
        if code != 0:
            sys.exit(f"ollama create failed for {name}: {err}")
    print("slots ready. Do not commit seeds.secret.json.")


# ---------- practice runs (F-29) ----------

PRACTICE_SEEDS_FILE = "seeds.practice.json"


def ensure_practice_seeds(p):
    """Point the project at seeds a student actually has.

    The grading seeds are secret until grades are out, so a student cannot run the
    grading command as written. Any three integers give the same temperature
    schedule with a different draw, which is all a practice run needs. Written once
    and reused, so a student's practice runs stay comparable to each other.
    """
    if os.path.exists(os.path.join(p["_dir"], p["seeds_file"])):
        return p["seeds_file"]
    path = os.path.join(p["_dir"], PRACTICE_SEEDS_FILE)
    if not os.path.exists(path):
        seeds = [random.randint(1, 2 ** 31 - 1) for _ in range(p["k"])]
        with open(path, "w") as fh:
            json.dump({"seeds": seeds}, fh, indent=1)
            fh.write("\n")
        print(f"wrote {path}: {p['k']} seeds of your own. The grading seeds are different and secret.")
    p["seeds_file"] = PRACTICE_SEEDS_FILE
    return PRACTICE_SEEDS_FILE


def slot_models_missing(p):
    """Slots the model server does not have. A student has created none of them."""
    missing = []
    for i in range(1, p["k"] + 1):
        try:
            slot_parameters(p, i)
        except Exception:
            missing.append(i)
    return missing


def practice_setup(p, a, ptype):
    """Turn --practice into the flags a student would otherwise have to know.

    Implies --no-sandbox (the grading image is a TA artefact), tags the run
    "practice" so it can never overwrite a grading record, and runs the public
    suite, which is the only suite a student has.
    """
    a.no_sandbox = True
    a.skip_slot_check = True
    if a.run_tag == "grading":
        a.run_tag = "practice"
    if not a.tests:
        a.tests = rel(p, "public_tests")
        if not os.path.isdir(a.tests) and not a.dry_run:
            sys.exit(f"--practice runs the public suite, and this project has none at {a.tests}. "
                     "Pass --tests DIR if yours lives elsewhere.")
    if ptype != "B":
        return
    ensure_practice_seeds(p)
    if a.dry_run:
        return
    require_model_server(p)
    missing = slot_models_missing(p)
    if missing:
        print(f"slot models {missing} are not on {host_side_ollama(p)}; creating them")
        create_slots(p, a.dry_run)


# ---------- sandbox ----------

def endpoints(p):
    """host:port pairs the sandbox may reach. Ports matter: opening every port on the
    grading machine would expose the model server's management API, which can read the
    secret seeds and overwrite the pinned slot models."""
    out = []
    res_host, res_port = p.get("resource_host"), p.get("resource_port", 8080)
    if res_host:
        out.append(f"{res_host}:{res_port}")
    o = urllib.parse.urlsplit(p["ollama_host"])
    out.append(f"{o.hostname}:{o.port or 11434}")
    for extra in p.get("extra_allow_endpoints", []):
        out.append(extra)
    return ",".join(dict.fromkeys(out))


def docker_base(p, workdir, extra_env=None, network=True, tests_dir=None, name=None,
                project_file=None):
    cmd = ["docker", "run", "--rm", "-i",
           "-v", f"{os.path.abspath(workdir)}:/work", "-w", "/work",
           "-v", f"{HERE}:/tools:ro"]
    if name:
        cmd += ["--name", name]
    if tests_dir:
        # Mounted inside /root, which is 0700 and root-owned, so the unprivileged user
        # cannot traverse to it whatever the host's permissions on the mount are. The
        # entrypoint stages a root-only copy at /tests for the test runner itself.
        cmd += ["-v", f"{os.path.abspath(tests_dir)}:/root/tests-src:ro"]
    if project_file:
        # Read-only so run_tests.py can enforce the declared equivalence policy inside
        # the container. It carries no secrets: seeds live in seeds.secret.json.
        cmd += ["-v", f"{os.path.abspath(project_file)}:/project.json:ro"]
    if network:
        cmd += ["--cap-add", "NET_ADMIN", "--add-host", "host.docker.internal:host-gateway",
                "-e", f"ALLOW_ENDPOINTS={endpoints(p)}", "-e", f"OLLAMA_HOST={p['ollama_host']}"]
    else:
        cmd += ["--network", "none"]
    for k, v in (extra_env or {}).items():
        cmd += ["-e", f"{k}={v}"]
    cmd += ["--memory", p.get("sandbox_memory", "2g"), "--pids-limit", "256", p["sandbox_image"]]
    return cmd


def host_of(url):
    return url.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]


# Names that only resolve inside a container. A host-side check that dials one of these
# fails on a perfectly healthy machine, which is exactly what happened to the slot check.
CONTAINER_ONLY_HOSTS = ("host.docker.internal", "gateway.docker.internal", "host.containers.internal")


def host_side_ollama(p):
    """The model server's URL as reachable from *this* process, not from the sandbox.

    `ollama_host` is written for the container. Set `ollama_host_local` when the model
    server is somewhere else entirely (a shared box); otherwise a container-only name is
    translated to loopback.
    """
    if p.get("ollama_host_local"):
        return p["ollama_host_local"]
    url = p["ollama_host"]
    for name in CONTAINER_ONLY_HOSTS:
        if name in url:
            return url.replace(name, "127.0.0.1")
    return url


def write_opencode_config(p, workdir, slot_model, temperature=None, seed=None, sandbox=True):
    """OpenCode config so the sandbox talks to the pinned slot model with tools auto-approved.

    Temperature and seed are pinned in the Ollama Modelfile (see create_slots). They are
    repeated here deliberately: measurement on 2026-09-08 showed OpenCode 1.18.29 sends
    no sampling parameters, so the Modelfile governs, but a release that started sending
    its own defaults would silently flatten the best-of-K schedule. Setting them in both
    places means whichever wins carries the right value.
    """
    model_opts = {"name": slot_model}
    if temperature is not None:
        model_opts["options"] = {"temperature": temperature}
        if seed is not None:
            model_opts["options"]["seed"] = seed
    cfg = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            "ollama": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Ollama (reference)",
                "options": {
                    # Inside the sandbox the container-only name is what resolves; on the
                    # host it does not, so a non-sandbox run needs the host-side URL or the
                    # student would have to edit project.json to practise.
                    "baseURL": (p["ollama_host"] if sandbox else host_side_ollama(p)).rstrip("/") + "/v1",
                    # OpenCode 1.18.29 aborts a request whose response headers (or next
                    # streamed chunk) take longer than 300 s, "ProviderHeaderTimeoutError".
                    # A 14B model on CPU spends longer than that on the first prompt
                    # (measured on the R620, 2026-09-09). The runner already kills the
                    # harness at regeneration_timeout_s, so that is the only bound needed.
                    "headerTimeout": int(p["regeneration_timeout_s"]) * 1000,
                    "chunkTimeout": int(p["regeneration_timeout_s"]) * 1000,
                },
                "models": {slot_model: model_opts},
            }
        },
        "model": f"ollama/{slot_model}",
        "permission": {"edit": "allow", "bash": "allow", "webfetch": "allow"},
        "share": "disabled",
    }
    with open(os.path.join(workdir, "opencode.json"), "w") as fh:
        json.dump(cfg, fh, indent=2)


# ---------- tests ----------

def roster_variant(p, sid):
    """The variant the professor assigned. The roster decides, not the submission:
    a variant.txt inside a submission is written by the student."""
    v = p.get("variants") or {}
    path = os.path.join(p["_dir"], v.get("roster", "variants.csv"))
    if not os.path.exists(path):
        return None, f"variant roster not found: {path}"
    def members(key):
        """A roster key or a submission directory name, split into student ids.
        Pairs are written `A+B` in the ledger, `A-B` as a directory, `A,B` in a roster."""
        out = []
        for part in re.split(r"[+,\-]", key or ""):
            part = part.strip().upper()
            if part:
                out.append(part)
        return out

    want = members(sid)
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            have = members(row.get("student_id"))
            if want and (want == have or set(want) & set(have)):
                return (row.get("variant") or "").strip(), None
    return None, f"{sid} is not on the variant roster {os.path.basename(path)}"


def resolve_tests(p, sub_dir, override, dry, sid=None):
    """Hidden tests dir, generating per-variant tests if the project uses variants."""
    if override:
        return override, None
    base = rel(p, "hidden_tests")
    v = p.get("variants")
    if not v:
        return base, None
    variant, why = roster_variant(p, sid if sid is not None else os.path.basename(os.path.abspath(sub_dir)))
    if why:
        return None, why
    gen_out = tempfile.mkdtemp(prefix="hidden-")
    code, out, err, _ = sh([p["python"], os.path.join(p["_dir"], v["generator"]), "--variant", variant, "--out", gen_out], dry=dry)
    if code not in (0, None) and not dry:
        return None, f"generator failed: {err[-300:]}"
    return gen_out, None


def run_tests(p, workdir, tests_dir, sandbox, dry):
    """Run the hidden suite, with the project's declared equivalence policies binding.

    --project is passed through in both paths so a category whose policy and check.py
    disagree is refused here rather than graded on the wrong rule (F-34).
    """
    project_file = p.get("_path")
    if sandbox:
        cmd = docker_base(p, workdir, network=False, tests_dir=tests_dir,
                          project_file=project_file) + [
            "runtests",
            "python3", "/tools/run_tests.py", "--solution", "/work", "--tests", "/tests",
            "--entry", p["entry"], "--timeout", str(p["test_timeout_s"]),
            "--run-as", "runner", "--json"]
        if project_file:
            cmd += ["--project", "/project.json"]
    else:
        cmd = [p["python"], os.path.join(HERE, "run_tests.py"), "--solution", workdir, "--tests", tests_dir,
               "--entry", p["entry"], "--timeout", str(p["test_timeout_s"]), "--json"]
        if project_file:
            cmd += ["--project", project_file]
    code, out, err, wall = sh(cmd, timeout=3600, dry=dry)
    if dry:
        return {"dry_run": True}
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return {"solution_started": False, "categories": {}, "error": (err or out)[-500:]}


# ---------- regeneration ----------

def prepare_workdir(p, sub_dir, workdir):
    """Build the directory the harness runs in.

    Only the part's specification and the data files it names by filename are copied.
    Anything executable in the target language is left behind, so a student cannot ship
    a finished solution and be graded on it regardless of what the harness does, and a
    project directory handed here by mistake cannot leak the hidden tests or the seeds
    into the container.
    """
    sub_dir = os.path.abspath(sub_dir)
    workdir = os.path.abspath(workdir)
    if not os.path.isdir(sub_dir):
        raise SubmissionError(f"submission path is not a directory: {sub_dir}")
    if os.path.exists(os.path.join(sub_dir, "project.json")):
        raise SubmissionError(
            f"{sub_dir} contains project.json, so it is a project directory, not a submission. "
            "Handing it to the harness would copy the hidden tests and the seeds into the container.")
    if workdir == sub_dir or workdir.startswith(sub_dir + os.sep):
        raise SubmissionError(
            f"the output directory {workdir} is inside the submission {sub_dir}; "
            "this copies the run into itself. Use --out outside the submission tree.")

    spec_name = p["spec"]
    spec_path = os.path.join(sub_dir, spec_name)
    if not os.path.exists(spec_path):
        raise SubmissionError(f"{sub_dir} has no {spec_name}")

    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)
    shutil.copyfile(spec_path, os.path.join(workdir, spec_name))

    spec_text = open(spec_path, encoding="utf-8", errors="replace").read()
    code_ext = os.path.splitext(p["entry"])[1].lower()
    carried = []
    for name in sorted(os.listdir(sub_dir)):
        src = os.path.join(sub_dir, name)
        if not os.path.isfile(src) or name == spec_name:
            continue
        if name in ("PROCESS.md", "WRITTEN.md") or name.startswith("."):
            continue
        if name.lower().endswith(code_ext):
            continue                       # executable in the target language
        if re.match(r"^SPEC[-.].*\.md$", name, re.I):
            continue                       # another part's specification
        if name not in spec_text:
            continue                       # not named by the specification
        shutil.copyfile(src, os.path.join(workdir, name))
        carried.append(name)
    return carried


def classify_failure(code, out, err):
    """Distinguish a broken environment from a specification that did not work."""
    if code == 0:
        return None
    blob = ((err or "") + (out or "")).lower()
    for marker in ENVIRONMENT_MARKERS:
        if marker in blob:
            return f"environment: {marker}"
    if code == 127:
        return "environment: harness not installed (exit 127)"
    return None


def regenerate(p, sub_dir, workdir, slot, seed, run_tag, sandbox, dry):
    if not dry:
        prepare_workdir(p, sub_dir, workdir)
    elif not os.path.exists(workdir):
        os.makedirs(workdir, exist_ok=True)
    slot_model = f"{p['slot_prefix']}{slot}"
    write_opencode_config(p, workdir, slot_model,
                          temperature=p["temperatures"][slot - 1], seed=seed, sandbox=sandbox)
    prompt = wrapper_prompt(p)
    env = {"RUN_TAG": run_tag, "SLOT_MODEL": slot_model, "PROMPT": prompt}
    cname = f"harness-{p.get('name','project')}-{run_tag}-{os.path.basename(os.path.dirname(workdir))}"
    cname = re.sub(r"[^A-Za-z0-9_.-]", "-", cname)[:100]
    if sandbox:
        cmd = docker_base(p, workdir, extra_env=env, network=True, name=cname) + ["regenerate"]
        run_env = None
    else:
        # OpenCode 1.18.29 takes its project directory from the PWD variable, not from the
        # process's real working directory. Launched from a script whose PWD is the repo, it
        # opened a second instance on the repo and died in 4 s with "Unexpected server error"
        # (R620, 2026-09-09). Say the directory both ways.
        cmd = ["opencode", "run", "--dir", workdir, "-m", f"ollama/{slot_model}", "--format", "json", prompt]
        run_env = dict(os.environ, PWD=workdir)
    code, out, err, wall = sh(cmd, timeout=p["regeneration_timeout_s"], cwd=None if sandbox else workdir,
                              dry=dry, env=run_env)
    timed_out = code is None
    if timed_out and sandbox and not dry:
        # Killing the docker client leaves the container and the harness running, holding
        # the model server for the rest of the batch. Kill the container by name.
        subprocess.run(["docker", "kill", cname], capture_output=True)
    rec = {"harness_exit": code, "timed_out": timed_out, "wall_s": round(wall, 1),
           "harness_stdout_tail": out[-3000:], "harness_stderr_tail": err[-1500:],
           "entry_present": os.path.exists(os.path.join(workdir, p["entry"]))}
    env_err = classify_failure(code, out, err) if not timed_out else None
    if env_err:
        rec["environment_error"] = env_err
    # A harness that exits cleanly, calls no tool and writes nothing did not fail to solve
    # the task: it never started. Scoring that as the student's zero would blame a cohort
    # for a broken setup. Measured failure mode: a model that emits its tool call as plain
    # text (docs/review/evidence/harness-tool-calling.md).
    if not rec["entry_present"] and not env_err and not timed_out and not dry:
        if '"type":"tool"' not in (out or ""):
            rec["harness_error"] = (
                f"the harness exited {code} having made no tool call and produced no file. "
                "Either the model is not emitting structured tool calls or the harness itself "
                "failed; neither is the student's doing. Run the calibration checklist before grading.")
    return rec


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


def record_name(run_tag, slot, dry=False):
    """Grading writes k<N>.json. Any other run tag writes its own record, so an appeal
    is not mistaken for a completed grading slot and cannot overwrite one.

    A --dry-run record is worth keeping (it holds the command lines) but is not a run, so
    it is named <tag>-k<N>.dry.json; grade.py and milestone.py ignore *.dry.json.
    """
    base = f"k{slot}" if run_tag == "grading" else f"{run_tag}-k{slot}"
    return base + (".dry.json" if dry else ".json")


def work_dir_name(run_tag, slot, dry=False):
    """The directory the harness runs in, beside its record."""
    return f"{run_tag}-k{slot}" + ("-dry-work" if dry else "-work")


def process_type_b(p, sid, sub_dir, out, seeds, run_tag, slots, tests_override, sandbox, dry):
    """Returns "ok", "skipped", or "environment" for the batch's failure counter."""
    tests_dir, why = resolve_tests(p, sub_dir, tests_override, dry, sid=sid)
    if why:
        print(f"  {sid}: SKIP ({why})")
        return "skipped"
    outcome = "ok"
    for slot in slots:
        rp = record_path(out, sid, record_name(run_tag, slot, dry))
        if already_done(rp):
            print(f"  {sid} k{slot}: done, skipping")
            continue
        workdir = os.path.join(out, sid, work_dir_name(run_tag, slot, dry))
        print(f"  {sid} k{slot}: temperature={p['temperatures'][slot-1]} tag={run_tag}-k{slot}")
        # The seed value is deliberately not stored: a run record travels with an appeal
        # packet, and the seeds are secret until grades are released.
        rec = {"submission": sid, "type": "B", "slot": slot, "temperature": p["temperatures"][slot - 1],
               "seed_recorded": False, "run_tag": f"{run_tag}-k{slot}", "started": now(),
               "dry_run": bool(dry),
               "tests_dir": os.path.abspath(tests_dir) if tests_dir else None}
        try:
            rec["regeneration"] = regenerate(p, sub_dir, workdir, slot, seeds[slot - 1],
                                             f"{run_tag}-k{slot}", sandbox, dry)
        except SubmissionError as e:
            print(f"  {sid}: SKIP ({e})")
            return "skipped"
        env_err = rec["regeneration"].get("environment_error") or rec["regeneration"].get("harness_error")
        if env_err:
            # Nothing ran. Leave the slot incomplete so a retry pass picks it up, rather
            # than scoring the student zero for a machine that was broken.
            rec["ended"] = now()
            rec["complete"] = False
            rec["incomplete_reason"] = env_err
            with open(rp, "w") as fh:
                json.dump(rec, fh, indent=2)
            print(f"  {sid} k{slot}: INCOMPLETE ({env_err})")
            outcome = "environment"
            continue
        rec["tests"] = run_tests(p, workdir, tests_dir, sandbox, dry) if rec["regeneration"]["entry_present"] or dry \
            else {"solution_started": False, "categories": {}, "error": "no entry point produced"}
        rec["ended"] = now()
        rec["complete"] = not dry
        with open(rp, "w") as fh:
            json.dump(rec, fh, indent=2)
    return outcome


def process_type_a(p, sid, sub_dir, out, tests_override, sandbox, dry, run_tag="grading"):
    base = "a" if run_tag == "grading" else f"{run_tag}-a"
    rp = record_path(out, sid, base + (".dry.json" if dry else ".json"))
    if already_done(rp):
        print(f"  {sid}: done, skipping")
        return "ok"
    tests_dir, why = resolve_tests(p, sub_dir, tests_override, dry, sid=sid)
    if why:
        print(f"  {sid}: SKIP ({why})")
        return "skipped"
    workdir = os.path.join(out, sid, base + ("-dry-work" if dry else "-work"))
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    shutil.copytree(sub_dir, workdir, ignore=shutil.ignore_patterns(".git"))
    print(f"  {sid}: hidden tests")
    rec = {"submission": sid, "type": "A", "run_tag": run_tag, "started": now(),
           "dry_run": bool(dry)}
    rec["tests"] = run_tests(p, workdir, tests_dir, sandbox, dry)
    rec["ended"] = now()
    rec["complete"] = not dry
    with open(rp, "w") as fh:
        json.dump(rec, fh, indent=2)
    return "ok"


def run_batch(p, subs, out, seeds, run_tag, slots, tests_override, sandbox, dry, ptype):
    """Run every submission, stopping if the machine looks broken.

    An isolated environment failure leaves that slot incomplete and the batch carries on.
    CONSECUTIVE_FAILURE_LIMIT of them in a row raises BatchAborted, because continuing
    would mark a whole cohort incomplete against a model server that is down.
    """
    consecutive = 0
    skipped, ran = [], 0
    for sid, d in subs:
        if ptype == "B":
            outcome = process_type_b(p, sid, d, out, seeds, run_tag, slots, tests_override, sandbox, dry)
        else:
            outcome = process_type_a(p, sid, d, out, tests_override, sandbox, dry, run_tag=run_tag)
        if outcome == "skipped":
            skipped.append(sid)
        if outcome == "environment":
            consecutive += 1
            if consecutive >= CONSECUTIVE_FAILURE_LIMIT:
                raise BatchAborted(
                    f"{consecutive} consecutive environment failures ending at {sid}. "
                    "Nothing was scored against them; fix the environment and re-run the "
                    "same command to retry the incomplete slots.")
        elif outcome == "ok":
            consecutive = 0
            ran += 1
    if skipped:
        print(f"\nSKIPPED {len(skipped)} of {len(subs)} submissions: {', '.join(skipped)}",
              file=sys.stderr)
    if subs and ran == 0:
        raise NothingGraded(f"none of the {len(subs)} submissions produced a record")
    return {"ran": ran, "skipped": skipped}


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
    ap.add_argument("--verify-slots", action="store_true",
                    help="check the model server reports the scheduled temperature and seed per slot")
    ap.add_argument("--skip-slot-check", action="store_true",
                    help="grade without verifying the slot models (not for a graded batch)")
    ap.add_argument("--dry-run", action="store_true", help="print commands, write nothing complete")
    ap.add_argument("--no-sandbox", action="store_true", help="run on the host (practice only; never for grading)")
    ap.add_argument("--practice", action="store_true",
                    help="student practice run: implies --no-sandbox and --skip-slot-check, tags the run "
                         "'practice', runs the public suite, writes seeds.practice.json if the secret seeds "
                         "are absent, and creates the slot models if the model server has none")
    a = ap.parse_args()

    p = load_project(a.project)
    if a.create_slots:
        return create_slots(p, a.dry_run)
    if a.verify_slots:
        problems = verify_slots(p, load_seeds(p))
        for x in problems:
            print("  " + x)
        print("slot check: " + ("FAILED" if problems else "ok"))
        return 1 if problems else 0
    ptype = a.type or p["type"]
    # Before practice_setup, which writes seeds and creates slot models: a run that
    # cannot happen must say so before it leaves anything behind.
    if not a.dry_run:
        require_run_binaries(ptype, not (a.no_sandbox or a.practice))
    if a.practice:
        practice_setup(p, a, ptype)
    sandbox = not a.no_sandbox
    if a.practice:
        print(f"practice run: tag={a.run_tag}, tests={a.tests}, no sandbox. Not a graded run.")
    elif not sandbox:
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
    if a.slot is not None:
        if not 1 <= a.slot <= p["k"]:
            sys.exit(f"--slot must be between 1 and {p['k']} for this project; got {a.slot}")
        slots = [a.slot]
    else:
        slots = list(range(1, p["k"] + 1))
    if ptype == "B" and not a.dry_run and not a.skip_slot_check:
        problems = verify_slots(p, seeds)
        if problems:
            for x in problems:
                print("  " + x, file=sys.stderr)
            sys.exit("slot check failed: the temperature schedule is not reaching the model. "
                     "Re-run --create-slots, or pass --skip-slot-check to grade anyway.")
    print(f"{len(subs)} submissions, type {ptype}, sandbox={'on' if sandbox else 'OFF'}, out={a.out}")
    try:
        run_batch(p, subs, a.out, seeds, a.run_tag, slots, a.tests, sandbox, a.dry_run, ptype)
    except BatchAborted as e:
        sys.exit(f"BATCH ABORTED: {e}")
    except NothingGraded as e:
        sys.exit(f"NOTHING GRADED: {e}. Check status.csv keys and, for a variants project, "
                 f"the variant roster.")
    print("done")


if __name__ == "__main__":
    main()
