#!/usr/bin/env python3
"""Deterministic review checks for the framework repo (review plan §Deterministic checks).

Writes a Markdown report. Standard library only. Network is used only for URL resolution
(skip with --no-network).

    python3 scripts/review_checks.py [--out docs/review/checks-YYYY-MM-DD.md] [--no-network]
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_TESTS = os.path.join(ROOT, "tools", "run_tests.py")
PRESCAN = os.path.join(ROOT, "tools", "prescan.py")
PORTFOLIO = "/Users/xaviermendez/develop/portfolioWebsite/xavis_projects"
OUT = []


def h(title):
    OUT.append(f"\n## {title}\n")


def row(status, what, detail=""):
    OUT.append(f"| {status} | {what} | {detail} |")


def table_header():
    OUT.append("| Result | Check | Detail |")
    OUT.append("|---|---|---|")


def sh(cmd, cwd=None, timeout=600):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


# ---------- examples ----------

def find_projects():
    """(label, project_json_path) for every project.json under examples/ that has tests."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "examples", "*", "project.json")) +
                    glob.glob(os.path.join(ROOT, "examples", "*", "part-*", "project.json"))):
        out.append((os.path.relpath(os.path.dirname(p), ROOT), p))
    return out


def run_suite(project_dir, p, solution_rel, tests_rel):
    sol = os.path.join(project_dir, solution_rel)
    tests = os.path.join(project_dir, tests_rel)
    if not os.path.isdir(sol) or not os.path.isdir(tests):
        return None
    code, out, err = sh([sys.executable, RUN_TESTS, "--solution", sol, "--tests", tests,
                         "--entry", p.get("entry", "solve.py"), "--timeout", str(p.get("test_timeout_s", 10)), "--json"])
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return {"error": (err or out)[-300:], "categories": {}}


def check_examples():
    h("Examples: reference passes, canonical fails twist categories, weights, policies")
    table_header()
    for label, path in find_projects():
        pdir = os.path.dirname(path)
        p = json.load(open(path))
        cats = p.get("categories", {})
        hidden_rel = p.get("hidden_tests", "tests/hidden")
        variants = p.get("variants")
        # locate reference + canonical solutions
        ref = next((d for d in ["reference/solution", "reference"] if os.path.exists(os.path.join(pdir, d, p.get("entry", "solve.py")))), None)
        can = "canonical" if os.path.exists(os.path.join(pdir, "canonical", p.get("entry", "solve.py"))) else None
        hidden_dir = os.path.join(pdir, hidden_rel)
        gen_note = ""
        if variants and not os.path.isdir(hidden_dir):
            gen = os.path.join(pdir, variants["generator"])
            hidden_dir = os.path.join("/tmp", "review-hidden-" + label.replace("/", "-"))
            code, out, err = sh([sys.executable, gen, "--variant", "demo", "--out", hidden_dir])
            gen_note = f" (generated for variant demo, exit {code})"
            hidden_rel = hidden_dir
        if not os.path.isdir(hidden_dir):
            row("SKIP", f"{label}: hidden tests", "no hidden tests directory (stub part?)")
        else:
            if ref:
                r = run_suite(pdir, p, ref, hidden_rel if os.path.isabs(hidden_rel) else hidden_rel)
                if r is None or "error" in r:
                    row("FAIL", f"{label}: reference run", (r or {}).get("error", "no run"))
                else:
                    summ = ", ".join(f"{c}={v['pass']}/{v['total']}" for c, v in r["categories"].items())
                    allpass = all(v["pass"] == v["total"] for v in r["categories"].values()) and r["categories"]
                    row("PASS" if allpass else "FAIL", f"{label}: reference passes every hidden test{gen_note}", summ)
                    missing = [c for c in cats if c not in r["categories"]]
                    if missing:
                        row("FAIL", f"{label}: categories in project.json with no test directory", ", ".join(missing))
                    extra = [c for c in r["categories"] if c not in cats]
                    if extra:
                        row("FAIL", f"{label}: test directories not declared in project.json", ", ".join(extra))
            else:
                row("FAIL", f"{label}: reference solution", "not found")
            if can:
                r = run_suite(pdir, p, can, hidden_rel)
                if r is None or "error" in r:
                    row("FAIL", f"{label}: canonical run", (r or {}).get("error", "no run"))
                else:
                    twist = [c for c, m in cats.items() if m.get("twist")]
                    bad = []
                    for c in twist:
                        v = r["categories"].get(c)
                        if v and v["total"] and v["pass"] / v["total"] >= 0.5:
                            bad.append(f"{c}={v['pass']}/{v['total']}")
                    summ = ", ".join(f"{c}={v['pass']}/{v['total']}" for c, v in r["categories"].items() if c in twist)
                    row("PASS" if not bad and twist else "FAIL", f"{label}: canonical scores <50% on every twist category", summ or "no twist categories")
            else:
                row("FAIL", f"{label}: canonical solution", "not found")
        # weights rule
        nongrad = {c: m for c, m in cats.items() if not m.get("grad_only")}
        tw = sum(float(m.get("weight", 1)) for m in nongrad.values() if m.get("twist"))
        tot = sum(float(m.get("weight", 1)) for m in nongrad.values())
        ok = cats and abs(tw * 2 - tot) < 1e-9
        row("PASS" if ok else "FAIL", f"{label}: twist weights = half of non-grad weights", f"twist={tw}, total={tot}")
        # policies
        for c, m in cats.items():
            pol = m.get("policy", "strict")
            cdir = os.path.join(hidden_dir, c) if os.path.isdir(hidden_dir) else None
            has_check = cdir and os.path.exists(os.path.join(cdir, "check.py"))
            if "policy" not in m:
                row("WARN", f"{label}/{c}: equivalence policy not declared in project.json", "treated as strict" + ("; check.py present" if has_check else ""))
            elif pol != "strict" and not has_check:
                row("FAIL", f"{label}/{c}: policy {pol} but no check.py", "")
        # public tests exist
        pub = os.path.join(pdir, p.get("public_tests", "tests/public"))
        row("PASS" if os.path.isdir(pub) else ("SKIP" if not os.path.isdir(os.path.join(pdir, "tests")) else "FAIL"), f"{label}: public tests present", os.path.relpath(pub, ROOT))
        # sample submissions: word cap + prescan
        subs = os.path.join(pdir, "submissions")
        if os.path.isdir(subs):
            for sid in sorted(os.listdir(subs)):
                sd = os.path.join(subs, sid)
                if not os.path.isdir(sd):
                    continue
                words = 0
                for f in os.listdir(sd):
                    if f.endswith((".md", ".txt")) and f not in ("PROCESS.md", "WRITTEN.md"):
                        words += len(open(os.path.join(sd, f), encoding="utf-8", errors="replace").read().split())
                row("PASS" if words <= 1500 else "FAIL", f"{label}/submissions/{sid}: spec words ≤ 1500", str(words))
                for req in ("PROCESS.md", "WRITTEN.md"):
                    row("PASS" if os.path.exists(os.path.join(sd, req)) else "FAIL", f"{label}/submissions/{sid}: {req} present", "")
            code, out, err = sh([sys.executable, PRESCAN, subs, "--allow", "host.docker.internal", "localhost", "www.bittorrent.org"])
            flagged = [l for l in out.splitlines() if not l.startswith("OK")]
            row("PASS" if not flagged else "WARN", f"{label}: prescan on sample submissions", "; ".join(flagged)[:200] or "all OK")
        # reference spec word cap
        for spec in glob.glob(os.path.join(pdir, "reference", "SPEC.md")):
            w = len(open(spec, encoding="utf-8").read().split())
            row("PASS" if w <= 1500 else "FAIL", f"{label}: reference SPEC.md ≤ 1500 words", str(w))


