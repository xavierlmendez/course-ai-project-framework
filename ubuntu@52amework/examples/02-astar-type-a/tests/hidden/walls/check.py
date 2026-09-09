#!/usr/bin/env python3
"""Checker: python3 check.py in.json out.json actual.json  -> exit 0 on pass.
Validates the path is legal, starts/ends correctly, its momentum cost equals the
expected optimal cost, and the reported cost equals that cost."""
import json
import sys


def momentum_cost(path):
    cost, prev, run = 0, None, 0
    for a, b in zip(path, path[1:]):
        d = (b[0] - a[0], b[1] - a[1])
        run = run + 1 if d == prev else 1
        cost += 0 if run % 4 == 0 else 1
        prev = d
    return cost


def main():
    inp = json.load(open(sys.argv[1]))
    exp = json.load(open(sys.argv[2]))
    act = json.load(open(sys.argv[3]))
    grid, start, goal = inp["grid"], inp["start"], inp["goal"]
    R, C = len(grid), len(grid[0])
    if exp["cost"] is None:
        ok = act.get("cost") is None and act.get("path") == []
        print("unreachable" if ok else f"expected unreachable, got {act}")
        return 0 if ok else 1
    path = act.get("path")
    if not isinstance(path, list) or not path:
        print("no path"); return 1
    if list(path[0]) != list(start) or list(path[-1]) != list(goal):
        print("path does not start at start / end at goal"); return 1
    for cell in path:
        if not (isinstance(cell, list) and len(cell) == 2 and all(isinstance(x, int) for x in cell)):
            print(f"bad cell {cell}"); return 1
        r, c = cell
        if not (0 <= r < R and 0 <= c < C) or grid[r][c] == "#":
            print(f"illegal cell {cell}"); return 1
    for a, b in zip(path, path[1:]):
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
            print(f"non-adjacent step {a}->{b}"); return 1
    pc = momentum_cost(path)
    if pc != exp["cost"]:
        print(f"path cost {pc} != optimal {exp['cost']}"); return 1
    if act.get("cost") != pc:
        print(f"reported cost {act.get('cost')} != path cost {pc}"); return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
