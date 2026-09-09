#!/usr/bin/env python3
"""Reference ledger server: serves the published resource and appends signed
ledger entries to a text file. Standard library only.

    GET  /                       the published resource (resource/index.md rendered
                                 as text/plain; {{NONCE}}, {{VARIANT}}, {{BASE_URL}} substituted)
    GET  /?v=<variant>           same, with the per-student variant parameter
    GET  /<file>                 any other file under resource/ (e.g. examples)
    GET  /ledger                 the HTML form (a text box and a submit button)
    POST /ledger                 append an entry. Form or JSON fields:
                                   student_id  "ABC123456" or "ABC123456,DEF654321"
                                   nonce       must equal the project nonce
                                   run_tag     optional, default "practice"
                                   variant     optional
                                 Returns 200 "ok" or 400 with a plain reason.

The ledger file is never served. Read it on the server.

Usage:
    ledger_server.py --resource DIR --ledger FILE --nonce STRING [--port 8080]
    ledger_server.py --project project.json [--port 8080]      # practice server:
        resource/ and ledger.tsv beside project.json, port from its resource_port,
        nonce from its "nonce" key or a random practice nonce that is printed.
"""
import argparse
import datetime
import http.server
import json
import os
import re
import secrets
import urllib.parse

ID_RE = re.compile(r"^[A-Z]{3}[0-9]{6}$")
TAG_RE = re.compile(r"^[a-z0-9_-]{1,32}$")
VAR_RE = re.compile(r"^[A-Za-z0-9_-]{0,32}$")

FORM = """<!doctype html><title>Course ledger</title>
<h1>Course ledger</h1>
<form method="post" action="/ledger">
<label>Student ID(s), comma-separated: <input name="student_id" size="24"></label><br>
<label>Nonce from the resource page: <input name="nonce" size="24"></label><br>
<label>Run tag: <input name="run_tag" value="practice"></label><br>
<label>Variant (if your URL had one): <input name="variant"></label><br>
<button type="submit">Sign the ledger</button>
</form>
<p>The ledger is write-only. Entries are visible to course staff only.</p>"""


def make_handler(resource_dir, ledger_path, nonce, base_url):
    class H(http.server.BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="text/plain; charset=utf-8"):
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urllib.parse.urlsplit(self.path)
            q = urllib.parse.parse_qs(u.query)
            path = u.path
            if path == "/ledger":
                return self._send(200, FORM, "text/html; charset=utf-8")
            rel = "index.md" if path in ("", "/") else path.lstrip("/")
            full = os.path.realpath(os.path.join(resource_dir, rel))
            root = os.path.realpath(resource_dir)
            # commonpath, not startswith: a sibling directory whose name merely starts with
            # the resource directory's name (resource-private/) would pass a prefix test.
            try:
                contained = os.path.commonpath([full, root]) == root
            except ValueError:
                contained = False
            if not contained or not os.path.isfile(full):
                return self._send(404, "not found")
            text = open(full, encoding="utf-8").read()
            variant = q.get("v", [""])[0]
            if not VAR_RE.match(variant):
                return self._send(400, "bad variant")
            text = text.replace("{{NONCE}}", nonce).replace("{{VARIANT}}", variant).replace("{{BASE_URL}}", base_url)
            return self._send(200, text)

        def do_POST(self):
            if urllib.parse.urlsplit(self.path).path != "/ledger":
                return self._send(404, "not found")
            n = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(n).decode(errors="replace")
            ctype = self.headers.get("Content-Type", "")
            if "json" in ctype:
                try:
                    fields = {k: str(v) for k, v in json.loads(raw).items()}
                except Exception:
                    return self._send(400, "bad json")
            else:
                fields = {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}
            ids = [s.strip().upper() for s in fields.get("student_id", "").split(",") if s.strip()]
            if not ids or len(ids) > 2:
                return self._send(400, "student_id: give one or two IDs, comma-separated")
            bad = [i for i in ids if not ID_RE.match(i)]
            if bad:
                return self._send(400, f"student_id must be three letters + six digits (XXXNNNNNN): {','.join(bad)}")
            if fields.get("nonce", "") != nonce:
                return self._send(400, "nonce does not match the published resource; fetch the page and copy it exactly")
            tag = fields.get("run_tag", "practice") or "practice"
            if not TAG_RE.match(tag):
                return self._send(400, "run_tag: lowercase letters, digits, - or _")
            variant = fields.get("variant", "")
            if not VAR_RE.match(variant):
                return self._send(400, "bad variant")
            ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
            line = "\t".join([ts, "+".join(ids), tag, variant, self.client_address[0]])
            with open(ledger_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            return self._send(200, "ok: ledger signed for " + "+".join(ids))

        def log_message(self, fmt, *args):  # quieter
            pass

    return H


def from_project(a):
    """Fill --resource, --ledger, --nonce and --port from a project.json.

    The one-line form a handout can give a student: everything the server needs is
    already in the project directory. An explicit flag still wins. The nonce is a
    per-semester secret the professor passes with --nonce; without one, a random
    nonce is generated and printed, which is all a practice server needs because the
    page it serves and the entries it accepts then agree with each other.
    """
    d = os.path.dirname(os.path.abspath(a.project))
    with open(a.project) as fh:
        proj = json.load(fh)
    a.resource = a.resource or os.path.join(d, proj.get("resource_dir", "resource"))
    a.ledger = a.ledger or os.path.join(d, proj.get("ledger_file", "ledger.tsv"))
    a.nonce = a.nonce or proj.get("nonce") or ("practice-" + secrets.token_hex(4))
    if a.port is None:
        a.port = proj.get("resource_port", 8080)
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", help="project.json; fills --resource, --ledger, --nonce and --port")
    ap.add_argument("--resource")
    ap.add_argument("--ledger")
    ap.add_argument("--nonce")
    ap.add_argument("--port", type=int)
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--base-url", help="absolute URL students/harnesses use to reach this server (substituted for {{BASE_URL}})")
    a = ap.parse_args()
    if a.project:
        from_project(a)
    missing = [f for f in ("resource", "ledger", "nonce") if not getattr(a, f)]
    if missing:
        ap.error("give --project, or " + " and ".join("--" + m for m in missing))
    if a.port is None:
        a.port = 8080
    base_url = (a.base_url or f"http://localhost:{a.port}").rstrip("/")
    if not os.path.exists(a.ledger):
        with open(a.ledger, "w") as fh:
            fh.write(f"# ledger\tnonce={a.nonce}\tstarted={datetime.datetime.now(datetime.timezone.utc).date()}\n")
            fh.write("# utc_timestamp\tstudent_ids\trun_tag\tvariant\tclient\n")
    srv = http.server.ThreadingHTTPServer((a.bind, a.port), make_handler(os.path.abspath(a.resource), a.ledger, a.nonce, base_url))
    print(f"serving {a.resource} on :{a.port}; ledger -> {a.ledger}; nonce {a.nonce}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
