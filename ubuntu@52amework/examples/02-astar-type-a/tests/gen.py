#!/usr/bin/env python3
"""Generate public and hidden tests for example 02 using the reference solution.
Run from the example directory: python3 tests/gen.py"""
import json, os, random, shutil, sys
from collections import deque
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reference", "solution"))
from solve import solve as momentum_solve

HERE = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(20260908)


def bfs_steps(grid, start, goal):
    R, C = len(grid), len(grid[0])
    q, seen = deque([tuple(start)]), {tuple(start): 0}
    while q:
        r, c = q.popleft()
        if [r, c] == list(goal):
            return seen[(r, c)]
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] != "#" and (nr, nc) not in seen:
                seen[(nr, nc)] = seen[(r, c)] + 1
                q.append((nr, nc))
    return None


def rand_grid(R, C, wall_p):
    return ["".join("#" if rng.random() < wall_p else "." for _ in range(C)) for _ in range(R)]


def rand_open(grid):
    R, C = len(grid), len(grid[0])
    while True:
        r, c = rng.randrange(R), rng.randrange(C)
        if grid[r][c] == ".":
            return [r, c]


def case(grid, start, goal):
    cost, _ = momentum_solve(grid, start, goal)
    return {"grid": grid, "start": start, "goal": goal}, {"cost": cost}


def gen_basic(n):  # <=4x4, no walls: no run of 4 is possible, so canonical is exact
    out = []
    while len(out) < n:
        R, C = rng.randint(2, 4), rng.randint(2, 4)
        g = rand_grid(R, C, 0.0)
        s, t = rand_open(g), rand_open(g)
        if s != t:
            out.append(case(g, s, t))
    return out


def gen_walls(n):  # <=4x4 with walls, reachable
    out = []
    while len(out) < n:
        R, C = 4, 4
        g = rand_grid(R, C, 0.3)
        s, t = rand_open(g), rand_open(g)
        if s != t and bfs_steps(g, s, t) is not None and bfs_steps(g, s, t) >= 3:
            out.append(case(g, s, t))
    return out


def gen_unreachable(n):
    out = []
    while len(out) < n:
        R, C = rng.randint(3, 7), rng.randint(3, 7)
        g = rand_grid(R, C, 0.35)
        s, t = rand_open(g), rand_open(g)
        if s != t and bfs_steps(g, s, t) is None:
            out.append(case(g, s, t))
    return out


def gen_long_run(n):  # optimal path contains a run >= 4, so cost < steps
    out = []
    while len(out) < n:
        R, C = rng.randint(5, 9), rng.randint(5, 9)
        g = rand_grid(R, C, 0.15)
        s, t = rand_open(g), rand_open(g)
        steps = bfs_steps(g, s, t)
        if steps is None or s == t:
            continue
        cost, _ = momentum_solve(g, s, t)
        if cost < steps:
            out.append(case(g, s, t))
    return out


def dist_to(grid, goal):
    R, C = len(grid), len(grid[0])
    q, d = deque([tuple(goal)]), {tuple(goal): 0}
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] != "#" and (nr, nc) not in d:
                d[(nr, nc)] = d[(r, c)] + 1
                q.append((nr, nc))
    return d


def min_cost_among_shortest(grid, start, goal, steps):
    """Minimum momentum cost over all paths that are shortest in steps."""
    dist = dist_to(grid, goal)
    layer = {(start[0], start[1], -1, 0): 0}
    for k in range(steps):
        nxt = {}
        for (r, c, d, run), cost in layer.items():
            for di, (dr, dc) in enumerate(((-1,0),(1,0),(0,-1),(0,1))):
                nr, nc = r+dr, c+dc
                if dist.get((nr, nc)) != steps - k - 1:
                    continue
                nrun = run + 1 if di == d else 1
                st = (nr, nc, di, nrun % 4)
                nc_ = cost + (0 if nrun % 4 == 0 else 1)
                if nc_ < nxt.get(st, 1e9):
                    nxt[st] = nc_
        layer = nxt
    return min(layer.values())


def gen_detour(n):  # every shortest-in-steps path costs strictly more than the optimum
    out = []
    tries = 0
    while len(out) < n and tries < 400000:
        tries += 1
        R, C = rng.randint(5, 9), rng.randint(6, 10)
        g = rand_grid(R, C, 0.25)
        s, t = rand_open(g), rand_open(g)
        steps = bfs_steps(g, s, t)
        if steps is None or s == t:
            continue
        cost, path = momentum_solve(g, s, t)
        if min_cost_among_shortest(g, s, t, steps) > cost:
            out.append(case(g, s, t))
    return out


def gen_large(n):
    out = []
    while len(out) < n:
        R, C = 150, 150
        g = rand_grid(R, C, 0.28)
        s, t = [0, 0], [R - 1, C - 1]
        g[0] = "." + g[0][1:]
        g[-1] = g[-1][:-1] + "."
        if bfs_steps(g, s, t) is not None:
            out.append(case(g, s, t))
    return out


def write(root, cat, cases, start_idx=1):
    d = os.path.join(root, cat)
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(HERE, "check.py"), os.path.join(d, "check.py"))
    for i, (inp, exp) in enumerate(cases, start_idx):
        json.dump(inp, open(os.path.join(d, f"{i:03d}.in.json"), "w"))
        json.dump(exp, open(os.path.join(d, f"{i:03d}.out.json"), "w"))


def main():
    hidden = os.path.join(HERE, "hidden")
    public = os.path.join(HERE, "public")
    for d in (hidden, public):
        if os.path.exists(d):
            shutil.rmtree(d)
    write(hidden, "basic", gen_basic(6))
    write(hidden, "walls", gen_walls(6))
    write(hidden, "unreachable", gen_unreachable(4))
    write(hidden, "twist_long_run", gen_long_run(8))
    write(hidden, "twist_detour", gen_detour(6))
    write(hidden, "grad_large", gen_large(4))
    # public sample: hand-picked shapes
    write(public, "basic", [case(["....", "....", "...."], [0, 0], [2, 3])] + gen_basic(1))
    write(public, "walls", gen_walls(1))
    write(public, "unreachable", gen_unreachable(1))
    write(public, "twist_long_run", [case(["......", "......"], [0, 0], [0, 5])])
    print("done")


if __name__ == "__main__":
    main()
