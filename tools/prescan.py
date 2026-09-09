#!/usr/bin/env python3
"""Pre-scan student specifications for lines a TA must read closely.

This is a focusing tool for the safety read, not a safety control. The
sandbox is the safety control. Standard library only.

Usage:
    prescan.py SUBMISSIONS_DIR [--project project.json] [--allow HOST ...] [--cap 1500]
    prescan.py --course COURSE_DIR [--cap 1500] [--page-cap 600]

Two modes. The first scans **one program's** submissions directory, the shape the runner
grades. The second scans the **course-level** `submissions/` tree beside `parts.json`, the
shape students actually submit (one directory per student, one sub-directory per program,
one `WRITTEN.md` and one `PROCESS.md` for the whole project). The course mode is the one to
run on Day 0, before `fan_out.py` has copied anything: it checks the layout, every
`SPEC.md` against the same patterns and word cap, and the two course-level pages against
the 600-word cap once each rather than once per program. It prints one row per student.

`--course DIR` works on **either** shape, so the runbook has one command for both. If
`DIR/parts.json` exists the course scan above runs; otherwise `DIR` is a single-part project
and `DIR/submissions/` is scanned with `DIR/project.json`, printing exactly the rows the
per-program mode prints. A single-part project has no course-level tree to fan out, so the
submissions directory beside `project.json` *is* the layout the student submitted.

A **Type A** project has no specification: the submission is code, and `variant.txt` is
ignored. Its rows print `words=n/a` and the 1,500-word cap is not applied. `PROCESS.md` and
`WRITTEN.md` are still counted against the 600-word page cap.

Pass --project and the allowed hosts come from the project itself, so the mandatory
ledger line in every conforming specification is not flagged as an offsite URL.
It also checks that the student id inside the submission matches the submission directory.
For a pair directory `A-B` **either** member is acceptable, since the specification's ledger
line names whoever signs. A submission that names no id at all is not reported: only one
that claims some *other* id and none of its own (`spec-id-mismatch:...`).

Prints one line per submission: FLAG|INCOMPLETE|OK  <id>  <reasons>
Exit 0 always (the TA decides).
"""
import argparse
import json
import os
import re
import sys
import urllib.parse

PATTERNS = [
    ("override", re.compile(r"ignore (all |any )?(previous|prior|above) (instructions|rules)", re.I)),
    ("override", re.compile(r"(you are now|new instructions|system prompt|disregard)", re.I)),
    ("grader", re.compile(r"\b(TA|grader|instructor|professor)\b.*\b(give|award|assign|mark)\b.*\b(full|max|100|points|grade)", re.I)),
    ("shell", re.compile(r"\b(rm -rf|curl\b|wget\b|nc\s+-[a-z]|ncat\b|ssh\s+\S+@|scp\s+\S+@|sudo\b|chmod \+x|base64 -d|eval\(|exec\()", re.I)),
    ("shell", re.compile(r"(\bsh\b|bash)\s*-c|\|\s*(sh|bash)\b", re.I)),
    ("network", re.compile(r"\b(socket|urllib|requests\.(get|post)|http\.client|subprocess)\b")),
    ("secrets", re.compile(r"(~/\.ssh|/etc/passwd|\.env\b|api[_-]?key|token=|password)", re.I)),
    ("exfil", re.compile(r"(webhook|ngrok|pastebin|discord\.com/api|telegram)", re.I)),
    ("escape", re.compile(r"(\bdocker\s+(run|exec|cp|sock)|/var/run/|\.\./\.\./|/proc/|/sys/)", re.I)),
    # A specification that reaches for the graded answers rather than computing them.
    ("answers", re.compile(r"(/tests\b|\btests/hidden\b|expected[ _-]?output|\.out\.json|answer key)", re.I)),
    ("dnstool", re.compile(r"\b(dig|nslookup|host)\s+[a-z0-9.-]+\.[a-z]{2,}", re.I)),
    ("encoded", re.compile(r"[A-Za-z0-9+/]{80,}={0,2}")),
]
URL = re.compile(r"https?://([A-Za-z0-9.-]+)", re.I)
TEXT_EXT = (".md", ".txt", ".json", ".yaml", ".yml", ".py", ".toml", ".cfg", ".ini")
# Extensions that hold a solution rather than a specification. They are still scanned for
# malicious content, but they do not count toward the specification's word cap: a Type A
# submission is code by definition and would otherwise always be over cap.
CODE_EXT = (".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rs")


