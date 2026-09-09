#!/usr/bin/env python3
"""Generate public and hidden test cases from the reference solution.
Run from the example directory: python3 tests/make_tests.py
Professor-only: it contains the hidden cases."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "reference", "solution", "solve.py")


def expected(value):
    p = subprocess.run([sys.executable, REF], input=json.dumps({"value": value}).encode(), capture_output=True, check=True)
    return json.loads(p.stdout)


def write(suite, cat, cases):
    d = os.path.join(HERE, suite, cat)
    os.makedirs(d, exist_ok=True)
    for i, v in enumerate(cases, 1):
        with open(os.path.join(d, f"{i:03d}.in.json"), "w") as fh:
            json.dump({"value": v}, fh)
        with open(os.path.join(d, f"{i:03d}.out.json"), "w") as fh:
            json.dump(expected(v), fh)


PUBLIC = {
    "basic_scalars": ["spam", 3],
    "lists": [["spam", "eggs"]],
    "dicts": [{"cow": "moo", "spam": "eggs"}],
    "twist_length_prefix": ["0123456789"],       # hints at hex prefixes
    "twist_bool_null": [True],                   # hints at t/f/n
}

HIDDEN = {
    "basic_scalars": ["", "a", -3, 0, 12345678901234567890, "é", "hello world", "日本"],
    "lists": [[], [1, 2, 3], ["a", ["b", ["c"]]], [[], [[]]], [1, "x", [2, "y"]], ["spam", "eggs", "ham"]],
    "dicts": [{}, {"a": 1}, {"b": 2, "a": 1}, {"k": {"j": [1, {"i": "v"}]}}, {"cow": "moo", "spam": ["a", "b"]}, {"x": {}, "y": []}],
    "twist_length_prefix": ["0123456789", "x" * 16, "y" * 255, "z" * 256, ["0123456789ab", "0123456789abcdef"],
                            {"key": "0123456789abcdef0123456789"}, "ü" * 8, "abcdefghij" * 3],
    "twist_key_order": [{"bb": 1, "a": 2, "ccc": 3}, {"z": 1, "aa": 2}, {"ab": 1, "aa": 2, "b": 3},
                        {"é": 1, "zz": 2, "a": 3}, {"spam": 1, "cow": 2, "eggs": 3, "z": 4},
                        {"outer": {"bb": 1, "a": {"ccc": 1, "dd": 2, "e": 3}}}, {"aaa": 1, "abc": 2, "aab": 3, "ab": 4}],
    "twist_bool_null": [True, False, None, [True, False, None], {"t": True, "f": False, "n": None},
                        [1, True, 0, False], {"a": [None, [None]]}, {"flag": True, "count": 1}],
    "grad_deep_nesting": [
        (lambda d: (lambda f: f(f, d))(lambda f, n: [] if n == 0 else [f(f, n - 1)]))(400),
        (lambda d: (lambda f: f(f, d))(lambda f, n: {} if n == 0 else {"k": f(f, n - 1)}))(300),
        list(range(5000)),
        {"k%04d" % i: i for i in range(2000)},
        ["s" * 1000] * 500,
    ],
}

if __name__ == "__main__":
    for cat, cases in PUBLIC.items():
        write("public", cat, cases)
    for cat, cases in HIDDEN.items():
        write("hidden", cat, cases)
    print("wrote", sum(map(len, PUBLIC.values())), "public and", sum(map(len, HIDDEN.values())), "hidden cases")
