#!/usr/bin/env python3
"""Equivalence policy `estimate` for the Morris variant, opening phase.

    python3 check.py <in.txt> <expected.stdout.txt> <actual.json>
    actual.json = {"stdout": "...", "outfile": "..."}   (written by tools/run_tests.py)

Pass when:
  1. stdout is exactly three lines with the required prefixes and an integer count;
  2. the board on line 1 is a legal result of one White placement on the input board
     under the VARIANT topology (23 points, 18 mills), including the removal rule;
  3. the MINIMAX estimate equals the reference estimate in expected.stdout.txt;
  4. the output file holds the same board as line 1.
The positions-evaluated count is NOT compared here (see category evaluations_count).
"""
import json
import re
import sys

MILLS = [
    (0, 1, 2), (3, 4, 5), (8, 9, 10), (11, 12, 13), (14, 15, 16), (17, 18, 19), (20, 21, 22),
    (0, 8, 20), (2, 13, 22), (3, 9, 17), (5, 12, 19), (6, 10, 14), (7, 11, 16),
    (0, 3, 6), (2, 5, 7), (14, 17, 20), (16, 19, 22), (15, 18, 21),
]


def close_mill(loc, board):
    c = board[loc]
    return any(loc in m and all(board[p] == c for p in m if p != loc) for m in MILLS)


def legal_results(board):
    out = set()
    for i in range(23):
        if board[i] != "x":
            continue
        b = board[:i] + "W" + board[i + 1:]
        if close_mill(i, b):
            removable = [j for j in range(23) if b[j] == "B" and not close_mill(j, b)]
            if removable:
                for j in removable:
                    out.add(b[:j] + "x" + b[j + 1:])
            else:
                out.add(b)
        else:
            out.add(b)
    return out


def parse(stdout):
    lines = [l.rstrip() for l in stdout.strip().splitlines()]
    if len(lines) != 3:
        return None, f"expected 3 lines, got {len(lines)}"
    m1 = re.fullmatch(r"Board Position: ([WBx]{23})\.?", lines[0])
    m2 = re.fullmatch(r"Positions evaluated by static estimation: (\d+)\.", lines[1])
    m3 = re.fullmatch(r"MINIMAX estimate: (-?\d+)\.", lines[2])
    if not (m1 and m2 and m3):
        return None, "format: " + " | ".join(lines)[:120]
    return (m1.group(1), int(m2.group(1)), int(m3.group(1))), None


def main():
    in_path, exp_path, act_path = sys.argv[1:4]
    board = open(in_path).read().strip()
    actual = json.load(open(act_path))
    got, err = parse(actual.get("stdout", ""))
    if err:
        print(err); return 1
    exp, err = parse(open(exp_path).read())
    if err:
        print("bad expected file: " + err); return 2
    a_board, a_count, a_est = got
    e_board, e_count, e_est = exp
    if a_board not in legal_results(board):
        print(f"board {a_board} is not a legal White result of {board}"); return 1
    if a_est != e_est:
        print(f"estimate {a_est} != reference {e_est}"); return 1
    if (actual.get("outfile") or "").strip() != a_board:
        print("output file does not hold the printed board"); return 1
    print("estimate ok, board legal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
