#!/usr/bin/env python3
"""Reference solution: A* over the augmented state (row, col, direction, run length).

Momentum rule (published resource): within a run of consecutive steps in the same
direction, every 4th step is free. Cost of a run of length L is L - L//4.
Heuristic h(d) = d - d//4 for Manhattan distance d is admissible: any path has
n >= d steps and at most n//4 free steps, and n - n//4 is nondecreasing in n.
"""
import heapq
import json
import sys

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def solve(grid, start, goal):
    R, C = len(grid), len(grid[0])
    sr, sc = start
    gr, gc = goal

    def open_cell(r, c):
        return 0 <= r < R and 0 <= c < C and grid[r][c] != "#"

    if not open_cell(sr, sc) or not open_cell(gr, gc):
        return None, []
    if (sr, sc) == (gr, gc):
        return 0, [[sr, sc]]

    def h(r, c):
        d = abs(r - gr) + abs(c - gc)
        return d - d // 4

    # state: (r, c, dir_index or -1, run % 4)  -- run kept modulo 4 since only k%4 matters
    start_state = (sr, sc, -1, 0)
    best = {start_state: 0}
    parent = {start_state: None}
    pq = [(h(sr, sc), 0, start_state)]
    while pq:
        f, g, s = heapq.heappop(pq)
        if best.get(s, float("inf")) < g:
            continue
        r, c, d, run = s
        if (r, c) == (gr, gc):
            path = []
            while s is not None:
                path.append([s[0], s[1]])
                s = parent[s]
            return g, path[::-1]
        for di, (dr, dc) in enumerate(DIRS):
            nr, nc = r + dr, c + dc
            if not open_cell(nr, nc):
                continue
            nrun = (run + 1) if di == d else 1
            step = 0 if nrun % 4 == 0 else 1
            ns = (nr, nc, di, nrun % 4)
            ng = g + step
            if ng < best.get(ns, float("inf")):
                best[ns] = ng
                parent[ns] = s
                heapq.heappush(pq, (ng + h(nr, nc), ng, ns))
    return None, []


def main():
    data = json.load(sys.stdin)
    cost, path = solve(data["grid"], data["start"], data["goal"])
    json.dump({"cost": cost, "path": path}, sys.stdout)


if __name__ == "__main__":
    main()
