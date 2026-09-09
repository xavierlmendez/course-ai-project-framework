#!/usr/bin/env python3
"""Canonical BEP 3 bencoder, twist ignored. Booleans as integers (a common library choice); null unsupported."""
import json
import sys


def enc(v, out):
    if isinstance(v, bool):
        out.append(b"i1e" if v else b"i0e")
    elif isinstance(v, int):
        out.append(b"i%de" % v)
    elif isinstance(v, str):
        b = v.encode("utf-8")
        out.append(b"%d:" % len(b))
        out.append(b)
    elif isinstance(v, list):
        out.append(b"l")
        for x in v:
            enc(x, out)
        out.append(b"e")
    elif isinstance(v, dict):
        out.append(b"d")
        for k in sorted(v, key=lambda k: k.encode("utf-8")):
            enc(k, out)
            enc(v[k], out)
        out.append(b"e")
    else:
        raise ValueError("unsupported")


def main():
    data = json.load(sys.stdin)
    out = []
    enc(data["value"], out)
    json.dump({"hex": b"".join(out).hex()}, sys.stdout)


if __name__ == "__main__":
    main()
