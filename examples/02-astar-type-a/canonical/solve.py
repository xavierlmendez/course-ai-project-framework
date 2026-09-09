#!/usr/bin/env python3
"""Canonical textbook A*: 4-neighbour grid, unit step cost, Manhattan heuristic.
Ignores the published resource entirely. Expected to score low on twist categories."""
import heapq
import json
import sys


def solve(grid, start, goal):
    R, C = len(grid), len(grid[0])
    sr, sc = start
    gr, gc = goal
    if grid[sr][sc] == "#" or grid[gr][gc] == "#":
        return None, []
    h = lambda r, c: abs(r - gr) + abs(c - gc)
    best = {(sr, sc): 0}
    parent = {(sr, sc): None}
    pq = [(h(sr, sc), 0, (sr, sc))]
    while pq:
        f, g, (r, c) = heapq.heappop(pq)
        if best[(r, c)] < g:
            continue
        if (r, c) == (gr, gc):
            path, s = [], (r, c)
            while s is not None:
                path.append(list(s))
                s = parent[s]
            return g, path[::-1]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] != "#" and g + 1 < best.get((nr, nc), 1e18):
                best[(nr, nc)] = g + 1
                parent[(nr, nc)] = (r, c)
                heapq.heappush(pq, (g + 1 + h(nr, nc), g + 1, (nr, nc)))
    return None, []


def main():
    d = json.load(sys.stdin)
    cost, path = solve(d["grid"], d["start"], d["goal"])
    json.dump({"cost": cost, "path": path}, sys.stdout)


if __name__ == "__main__":
    main()