def allowed(host, allow):
    return any(host == h or host.endswith("." + h) for h in allow)


LEDGER_CURL = re.compile(r"\bcurl\b[^|;&]*\/ledger\b")


def scan_text(text, allow):
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        hosts = URL.findall(line)
        # The ledger sign instruction is a curl to an allowed host; it is expected in every spec.
        ledger_line = bool(LEDGER_CURL.search(line)) and hosts and all(allowed(h, allow) for h in hosts) \
            and "|" not in line and "$(" not in line
        for label, rx in PATTERNS:
            if rx.search(line):
                if ledger_line and label == "shell":
                    continue
                hits.append(f"L{i}:{label}")
        for host in hosts:
            if not allowed(host, allow):
                hits.append(f"L{i}:url:{host}")
    return hits


PAGE_FILES = ("PROCESS.md", "WRITTEN.md")
# A student id as the course writes them: letters then digits, e.g. ABC123456.
STUDENT_ID = re.compile(r"\b[A-Z]{2,5}[0-9]{4,9}\b")
# Lines where an id is being claimed rather than merely mentioned.
ID_LINE = re.compile(r"student[ _-]?id|\bledger\b|\bsign\b", re.I)


def members(key):
    """A submission directory name split into student ids. A pair is `A-B` as a directory,
    `A+B` in the ledger and `A,B` in a roster; any member identifies the submission."""
    return [x.strip().upper() for x in re.split(r"[+,\-]", key or "") if x.strip()]


def id_check(dir_name, texts):
    """The runbook's 'the student ID inside the specification matches the submission
    directory' check. A pair's specification may name **either** member, so any member
    is acceptable. Reported only when the submission claims some *other* id and none of
    its own: a specification that names no id at all is not evidence of anything."""
    own = members(dir_name)
    if not own:
        return []
    blob = "\n".join(texts)
    upper = blob.upper()
    if any(m in upper for m in own):
        return []
    claimed = []
    for line in blob.splitlines():
        if ID_LINE.search(line):
            claimed += [i for i in STUDENT_ID.findall(line.upper()) if i not in claimed]
    if claimed:
        return [f"spec-id-mismatch:{','.join(claimed)}"]
    return []


def scan_tree(path, allow):
    """Walk one directory: (hits, specification words, {page file: words}, texts).

    The specification word count excludes the two course-level pages and any file in the
    target language, which are capped and counted elsewhere.
    """
    hits, words, pages, texts = [], 0, {}, []
    for root, _, files in os.walk(path):
        for f in files:
            if not f.lower().endswith(TEXT_EXT):
                hits.append(f"binary-or-unknown:{f}")
                continue
            p = os.path.join(root, f)
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
            except OSError as e:
                hits.append(f"unreadable:{f}:{e}")
                continue
            texts.append(text)
            rel = os.path.relpath(p, path)
            if rel in PAGE_FILES:
                pages[rel] = len(text.split())
            elif not rel.lower().endswith(CODE_EXT):
                words += len(text.split())
            hits += [f"{rel}:{h}" for h in scan_text(text, allow)]
    return hits, words, pages, texts


def scan_submission(path, allow, cap, page_cap=600):
    hits, words, pages, texts = scan_tree(path, allow)
    for name in PAGE_FILES:
        if name not in pages:
            hits.append(f"missing:{name}")
        elif pages[name] > page_cap:
            hits.append(f"{name}:over-page-cap:{pages[name]}")
    hits += id_check(os.path.basename(os.path.normpath(path)), texts)
    return hits, words


