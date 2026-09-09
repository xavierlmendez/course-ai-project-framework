# Example 03: Bencode-L encoder (Type B, research-pointer variant)

## What this example showcases

- **The research-pointer variant** (framework §15, options menu). The published resource does not restate the base format. It points to external documentation (BitTorrent BEP 3 bencoding) and states only the twist. The student's specification has to get the harness to read *both*.
- **The snapshot rule.** External pages change and the grading sandbox only reaches allowlisted hosts. The professor snapshots the external page into `resource/snapshot-bep_0003.md` (fetched 2026-09-08, source URL and date at the top) and the resource links the snapshot. **Grade against the snapshot**: keep `www.bittorrent.org` *off* the sandbox allowlist so every regeneration reads the same text. Students may read the live page during development; the handout says the snapshot is authoritative.
- A data-representation domain, to show the framework is content-agnostic.

## I/O design

Input `{"value": V}` where V is any JSON value without floats. Output `{"hex": H}`, H the lowercase hex of the Bencode-L bytes. Hex output keeps the contract pure JSON while testing a binary format byte-for-byte.

## The twist (Bencode-L = BEP 3 with three changes)

1. String length prefixes are lowercase **hexadecimal** (UTF-8 byte count).
2. Dictionary keys are ordered by **UTF-8 byte length, then bytewise** (BEP 3: bytewise only).
3. `true`/`false`/`null` encode as `t`/`f`/`n` (BEP 3 has no encoding for them).

Why it passes the twist checklist: not documented anywhere as a format; fits in half a page with a worked example; breaks the canonical solution on identifiable input classes (strings ≥ 10 bytes, dicts with unequal key lengths, any boolean or null); requires understanding what "length" and "sorted as raw strings" mean in the base spec; testable by exact hex match; the public tests touch rules 1 and 3 with one case each and never show a dict where rule 2 changes the order.

## Categories and weights

| Category | Cases | Weight | Notes |
|---|---|---|---|
| basic_scalars | 8 | 1 | includes non-ASCII strings |
| lists | 6 | 1 | |
| dicts | 6 | 1 | key orders where BEP 3 and Bencode-L agree |
| twist_length_prefix | 8 | 1 (twist) | 10, 16, 255, 256 bytes; multibyte |
| twist_key_order | 7 | 1 (twist) | |
| twist_bool_null | 8 | 1 (twist) | |
| grad_deep_nesting | 5 | 1, grad only | 400-deep lists, 300-deep dicts, 5,000-item lists |

Twist weights 3 = half of the 6 non-graduate weights.

## Verification (2026-09-08, `tools/run_tests.py`, this machine)

Reference solution vs hidden suite:

```
basic_scalars 8/8  lists 6/6  dicts 6/6  twist_length_prefix 8/8  twist_key_order 7/7  twist_bool_null 8/8  grad_deep_nesting 5/5
```

Reference vs public: 6/6. Canonical BEP 3 solution (twist ignored, booleans as integers) vs hidden suite:

```
basic_scalars 7/8  lists 6/6  dicts 6/6  twist_length_prefix 0/8  twist_key_order 2/7  twist_bool_null 0/8  grad_deep_nesting 4/5
```

The twist is load-bearing: the canonical solution keeps most of the base points and loses 21 of 23 twist cases.

`tools/prescan.py submissions --allow host.docker.internal localhost www.bittorrent.org` → `OK GHI111222 words=200`. The reference specification also scans `OK`. `tools/runner.py --dry-run` prints the six sandbox commands (three regenerations, three hidden-test runs) with slot models `ref-bencode-b-slot1..3` and run tags `grading-k1..3`.

**Not verified here:** an actual regeneration. OpenCode and `qwen3:14b` are not installed on this machine. Run the calibration checklist before release.

## Files

```
project.json                  categories, weights, timeouts, model
seeds.secret.json             three seeds; gitignored; secret until grades are out
resource/index.md             the published resource ({{NONCE}}, {{BASE_URL}} substituted by ledger_server.py)
resource/snapshot-bep_0003.md the external page, snapshotted
tests/make_tests.py           regenerates public/ and hidden/ from the reference solution (professor only)
tests/public/, tests/hidden/  exact-match cases by category
reference/SPEC.md             reference specification (582 words), the calibration gate and appeals key
reference/solution/solve.py   professor's encoder
canonical/solve.py            plain BEP 3, twist ignored
handout.md                    filled Type B handout
submissions/GHI111222/        a plausible student submission (SPEC.md, PROCESS.md, WRITTEN.md)
```

## How to run

```
cd examples/03-serialization-type-b-research
python3 ../../tools/ledger_server.py --resource resource --ledger ledger.tsv --nonce <NONCE> --port 8080 \
        --base-url http://host.docker.internal:8080
python3 ../../tools/runner.py --project project.json --create-slots
python3 ../../tools/prescan.py submissions --allow host.docker.internal localhost www.bittorrent.org
python3 ../../tools/runner.py --project project.json --submissions submissions --out runs
python3 ../../tools/grade.py --project project.json --runs runs > gradebook.csv
```

Note on the pre-scan: it flags the word `curl`. The resource page shows a `curl` command, but a specification only needs to say "do what the ledger section says"; a specification that pastes the command will be flagged for a close read, which is the intended behaviour.
