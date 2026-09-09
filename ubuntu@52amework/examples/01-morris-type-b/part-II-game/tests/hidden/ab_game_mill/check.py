#!/usr/bin/env python3
"""Equivalence policy `ab` for the Morris variant, midgame/endgame phase, White to move.

    python3 check.py <in.txt> <expected.stdout.txt> <actual.json>
    actual.json = {"stdout": "...", "outfile": "..."}   (written by tools/run_tests.py)

Pass when:
  1. stdout is exactly three lines with the required prefixes and integer values;
  2. the board on line 1 is a legal result of ONE White move on the input board under
     the VARIANT topology (23 points, 18 mills, four diagonal spokes), including the
     mill-capture rule and hopping when the mover holds exactly three pieces;
  3. the output file holds the same board as line 1;
  4. the MINIMAX estimate equals the estimate the MINIMAX reference printed on the
     same board and depth (expected.stdout.txt), and
  5. the positions-evaluated count is STRICTLY LOWER than that reference's count,
     which is what pruning has to buy.
"""
import json
import re
import sys

NEIGHBORS = {
    0: [1, 3, 8], 1: [0, 2, 4], 2: [1, 5, 13], 3: [0, 4, 6, 9], 4: [1, 3, 5],
    5: [2, 4, 7, 12], 6: [3, 10], 7: [5, 11], 8: [0, 9, 20], 9: [3, 8, 10, 17],
    10: [6, 9, 14], 11: [7, 12, 16], 12: [5, 11, 13, 19], 13: [2, 12, 22],
    14: [10, 15, 17], 15: [14, 16, 18], 16: [11, 15, 19], 17: [9, 14, 18, 20],
    18: [15, 17, 19, 21], 19: [12, 16, 18, 22], 20: [8, 17, 21], 21: [20, 18, 22],
    22: [13, 19, 21],
}

MILLS = [
    (0, 1, 2), (3, 4, 5), (8, 9, 10), (11, 12, 13), (14, 15, 16), (17, 18, 19), (20, 21, 22),
    (0, 8, 20), (2, 13, 22), (3, 9, 17), (5, 12, 19), (6, 10, 14), (7, 11, 16),
    (0, 3, 6), (2, 5, 7), (14, 17, 20), (16, 19, 22), (15, 18, 21),
]

PHASE = "game"      # "opening" or "game" (midgame/endgame)
SIDE = "W"        # "W" or "B" -- the side to move at the root
MODE = "ab"        # "estimate", "ab" or "valid"


def close_mill(loc, board):
    c = board[loc]
    return any(loc in m and all(board[p] == c for p in m if p != loc) for m in MILLS)


def swap_colors(board):
    return board.translate(str.maketrans("WB", "BW"))


def with_removals(b, out):
    """Add every board reachable from b by removing one non-mill Black piece."""
    removable = [j for j in range(23) if b[j] == "B" and not close_mill(j, b)]
    if removable:
        for j in removable:
            out.add(b[:j] + "x" + b[j + 1:])
    else:
        out.add(b)


def place_white(board, out):
    for i in range(23):
        if board[i] != "x":
            continue
        b = board[:i] + "W" + board[i + 1:]
        if close_mill(i, b):
            with_removals(b, out)
        else:
            out.add(b)


def move_white(board, out):
    """Midgame slide, or endgame hop when White holds exactly three pieces."""
    hopping = board.count("W") == 3
    for i in range(23):
        if board[i] != "W":
            continue
        targets = range(23) if hopping else NEIGHBORS[i]
        for j in targets:
            if board[j] != "x":
                continue
            b = board[:i] + "x" + board[i + 1:]
            b = b[:j] + "W" + b[j + 1:]
            if close_mill(j, b):
                with_removals(b, out)
            else:
                out.add(b)


def legal_results(board):
    """Every board that is one legal move of SIDE away from `board`."""
    base = swap_colors(board) if SIDE == "B" else board
    out = set()
    if PHASE == "opening":
        place_white(base, out)
    else:
        move_white(base, out)
    return {swap_colors(b) for b in out} if SIDE == "B" else out


def parse(stdout):
    lines = [l.rstrip() for l in (stdout or "").strip().splitlines()]
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
        print(err)
        return 1
    a_board, a_count, a_est = got
    if a_board not in legal_results(board):
        print(f"board {a_board} is not a legal W result of {board}")
        return 1
    if (actual.get("outfile") or "").strip() != a_board:
        print("output file does not hold the printed board")
        return 1
    if MODE == "valid":
        print("legal move, format ok")
        return 0
    exp, err = parse(open(exp_path).read())
    if err:
        print("bad expected file: " + err)
        return 2
    _, e_count, e_est = exp
    if a_est != e_est:
        print(f"estimate {a_est} != reference {e_est}")
        return 1
    if MODE == "ab":
        if a_count >= e_count:
            print(f"evaluations {a_count} not lower than minimax {e_count}: no pruning")
            return 1
        print(f"ab ok: estimate {a_est}, {a_count} < {e_count}")
        return 0
    print("estimate ok, board legal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
