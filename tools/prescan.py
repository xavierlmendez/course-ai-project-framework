#!/usr/bin/env python3
"""Pre-scan student specifications for lines a TA must read closely.

This is a focusing tool for the safety read, not a safety control. The
sandbox is the safety control. Standard library only.

Usage:
    prescan.py SUBMISSIONS_DIR [--project project.json] [--allow HOST ...] [--cap 1500]

Pass --project and the allowed hosts come from the project itself, so the mandatory
ledger line in every conforming specification is not flagged as an offsite URL.
Prints one line per submission: FLAG|OK|OVERCAP  <id>  <reasons>
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


def scan_submission(path, allow, cap, page_cap=600):
    hits, words, pages = [], 0, {}
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
            rel = os.path.relpath(p, path)
            if rel in PAGE_FILES:
                pages[rel] = len(text.split())
            elif not rel.lower().endswith(CODE_EXT):
                words += len(text.split())
            hits += [f"{rel}:{h}" for h in scan_text(text, allow)]
    for name in PAGE_FILES:
        if name not in pages:
            hits.append(f"missing:{name}")
        elif pages[name] > page_cap:
            hits.append(f"{name}:over-page-cap:{pages[name]}")
    return hits, words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("submissions")
    ap.add_argument("--project", help="project.json; the resource and model hosts are taken from it")
    ap.add_argument("--allow", nargs="*", default=[], help="extra hosts allowed in URLs")
    ap.add_argument("--cap", type=int, default=1500, help="word cap on the specification + supporting files")
    ap.add_argument("--page-cap", type=int, default=600,
                    help="word cap on PROCESS.md and WRITTEN.md, checked per file")
    a = ap.parse_args()
    allow = list(a.allow)
    if a.project:
        try:
            proj = json.load(open(a.project))
        except OSError as e:
            sys.exit(f"--project: {e}")
        if proj.get("resource_host"):
            allow.append(proj["resource_host"])
        if proj.get("ollama_host"):
            h = urllib.parse.urlsplit(proj["ollama_host"]).hostname
            if h:
                allow.append(h)
        for e in proj.get("extra_allow_endpoints", []):
            allow.append(e.split(":")[0])
    if not allow:
        print("note: no allowed hosts given, so every URL will be flagged. "
              "Pass --project project.json.", file=sys.stderr)
    a.allow = list(dict.fromkeys(allow))
    for sid in sorted(os.listdir(a.submissions)):
        p = os.path.join(a.submissions, sid)
        if not os.path.isdir(p):
            continue
        hits, words = scan_submission(p, a.allow, a.cap, a.page_cap)
        status = "FLAG" if hits else "OK"
        if words > a.cap:
            status = "OVERCAP" if status == "OK" else "FLAG+OVERCAP"
        print(f"{status}\t{sid}\twords={words}\t" + " ".join(hits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
