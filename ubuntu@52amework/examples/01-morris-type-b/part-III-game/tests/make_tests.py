#!/usr/bin/env python3
"""Generate public and hidden tests for III-game (MiniMaxGameBlack) from the reference solution,
in the argv-files contract. Every case is produced by running a program, never typed by
hand. The run also reports what the canonical (twist-ignoring) solution does on each
case, so the professor can see which categories the twist is load-bearing in.

    python3 tests/make_tests.py            (run from part-III-game/)
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PART = os.path.dirname(HERE)
EXAMPLE = os.path.dirname(PART)
REF = os.path.join(PART, "reference", "solution", "MiniMaxGameBlack.py")
CAN = os.path.join(PART, "canonical", "MiniMaxGameBlack.py")
# The file the expected stdout comes from. For an `ab` category it is the MINIMAX
# program, so check.py can demand an equal estimate and a strictly lower count.
EXPECTED = REF

CASES = {
    "black_game_move": [
        ("xWxxxxxBxxWWxBBWxxxBBxW", 2),
        ("WxxxxxxBxBxxxWxBWxBBxWW", 2),
        ("WWxBxxWBWxxxxBBWxxxBxxx", 2),
        ("WxxBxxxxxWWxxWxBxBxBxBW", 2),
        ("BWxxWxxBBWxBxxxWxxxxBWx", 2),
    ],
    "black_hopping": [
        ("WxxBxxWxxxWxBxWxxBWxxxx", 2),
        ("xBxxxxBxWxWWWxxxxxxxxWB", 2),
        ("BWxxxxxxWxWxWBxBxxxxWxx", 2),
        ("xBxxBxxxxxxxWxWWWBxxxxW", 2),
    ],
    "black_game_mill": [
        ("xBBxBxWBWxxxWWxWxxxBxxx", 2),
        ("xBWBxWBxxBxxxxWxWxxxWxB", 2),
        ("xBBxxxxBWxBWBxxWxxxWxWx", 2),
        ("xWWBxxxxWBBxWxxxxBWxBxx", 2),
        ("xWBxWxWBxxBWBxWxxxxxBxx", 2),
        ("BBWxBxBWxxxxxxxBWxxxWWx", 2),
    ],
    "grad_depth3": [
        ("BWxWxBxxxxWxxxxxxxxBxWB", 3),
        ("xWWxxxBxBxxWxWxxxBxBxxx", 3),
        ("xxxBBxWxxBWxWxxBxWxxxxx", 3),
        ("xBxxWxxxxBxWxWxBxxxBxWx", 3),
    ],
}

POLICY = {
    "black_game_move": "estimate",
    "black_hopping": "estimate",
    "black_game_mill": "estimate",
    "grad_depth3": "estimate"
}

PUBLIC = {
    "black_game_move": [
        0,
        1
    ],
    "black_game_mill": [
        0
    ]
}

# Which checker file implements each policy in this directory.
CHECKER = {"estimate": "check.py", "ab": "check.py", "valid": "check_valid.py"}


def run(prog, board, depth):
    tmp = tempfile.mkdtemp()
    inp, out = os.path.join(tmp, "in.txt"), os.path.join(tmp, "out.txt")
    with open(inp, "w") as fh:
        fh.write(board)
    p = subprocess.run([sys.executable, prog, inp, out, str(depth)],
                       capture_output=True, text=True, timeout=300)
    outfile = open(out).read() if os.path.exists(out) else ""
    shutil.rmtree(tmp, ignore_errors=True)
    return p.stdout, outfile.strip()


def write_case(d, n, board, depth, stdout, outfile):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{n:03d}.args"), "w") as fh:
        fh.write("{in} {out} " + str(depth) + "\n")
    with open(os.path.join(d, f"{n:03d}.in.txt"), "w") as fh:
        fh.write(board)
    with open(os.path.join(d, f"{n:03d}.stdout.txt"), "w") as fh:
        fh.write(stdout)
    if outfile is not None:
        with open(os.path.join(d, f"{n:03d}.outfile.txt"), "w") as fh:
            fh.write(outfile)


def estimate_of(stdout):
    return stdout.strip().splitlines()[-1]


def main():
    for root in ("public", "hidden"):
        shutil.rmtree(os.path.join(HERE, root), ignore_errors=True)
    for cat, cases in CASES.items():
        policy = POLICY[cat]
        hidden = os.path.join(HERE, "hidden", cat)
        public = os.path.join(HERE, "public", cat)
        pn = 0
        for n, (board, depth) in enumerate(cases, 1):
            exp_out, exp_file = run(EXPECTED, board, depth)
            ref_out, _ = run(REF, board, depth)
            can_out, _ = run(CAN, board, depth)
            # `strict` compares all three lines and the output file; the other policies
            # have a checker and ignore the output file.
            of = exp_file if policy == "strict" else None
            write_case(hidden, n, board, depth, exp_out, of)
            if (n - 1) in PUBLIC.get(cat, []):
                pn += 1
                write_case(public, pn, board, depth, exp_out, of)
            same = ref_out.strip() == can_out.strip()
            est_same = estimate_of(ref_out) == estimate_of(can_out)
            verdict = "identical" if same else ("same estimate" if est_same else "DIFFERENT estimate")
            print(f"{cat} {n:03d} depth={depth} board={board} canonical: {verdict}")
        if policy != "strict":
            src = os.path.join(HERE, CHECKER[policy])
            shutil.copy(src, os.path.join(hidden, "check.py"))
            if os.path.isdir(public):
                shutil.copy(src, os.path.join(public, "check.py"))
    print("done")


if __name__ == "__main__":
    main()
