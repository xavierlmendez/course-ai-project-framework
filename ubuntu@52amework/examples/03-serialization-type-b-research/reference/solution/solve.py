#!/usr/bin/env python3
"""Reference Bencode-L encoder (professor's solution)."""
import json
import sys

sys.setrecursionlimit(10000)


def enc(v, out):
    if v is True:
        out.append(b"t")
    elif v is False:
        out.append(b"f")
    elif v is None:
        out.append(b"n")
    elif isinstance(v, int):
        out.append(b"i%de" % v)
    elif isinstance(v, str):
        b = v.encode("utf-8")
        out.append(("%x:" % len(b)).encode("ascii"))
        out.append(b)
    elif isinstance(v, list):
        out.append(b"l")
        for x in v:
            enc(x, out)
        out.append(b"e")
    elif isinstance(v, dict):
        out.append(b"d")
        for k in sorted(v, key=lambda k: (len(k.encode("utf-8")), k.encode("utf-8"))):
            enc(k, out)
            enc(v[k], out)
        out.append(b"e")
    else:
        raise ValueError("unsupported type: %r" % type(v))


def main():
    data = json.load(sys.stdin)
    out = []
    enc(data["value"], out)
    json.dump({"hex": b"".join(out).hex()}, sys.stdout)


if __name__ == "__main__":
    main()
