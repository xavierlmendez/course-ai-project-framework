import bisect, json, sys

def gap(v):
    return 1 + sum(ord(c) for c in v) % 4

data = json.load(sys.stdin)
jobs = data["jobs"]
g = gap(data.get("variant", ""))
jobs.sort(key=lambda j: j["end"])
ends = [j["end"] for j in jobs]
n = len(jobs)
best = [0] * (n + 1)
pick = [None] * (n + 1)
for i in range(1, n + 1):
    j = jobs[i - 1]
    # cooldown: previous job must end at least g before this one starts
    p = bisect.bisect_right(ends, j["start"] - g, 0, i - 1)
    if best[p] + j["weight"] > best[i - 1]:
        best[i] = best[p] + j["weight"]
        pick[i] = p
    else:
        best[i] = best[i - 1]
chosen = []
i = n
while i > 0:
    if pick[i] is not None:
        chosen.append(jobs[i - 1])
        i = pick[i]
    else:
        i -= 1
chosen.sort(key=lambda j: j["start"])
print(json.dumps({"total": best[n], "chosen": [j["id"] for j in chosen]}))
