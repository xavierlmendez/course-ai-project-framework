"""The sandbox: what a student's code can reach from inside it.

These tests build the image and run containers, so they are slower than the rest of
the suite and are skipped when Docker is unavailable. They are the proof for Phase 2's
exit criterion: each one fails against the unfixed sandbox.

    python3 -m unittest tests.test_sandbox
"""
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import TempCase, ROOT  # noqa: E402

IMAGE = "harness-sandbox-test"
SANDBOX_DIR = os.path.join(ROOT, "tools", "sandbox")


def docker_available():
    if not shutil.which("docker"):
        return False
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0


def setUpModule():
    if not docker_available():
        raise unittest.SkipTest("docker is not available")
    p = subprocess.run(["docker", "build", "-q", "-t", IMAGE, SANDBOX_DIR],
                       capture_output=True, text=True, timeout=1800)
    if p.returncode != 0:
        raise unittest.SkipTest(f"sandbox image failed to build:\n{p.stderr[-2000:]}")


def host_listener(port):
    """A trivial TCP listener on the host, so 'reachable' and 'blocked' are distinguishable
    rather than both being connection failures."""
    code = ("import http.server,sys;"
            "http.server.HTTPServer(('0.0.0.0',%d), http.server.SimpleHTTPRequestHandler)"
            ".serve_forever()" % port)
    return subprocess.Popen([sys.executable, "-c", code],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_in_sandbox(args, env=None, network=True, mounts=(), timeout=120, entry=None):
    cmd = ["docker", "run", "--rm"]
    for src, dst, mode in mounts:
        cmd += ["-v", f"{src}:{dst}:{mode}" if mode else f"{src}:{dst}"]
    if network:
        cmd += ["--cap-add", "NET_ADMIN", "--add-host", "host.docker.internal:host-gateway"]
    else:
        cmd += ["--network", "none"]
    for k, v in (env or {}).items():
        cmd += ["-e", f"{k}={v}"]
    if entry:
        cmd += ["--entrypoint", entry]
    cmd += [IMAGE] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


class TestOutboundNetwork(TempCase):
    """F-08, F-09, F-49: what the allowlist actually allows."""

    ALLOW = "ALLOW_ENDPOINTS"

    def test_unlisted_host_is_blocked(self):
        r = run_in_sandbox(
            ["bash", "-c", "curl -s -m 6 -o /dev/null -w '%{http_code}' https://example.com || echo blocked"],
            env={self.ALLOW: "host.docker.internal:11434"})
        self.assertIn("blocked", r.stdout + r.stderr,
                      f"an unlisted host was reachable: {r.stdout!r}")

    def test_allowed_endpoint_is_reachable(self):
        """The allowlist must still let the two endpoints the task needs through, or the
        blocking tests below would pass on a sandbox that simply blocks everything."""
        proc = host_listener(18081)
        self.addCleanup(proc.terminate)
        r = run_in_sandbox(
            ["bash", "-c", "sleep 1; curl -s -m 8 -o /dev/null -w '%{http_code}' "
                           "http://host.docker.internal:18081/ || echo blocked"],
            env={self.ALLOW: "host.docker.internal:18081"})
        self.assertIn("200", r.stdout, f"an allowed endpoint was not reachable: {r.stdout!r}")

    def test_unlisted_port_on_an_allowed_host_is_blocked(self):
        """The allowlist names a host and a port. Allowing every port on a host exposes
        every service on the TA's machine, including the model server's management API,
        which can read and overwrite the pinned slot models."""
        proc = host_listener(18082)
        self.addCleanup(proc.terminate)
        r = run_in_sandbox(
            ["bash", "-c", "sleep 1; curl -s -m 8 -o /dev/null -w '%{http_code}' "
                           "http://host.docker.internal:18082/ || echo blocked"],
            env={self.ALLOW: "host.docker.internal:11434"})
        self.assertIn("blocked", r.stdout + r.stderr,
                      f"a listening port that was never allowed was reachable: {r.stdout!r}")

    def test_dns_to_an_arbitrary_resolver_is_blocked(self):
        """F-09: allowing udp/53 to any destination is a tunnel out of the allowlist."""
        r = run_in_sandbox(
            ["bash", "-c", "timeout 8 dig +short +tries=1 +time=3 @1.1.1.1 example.com "
                           "|| echo blocked"],
            env={self.ALLOW: "host.docker.internal:11434"})
        self.assertIn("blocked", r.stdout + r.stderr,
                      f"DNS to an outside resolver succeeded: {r.stdout!r}")

    def test_ipv6_is_blocked(self):
        r = run_in_sandbox(
            ["bash", "-c", "curl -s -6 -m 6 -o /dev/null -w '%{http_code}' "
                           "'http://[2606:4700:4700::1111]/' || echo blocked"],
            env={self.ALLOW: "host.docker.internal:11434"})
        self.assertIn("blocked", r.stdout + r.stderr,
                      f"outbound IPv6 was reachable: {r.stdout!r}")

    def test_loopback_still_works(self):
        r = run_in_sandbox(["bash", "-c", "curl -s -m 4 -o /dev/null -w '%{http_code}' "
                                          "http://127.0.0.1:1 ; echo ' rc='$?"],
                           env={self.ALLOW: "host.docker.internal:11434"})
        # connection refused (rc 7) proves the packet was not dropped by the firewall
        self.assertIn("rc=7", r.stdout, f"loopback appears to be filtered: {r.stdout!r}")


class TestHiddenTestIsolation(TempCase):
    """F-07: the graded solution must not be able to read the expected outputs."""

    def setUp(self):
        super().setUp()
        self.make_test_suite("tests", {"basic": 2})
        self.write("work/solve.py", "import json,sys\nd=json.load(sys.stdin)\nprint(json.dumps(d))\n")

    def mounts(self):
        return [(self.path("work"), "/work", None),
                (os.path.join(ROOT, "tools"), "/tools", "ro"),
                (self.path("tests"), "/root/tests-src", "ro")]

    def test_the_unprivileged_user_cannot_read_the_expected_outputs(self):
        """Whatever the solution does, it runs as the unprivileged user. That user must
        not be able to open an .out.json. The first half proves the file is really there,
        so a DENIED from a missing file cannot pass this test."""
        r = run_in_sandbox(
            ["runtests", "bash", "-c",
             "P=/tests/basic/001.out.json; "
             "cat \"$P\" >/dev/null 2>&1 && echo ROOT_CAN_READ || echo ROOT_CANNOT; "
             "id runner >/dev/null 2>&1 && echo USER_EXISTS || echo NO_USER; "
             "su -s /bin/bash runner -c \"cat $P\" >/dev/null 2>&1 && echo LEAKED || echo DENIED; "
             "su -s /bin/bash runner -c 'cat /root/tests-src/basic/001.out.json' >/dev/null 2>&1 "
             "&& echo MOUNT_LEAKED || echo MOUNT_DENIED"],
            network=False, mounts=self.mounts())
        self.assertIn("ROOT_CAN_READ", r.stdout, f"the expected outputs are not where the test looks: {r.stdout!r}")
        self.assertIn("USER_EXISTS", r.stdout, f"the unprivileged user is missing: {r.stdout!r}")
        self.assertIn("DENIED", r.stdout,
                      f"the graded user could read an expected output: {r.stdout!r}")
        self.assertIn("MOUNT_DENIED", r.stdout,
                      f"the graded user reached the tests through the read-only mount: {r.stdout!r}")

    def test_a_cheating_solution_scores_zero(self):
        """End to end: a solution that looks up the answer instead of computing it."""
        self.write("work/solve.py",
                   "import glob,json,sys\n"
                   "hits=sorted(glob.glob('/tests*/**/*.out.json', recursive=True))\n"
                   "sys.stderr.write('VISIBLE=%d\\n' % len(hits))\n"
                   "print(json.dumps(json.load(open(hits[0])) if hits else {'n': -1}))\n")
        r = run_in_sandbox(
            ["runtests", "python3", "/tools/run_tests.py", "--solution", "/work", "--tests", "/tests",
             "--entry", "solve.py", "--json"],
            network=False, mounts=self.mounts())
        self.assertTrue(r.stdout.strip(), f"no summary:\n{r.stderr[-1200:]}")
        summary = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(summary["categories"]["basic"]["pass"], 0,
                         f"a solution that read the answers scored marks: {summary}")

    def test_a_correct_solution_still_passes(self):
        r = run_in_sandbox(
            ["runtests", "python3", "/tools/run_tests.py", "--solution", "/work", "--tests", "/tests",
             "--entry", "solve.py", "--json"],
            network=False, mounts=self.mounts())
        self.assertTrue(r.stdout.strip(), f"no output from the test runner:\n{r.stderr[-1500:]}")
        summary = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(summary["categories"]["basic"]["pass"], 2,
                         f"isolation broke ordinary grading: {r.stderr[-1000:]}")


class TestHarnessPinning(TempCase):
    """F-10: the harness version must be fixed, or the temperature schedule can change
    under the course without warning."""

    def test_image_pins_an_exact_opencode_version(self):
        text = open(os.path.join(SANDBOX_DIR, "Dockerfile")).read()
        self.assertNotIn("opencode-ai@latest", text,
                         "the sandbox installs whatever OpenCode is current on build day")

    def test_installed_version_matches_the_pin(self):
        text = open(os.path.join(SANDBOX_DIR, "Dockerfile")).read()
        m = (re.search(r"ARG\s+OPENCODE_VERSION=([0-9][^\s]*)", text)
             or re.search(r"opencode-ai@([0-9][^\s\\\"']*)", text))
        self.assertIsNotNone(m, "the Dockerfile does not pin an OpenCode version")
        r = run_in_sandbox(["bash", "-c", "opencode --version"], network=False)
        self.assertIn(m.group(1), r.stdout.strip(),
                      f"the image has {r.stdout.strip()!r}, the Dockerfile pins {m.group(1)!r}")


if __name__ == "__main__":
    unittest.main()
