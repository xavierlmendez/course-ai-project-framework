#!/usr/bin/env python3
"""Generate tests for Part II (ABOpening). Expected stdout comes from the Part I
MINIMAX reference, so check.py can require equal estimates and fewer evaluations.
    python3 tests/make_tests.py   (run from part-II/)
"""
import os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); PART = os.path.dirname(HERE)
MM_REF = os.path.join(os.path.dirname(PART), "part-I", "reference", "solution", "MiniMaxOpening.py")
AB_REF = os.path.join(PART, "reference", "solution", "ABOpening.py")
AB_CAN = os.path.join(PART, "canonical", "ABOpening.py")
CHECK = os.path.join(HERE, "check.py")

def B(**p):
    b = ["x"] * 23
    for i in p.get("W", []): b[i] = "W"
    for i in p.get("B", []): b[i] = "B"
    return "".join(b)

CASES = {"ab_pruning": [(B(W=[9], B=[16]), 3), (B(W=[10], B=[9]), 3), (B(W=[0, 3], B=[9, 15]), 3),
                        (B(W=[2, 5, 12], B=[4, 13, 19]), 3)],
         "grad_depth4": [(B(W=[9], B=[16]), 4), (B(W=[0, 2, 4, 9, 12], B=[1, 3, 5, 15, 20]), 4)]}
PUBLIC = {"ab_pruning": [0, 2]}

def run(prog, board, depth):
    tmp = tempfile.mkdtemp(); inp, out = os.path.join(tmp, "in.txt"), os.path.join(tmp, "out.txt")
    open(inp, "w").write(board)
    p = subprocess.run([sys.executable, prog, inp, out, str(depth)], capture_output=True, text=True, timeout=120)
    shutil.rmtree(tmp); return p.stdout

def write_case(d, n, board, depth, stdout):
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f"{n:03d}.args"), "w").write("{in} {out} " + str(depth) + "\n")
    open(os.path.join(d, f"{n:03d}.in.txt"), "w").write(board)
    open(os.path.join(d, f"{n:03d}.stdout.txt"), "w").write(stdout)

def main():
    for root in ("public", "hidden"): shutil.rmtree(os.path.join(HERE, root), ignore_errors=True)
    for cat, cases in CASES.items():
        hidden, public = os.path.join(HERE, "hidden", cat), os.path.join(HERE, "public", cat)
        pn = 0
        for n, (board, depth) in enumerate(cases, 1):
            mm = run(MM_REF, board, depth); ab = run(AB_REF, board, depth); can = run(AB_CAN, board, depth)
            write_case(hidden, n, board, depth, mm)
            if (n - 1) in PUBLIC.get(cat, []): pn += 1; write_case(public, pn, board, depth, mm)
            cnt = lambda s: int(s.splitlines()[1].split(":")[1].strip(" ."))
            print(f"{cat} {n:03d} depth={depth} minimax={cnt(mm)} ab={cnt(ab)} canonical(ab)={cnt(can)}")
        shutil.copy(CHECK, os.path.join(hidden, "check.py"))
        if os.path.isdir(public): shutil.copy(CHECK, os.path.join(public, "check.py"))
    print("done")

if __name__ == "__main__": main()