# ---------- repo hygiene ----------

def check_repo():
    h("Repository hygiene")
    table_header()
    code, out, err = sh(["git", "ls-files"], cwd=ROOT)
    tracked = out.split()
    leaked = [f for f in tracked if "seeds.secret" in f]
    row("PASS" if not leaked else "FAIL", "no seeds.secret.json tracked by git", ", ".join(leaked))
    code, out, err = sh(["git", "status", "--porcelain", "--ignored"], cwd=ROOT)
    ignored_seeds = [l for l in out.splitlines() if l.startswith("!!") and "seeds.secret" in l]
    row("PASS" if ignored_seeds else "WARN", "seeds.secret.json files are gitignored", f"{len(ignored_seeds)} ignored")
    # python syntax
    bad = []
    for f in glob.glob(os.path.join(ROOT, "**", "*.py"), recursive=True):
        code, out, err = sh([sys.executable, "-m", "py_compile", f])
        if code != 0:
            bad.append(os.path.relpath(f, ROOT))
    row("PASS" if not bad else "FAIL", "all .py files compile", ", ".join(bad))
    # tests present?
    tests = glob.glob(os.path.join(ROOT, "tests", "**", "test_*.py"), recursive=True)
    row("PASS" if tests else "FAIL", "tools have a test suite (standards: every feature ships with a test)", f"{len(tests)} test files")
    for f in ["CLAUDE.md", "CONTRIBUTING.md", "docs/DECISIONS.md", "docs/BACKLOG.md", ".github/workflows/ci.yml", ".pre-commit-config.yaml"]:
        row("PASS" if os.path.exists(os.path.join(ROOT, f)) else "WARN", f"standards file present: {f}", "")
    todos = []
    for f in tracked:
        fp = os.path.join(ROOT, f)
        if f.endswith((".py", ".md", ".sh")) and os.path.exists(fp):
            for i, line in enumerate(open(fp, encoding="utf-8", errors="replace"), 1):
                if re.search(r"\bTODO\b", line) and not re.search(r"TODO\(BL-\d+\)", line):
                    todos.append(f"{f}:{i}")
    row("PASS" if not todos else "WARN", "no TODO without a BL-nn id", ", ".join(todos[:10]))


