#!/usr/bin/env python3
"""Reference solution: weighted interval scheduling with the variant cooldown twist.

Input  {"variant": "...", "jobs": [{"id", "start", "end", "weight", "class"}, ...]}
Output {"total": int, "chosen": [ids in start order]}

Rules (from the published resource):
  g = 1 + (sum of character codes of the variant) mod 4
  consecutive chosen jobs (prev, next) need  next.start >= prev.end + sep(next)
  sep(next) = 0 if next.class == "P" else g
"""
import bisect
import json
import sys


def gap_of(variant):
    return 1 + sum(ord(c) for c in variant) % 4


def solve(data):
    jobs = data["jobs"]
    g = gap_of(data.get("variant", ""))
    order = sorted(range(len(jobs)), key=lambda i: (jobs[i]["end"], jobs[i]["start"]))
    ends = [jobs[i]["end"] for i in order]
    n = len(order)
    best = [0] * (n + 1)          # best[k]: optimum using the first k jobs in end order
    take = [False] * (n + 1)
    prev = [0] * (n + 1)
    for k in range(1, n + 1):
        j = jobs[order[k - 1]]
        sep = 0 if j.get("class") == "P" else g
        p = min(bisect.bisect_right(ends, j["start"] - sep), k - 1)
        with_j = j["weight"] + best[p]
        if with_j > best[k - 1]:
            best[k], take[k], prev[k] = with_j, True, p
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
