# Written component

**Design decision.** I sort jobs by end time and keep `best[i]` = optimum over the first i jobs. For job i, I binary-search the last job whose end is at most `start - g`, which is the standard weighted-interval DP with the compatibility boundary shifted by g. This keeps the solution O(n log n), which matters because inputs reach 3,000 jobs.

**What handles the twist.** The line `p = bisect.bisect_right(ends, j["start"] - g, 0, i - 1)` is the entire twist: subtracting g from the start moves the compatibility boundary. g itself comes from `gap()` which implements the formula on the resource page; for my variant it is 3.

**Limitation.** My solution treats every job as class S. I ran out of time to handle the priority exemption, so on inputs where a P job could start immediately after the previous job my schedule is feasible but not optimal. I expect twist_class to fail.