# ---------- links ----------

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def check_internal_links():
    h("Internal links resolve")
    table_header()
    broken = []
    n = 0
    for f in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True):
        if "/node_modules/" in f:
            continue
        text = open(f, encoding="utf-8", errors="replace").read()
        for target in MD_LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            n += 1
            t = target.split("#")[0]
            if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), t))):
                broken.append(f"{os.path.relpath(f, ROOT)} → {target}")
    row("PASS" if not broken else "FAIL", f"{n} relative links checked", "; ".join(broken))


def check_external_urls(network):
    h("External URLs resolve")
    table_header()
    if not network:
        row("SKIP", "network disabled", "")
        return
    files = [os.path.join(ROOT, "templates", "student-primer.md"), os.path.join(ROOT, "framework.md"),
             os.path.join(ROOT, "docs", "research", "prior-project-spring-2026.md")] + \
            glob.glob(os.path.join(ROOT, "examples", "*", "resource", "*.md")) + \
            glob.glob(os.path.join(ROOT, "docs", "research", "harness-survey-*.md"))
    urls = {}
    for f in files:
        for u in re.findall(r"https?://[^\s)\]>\"'`]+", open(f, encoding="utf-8", errors="replace").read()):
            u = u.rstrip(".,;:")
            urls.setdefault(u, set()).add(os.path.relpath(f, ROOT))
    ok = bad = 0
    for u in sorted(urls):
        if "host.docker.internal" in u or "localhost" in u or "example.edu" in u or "<" in u or "{{" in u or "claude.ai/code/artifact" in u:
            continue
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (review-checks)"}, method="GET")
            with urllib.request.urlopen(req, timeout=15) as r:
                status = r.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception as e:
            status = str(e)[:40]
        if status == 200:
            ok += 1
        else:
            bad += 1
            row("FAIL" if status in (404, 410) else "WARN", u, f"{status} · in {', '.join(sorted(urls[u]))}")
    row("PASS" if not bad else "INFO", f"{ok} URLs returned 200", f"{bad} did not")


# ---------- vocabulary ----------

def check_vocabulary():
    h("Glossary: avoided terms used elsewhere (information for J12)")
    table_header()
    ctx = open(os.path.join(ROOT, "CONTEXT.md"), encoding="utf-8").read()
    avoid = {}
    for term, av in re.findall(r"\*\*([^*]+)\*\*:\n.*?\n_Avoid_: ([^\n]+)", ctx, re.S):
        for a in av.split(","):
            a = a.strip()
            a = re.sub(r"\s*\(.*?\)\s*", "", a).strip()
            if a and len(a) > 3:
                avoid[a.lower()] = term
    files = [os.path.join(ROOT, "framework.md"), os.path.join(ROOT, "README.md")] + glob.glob(os.path.join(ROOT, "templates", "*.md"))
    for a, term in sorted(avoid.items()):
        hits = []
        rx = re.compile(r"\b" + re.escape(a) + r"\b", re.I)
        for f in files:
            for i, line in enumerate(open(f, encoding="utf-8").read().splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{os.path.relpath(f, ROOT)}:{i}")
        if hits:
            row("INFO", f"'{a}' (avoid; canonical: {term})", f"{len(hits)} lines, e.g. {', '.join(hits[:4])}")


# ---------- portfolio ----------

def check_portfolio():
    h("Portfolio site (uncommitted changes)")
    table_header()
    if not os.path.isdir(os.path.join(PORTFOLIO, "node_modules")):
        row("SKIP", "node_modules missing", "run npm install")
        return
    code, out, err = sh(["npx", "tsc", "--noEmit"], cwd=PORTFOLIO, timeout=600)
    row("PASS" if code == 0 else "FAIL", "tsc --noEmit", (out + err).strip().splitlines()[-1][:200] if (out + err).strip() else "clean")
    code, out, err = sh(["npm", "run", "lint", "--silent"], cwd=PORTFOLIO, timeout=600)
    errs = [l for l in (out + err).splitlines() if " Error:" in l or "error " in l.lower() and "0 errors" not in l]
    row("PASS" if code == 0 else "FAIL", "npm run lint", f"exit {code}; {len(errs)} error lines")
    code, out, err = sh(["git", "status", "--short"], cwd=PORTFOLIO)
    row("INFO", "pending changes", out.strip().replace("\n", "; ")[:300])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "review", "checks-2026-09-08.md"))
    ap.add_argument("--no-network", action="store_true")
    a = ap.parse_args()
    OUT.append("# Deterministic review checks\n")
    OUT.append("Generated by `scripts/review_checks.py`. PASS/FAIL are checks; WARN/INFO are inputs for the judges.")
    check_examples()
    check_repo()
    check_internal_links()
    check_external_urls(not a.no_network)
    check_vocabulary()
    check_portfolio()
    text = "\n".join(OUT) + "\n"
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write(text)
    fails = sum(1 for l in OUT if l.startswith("| FAIL"))
    warns = sum(1 for l in OUT if l.startswith("| WARN"))
    print(f"wrote {a.out}: {fails} FAIL, {warns} WARN")
    print("\n".join(l for l in OUT if l.startswith("| FAIL") or l.startswith("| WARN")))


if __name__ == "__main__":
    main()
