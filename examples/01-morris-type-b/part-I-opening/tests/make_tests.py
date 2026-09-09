#!/usr/bin/env python3
"""Generate public and hidden tests for Part I (MiniMaxOpening) from the reference
solution, in the argv-files contract. Also reports how the canonical (twist-ignored)
solution fares on each case, so the professor can see the twist is load-bearing.

    python3 tests/make_tests.py            (run from part-I-opening/)
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PART = os.path.dirname(HERE)
REF = os.path.join(PART, "reference", "solution", "MiniMaxOpening.py")
CAN = os.path.join(PART, "canonical", "MiniMaxOpening.py")
CHECK = os.path.join(HERE, "check.py")


def B(**pieces):
    """Board from index->char pairs, e.g. B(W=[0,3], B=[9,15])."""
    b = ["x"] * 23
    for i in pieces.get("W", []):
        b[i] = "W"
    for i in pieces.get("B", []):
        b[i] = "B"
    return "".join(b)


# Diagonal spokes (the twist): (0,3,6) (2,5,7) (14,17,20) (16,19,22).
CASES = {
    # category: [(board, depth), ...]
    "opening_move": [
        (B(W=[9], B=[16]), 2),
        (B(W=[9], B=[16]), 3),
        (B(W=[10], B=[9]), 3),
        (B(W=[0, 3], B=[9, 15]), 3),        # diagonal threat changes the estimate at depth 3
        (B(W=[2, 5], B=[4, 12]), 3),
        (B(W=[8, 20], B=[17, 3]), 3),
    ],
    "opening_mill": [                         # best move closes a mill, mostly on a diagonal spoke
        (B(W=[0, 3], B=[9, 15]), 1),
        (B(W=[2, 5], B=[4, 12]), 1),
        (B(W=[14, 17], B=[10, 18]), 1),
        (B(W=[16, 19], B=[11, 15]), 1),
        (B(W=[0, 3, 8], B=[9, 15, 20]), 2),   # both a diagonal and a vertical are one away
        (B(W=[14, 17, 20, 21], B=[0, 1, 2, 9]), 2),  # black pieces in a mill are protected
    ],
    "evaluations_count": [                    # strict three-line match, depth 2 only
        (B(W=[9], B=[16]), 2),
        (B(W=[0, 3], B=[9, 15]), 2),
        (B(W=[2, 5, 12], B=[4, 13, 19]), 2),
        (B(W=[0, 1, 4, 9], B=[3, 8, 17, 20]), 2),
    ],
    "grad_depth4": [
        (B(W=[9], B=[16]), 4),
        (B(W=[0, 3], B=[9, 15]), 4),
        (B(W=[0, 2, 4, 9, 12], B=[1, 3, 5, 15, 20]), 4),
        (B(W=[14, 17, 10, 6], B=[20, 18, 15, 3]), 4),
    ],
}
PUBLIC = {"opening_move": [0, 2], "opening_mill": [1], "evaluations_count": [0]}
STRICT = {"evaluations_count"}


def run(prog, board, depth):
    tmp = tempfile.mkdtemp()
    inp, out = os.path.join(tmp, "in.txt"), os.path.join(tmp, "out.txt")
    open(inp, "w").write(board)
    p = subprocess.run([sys.executable, prog, inp, out, str(depth)], capture_output=True, text=True, timeout=120)
    outfile = open(out).read() if os.path.exists(out) else ""
    shutil.rmtree(tmp)
    return p.stdout, outfile.strip()


def write_case(d, n, board, depth, stdout, outfile):
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f"{n:03d}.args"), "w").write("{in} {out} " + str(depth) + "\n")
    open(os.path.join(d, f"{n:03d}.in.txt"), "w").write(board)
    open(os.path.join(d, f"{n:03d}.stdout.txt"), "w").write(stdout)
    open(os.path.join(d, f"{n:03d}.outfile.txt"), "w").write(outfile)


def main():
    for root in ("public", "hidden"):
        shutil.rmtree(os.path.join(HERE, root), ignore_errors=True)
    for cat, cases in CASES.items():
        hidden = os.path.join(HERE, "hidden", cat)
        public = os.path.join(HERE, "public", cat)
        for n, (board, depth) in enumerate(cases, 1):
            ref_out, ref_file = run(REF, board, depth)
            can_out, _ = run(CAN, board, depth)
            write_case(hidden, n, board, depth, ref_out, ref_file)
            if (n - 1) in PUBLIC.get(cat, []):
                write_case(public, len(os.listdir(public)) // 4 + 1 if os.path.isdir(public) else 1, board, depth, ref_out, ref_file)
            same = ref_out.strip() == can_out.strip()
            est_same = ref_out.strip().splitlines()[-1] == can_out.strip().splitlines()[-1]
            print(f"{cat} {n:03d} depth={depth} board={board} canonical: {'identical' if same else ('same estimate' if est_same else 'DIFFERENT estimate')}")
        if cat not in STRICT:
            shutil.copy(CHECK, os.path.join(hidden, "check.py"))
            if os.path.isdir(public):
                shutil.copy(CHECK, os.path.join(public, "check.py"))
    print("done")


if __name__ == "__main__":
    main()
