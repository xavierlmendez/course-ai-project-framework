#!/usr/bin/env python3
"""Textbook weighted interval scheduling. Twist ignored (no cooldown, no class rule).
Exists to confirm the twist is load-bearing: this must score low on twist categories."""
import bisect
import json
import sys


def solve(data):
    jobs = data["jobs"]
    order = sorted(range(len(jobs)), key=lambda i: (jobs[i]["end"], jobs[i]["start"]))
    ends = [jobs[i]["end"] for i in order]
    n = len(order)
    best, take, prev = [0] * (n + 1), [False] * (n + 1), [0] * (n + 1)
    for k in range(1, n + 1):
        j = jobs[order[k - 1]]
        p = min(bisect.bisect_right(ends, j["start"]), k - 1)
        if j["weight"] + best[p] > best[k - 1]:
            best[k], take[k], prev[k] = j["weight"] + best[p], True, p
        else:
            best[k], take[k], prev[k] = best[k - 1], False, k - 1
    chosen, k = [], n
    while k > 0:
        if take[k]:
            chosen.append(jobs[order[k - 1]])
            k = prev[k]
        else:
            k -= 1
    chosen.sort(key=lambda j: j["start"])
    return {"total": best[n], "chosen": [j["id"] for j in chosen]}


if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
