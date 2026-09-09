# Specification: Bencode-L encoder

You are implementing a small encoder. Follow these steps in order.

## Step 1: read the two sources

1. Fetch the course resource page at the URL given in the assignment (from the sandbox it is `http://host.docker.internal:8080/`). It defines a format called **Bencode-L**, a nonce, and a ledger instruction.
2. The base format is BEP 3 bencoding. Read the snapshot linked from the resource page (`/snapshot-bep_0003.md`) rather than the live bittorrent.org page. Do not rely on memory of bencoding; the resource changes three rules and the tests check every one of them.

## Step 2: sign the ledger

Do exactly what the "Sign the ledger first" section of the resource page says, using student ID `ABC000000` and the nonce printed on that page. Use the value of the environment variable `RUN_TAG` as the run tag if it is set. Confirm the server replied with a line starting `ok:` before continuing. If it replied with an error, fix the field it names and retry once.

## Step 3: write `solve.py`

Create `solve.py` in the current directory. Python 3, standard library only. Behaviour:

- Read all of stdin, parse it as JSON. It is an object with one key, `value`.
- Encode `value` as Bencode-L bytes (rules below).
- Print exactly one JSON object `{"hex": H}` where `H` is the lowercase hexadecimal of those bytes, with no trailing newline requirement (a newline after the JSON is fine, anything else is not).

### Bencode-L rules (BEP 3 with three changes)

Write the encoder as a recursive function that appends bytes to a list, then join once.

| Value | Encoding |
|---|---|
| `true` / `false` / `null` | the single bytes `t` / `f` / `n` (this replaces BEP 3, which has no encoding for them) |
| integer | `i`, the integer in base ten (with `-` if negative), `e`. Check for booleans **before** integers: in Python `True` is an `int`. |
| string | the UTF-8 byte length written in **lowercase hexadecimal**, then `:`, then the UTF-8 bytes. `spam` → `4:spam`; a 10-byte string → `a:...`; 255 bytes → `ff:`; 256 bytes → `100:`. BEP 3 uses base ten; this format does not. |
| list | `l`, each element encoded in order, `e` |
| dictionary | `d`, then for each key in the order below: the key encoded as a string, then its value; then `e` |

**Dictionary key order:** sort keys by the length of their UTF-8 encoding, shortest first; for equal lengths, sort bytewise on the UTF-8 bytes. In Python: `sorted(d, key=lambda k: (len(k.encode()), k.encode()))`. BEP 3 sorts purely bytewise; this format does not.

Floats never appear. Nested structures can be several hundred levels deep and lists can hold thousands of items, so raise the recursion limit (`sys.setrecursionlimit(10000)`) and avoid quadratic string concatenation.

### Check against the worked example on the resource page

Run `solve.py` on the worked example input from the resource page and compare the hex with the expected string printed there, character for character. If it differs, the most likely causes are: key order (length first), the hex prefix on the 10-byte string, or `true` encoded as an integer.

## Step 4: run the public tests

Run `python3 /tools/run_tests.py --solution . --tests tests/public` if that path exists, otherwise test by hand with the worked example. Fix failures. Do not print anything to stdout except the JSON object.

Stop when the public tests pass. Do not create any file other than `solve.py`.