def scan_course_student(student_dir, programs, allow, cap, page_cap, types=None):
    """One student's whole submission in the layout the handout asks for.

    Everything the per-program mode checks, but read once over the course-level tree: the
    layout itself (fan_out's rules), every program's SPEC.md against the same patterns and
    the same 1,500-word cap, and the **single** WRITTEN.md and PROCESS.md against the
    600-word cap — once each, not once per program.
    """
    import fan_out
    problems, _words, _missing = fan_out.inspect(student_dir, programs)
    hits, texts, words = list(problems), [], {}
    for name, dirname, _spec, _data in programs:
        d = os.path.join(student_dir, dirname)
        if not os.path.isdir(d):
            continue
        h, w, _p, t = scan_tree(d, allow)
        hits += [f"{dirname}/{x}" for x in h]
        texts += t
        # A Type A program has no specification to cap: the submission is code, and the
        # only text file a Type A submission carries is the ignored `variant.txt`.
        if (types or {}).get(name, "B") == "A":
            words[name] = None
            continue
        words[name] = w
        if w > cap:
            hits.append(f"{dirname}:spec-over-cap:{w}")
    for page in PAGE_FILES:
        p = os.path.join(student_dir, page)
        if not os.path.isfile(p):
            continue                      # fan_out.inspect already reported it as missing
        text = open(p, encoding="utf-8", errors="replace").read()
        texts.append(text)
        n = len(text.split())
        hits += [f"{page}:{h}" for h in scan_text(text, allow)]
        if n > page_cap:
            hits.append(f"{page}:over-page-cap:{n}")
    hits += id_check(os.path.basename(os.path.normpath(student_dir)), texts)
    return hits, words


def course_hosts(course_dir):
    """Allowed hosts taken from every part's project.json, so --course needs no --project."""
    import glob
    allow = []
    for pj in sorted(glob.glob(os.path.join(course_dir, "part-*", "project.json"))):
        try:
            proj = json.load(open(pj))
        except (OSError, ValueError):
            continue
        allow += hosts_from_project(proj)
    return allow


def course_types(course_dir):
    """{program name: "A" or "B"} from each part's project.json, for the word-cap rule."""
    import glob
    types = {}
    for pj in sorted(glob.glob(os.path.join(course_dir, "part-*", "project.json"))):
        try:
            proj = json.load(open(pj))
        except (OSError, ValueError):
            continue
        name = os.path.basename(os.path.dirname(pj))[len("part-"):]
        types[name] = str(proj.get("type", "B")).strip().upper()
    return types


def hosts_from_project(proj):
    allow = []
    if proj.get("resource_host"):
        allow.append(proj["resource_host"])
    if proj.get("ollama_host"):
        h = urllib.parse.urlsplit(proj["ollama_host"]).hostname
        if h:
            allow.append(h)
    for e in proj.get("extra_allow_endpoints", []):
        allow.append(e.split(":")[0])
    return allow


def classify(hits):
    """(status, suspicious, admin). FLAG needs a human to read for misconduct; INCOMPLETE is
    a file, layout or cap problem the student can fix."""
    admin = [h for h in hits if h.startswith(("missing:", "missing-program:", "stray-file:",
                                              "unknown-directory:"))
             or "over-page-cap" in h or "over-cap" in h]
    suspicious = [h for h in hits if h not in admin]
    return ("FLAG" if suspicious else "INCOMPLETE" if admin else "OK"), suspicious, admin


def scan_program_dir(submissions, allow, cap, page_cap, type_a=False):
    """The per-program mode: one row per submission directory. Returns 0."""
    for sid in sorted(os.listdir(submissions)):
        p = os.path.join(submissions, sid)
        if not os.path.isdir(p):
            continue
        hits, words = scan_submission(p, allow, cap, page_cap)
        # Two different outcomes, deliberately not the same word: FLAG means a human must
        # read it for possible misconduct; INCOMPLETE means a file or a cap problem the
        # student can fix. The runbook assigns a different status to each.
        admin = [h for h in hits if h.startswith("missing:") or "over-page-cap" in h]
        suspicious = [h for h in hits if h not in admin]
        # Type A has no specification: what a Type A submission contains is code, and its
        # `variant.txt` is written by the student and ignored. Counting either against the
        # specification's 1,500-word cap reports a cap on a file that is not one.
        shown = "n/a" if type_a else str(words)
        if not type_a and words > cap:
            admin.append(f"spec-over-cap:{words}")
        if suspicious:
            status = "FLAG"
        elif admin:
            status = "INCOMPLETE"
        else:
            status = "OK"
        print(f"{status}\t{sid}\twords={shown}\t" + " ".join(suspicious + admin))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("submissions", nargs="?",
                    help="one program's submissions directory (the per-program mode)")
    ap.add_argument("--course", help="a project directory: with parts.json, scan the "
                                     "course-level submissions/ tree in the layout students "
                                     "submit, one row per student; without one, scan the "
                                     "single-part project's own submissions/ directory")
    ap.add_argument("--project", help="project.json; the resource and model hosts are taken from it")
    ap.add_argument("--allow", nargs="*", default=[], help="extra hosts allowed in URLs")
    ap.add_argument("--cap", type=int, default=1500, help="word cap on the specification + supporting files")
    ap.add_argument("--page-cap", type=int, default=600,
                    help="word cap on PROCESS.md and WRITTEN.md, checked per file")
    a = ap.parse_args()
    if not a.submissions and not a.course:
        ap.error("give either a submissions directory (one program's) or --course DIR "
                 "(the project directory: a course holding parts.json, or a single-part "
                 "project holding project.json)")

    # --course accepts either shape, so the runbook has one command for both. A directory
    # with no parts.json is a single-part project: its own submissions/ and project.json are
    # what the per-program mode reads, and the rows are identical.
    course = os.path.abspath(a.course) if a.course else None
    multi_part = bool(course) and os.path.exists(os.path.join(course, "parts.json"))
    project_path = a.project
    if course and not multi_part and not project_path:
        pj = os.path.join(course, "project.json")
        if not os.path.exists(pj):
            sys.exit(f"{course}: neither parts.json nor project.json.\n"
                     f"  --course must be a project directory: a course directory holding "
                     f"parts.json, or a single-part project holding project.json.")
        project_path = pj

    allow, type_a = list(a.allow), False
    if project_path:
        try:
            proj = json.load(open(project_path))
        except OSError as e:
            sys.exit(f"--project: {e}")
        allow += hosts_from_project(proj)
        type_a = str(proj.get("type", "B")).strip().upper() == "A"
    elif multi_part:
        # Every part of a course points at the same resource and model hosts; taking them
        # from the parts means the course-level scan needs no --project of its own.
        allow += course_hosts(course)
    if not allow:
        print("note: no allowed hosts given, so every URL will be flagged. "
              "Pass --project project.json.", file=sys.stderr)
    a.allow = list(dict.fromkeys(allow))

    if multi_part:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import fan_out
        programs = fan_out.load_parts(course)
        types = course_types(course)
        # The tree lives beside parts.json unless the TA points somewhere else, which is
        # what happens when submissions are unpacked from the dropbox into scratch space.
        root = os.path.abspath(a.submissions) if a.submissions \
            else os.path.join(course, "submissions")
        for sid in fan_out.students(root):
            hits, words = scan_course_student(os.path.join(root, sid), programs,
                                              a.allow, a.cap, a.page_cap, types)
            status, suspicious, admin = classify(hits)
            counts = ",".join(
                (f"{n}=n/a" if words[n] is None else f"{n}={words[n]}") if n in words
                else f"{n}=-" for n, _d, _s, _f in programs)
            print(f"{status}\t{sid}\tprograms={len(words)}/{len(programs)}\twords={counts}\t"
                  + " ".join(suspicious + admin))
        return 0

    submissions = a.submissions or os.path.join(course, "submissions")
    if not os.path.isdir(submissions):
        sys.exit(f"submissions directory not found: {submissions}")
    return scan_program_dir(submissions, a.allow, a.cap, a.page_cap, type_a)


if __name__ == "__main__":
    sys.exit(main())
