# TA runbook

You have about 65 submissions and one grading week. Every command below runs as written.
Nothing here requires reading a harness transcript.

Replace `{{PROJECT}}` with the grading directory you make in Day 0 step 1 — a **copy** of the
professor's project, outside any git checkout.

Replace `{{PROJECT_JSON}}` with the project's `project.json`; for a multi-part project, the
first program's, e.g. `{{PROJECT}}/part-I-opening/project.json` — every program shares the
nonce, the resource and the ledger, so any of them will do and the first one is the habit.

**Single-part or multi-part.** If `{{PROJECT}}` contains `parts.json`, the project is
multi-part: each `part-*/` directory is graded on its own and the results are combined once.
Commands below are marked **[per part]** or **[course]**. Everything student-facing is
course-level: one `status.csv`, one `written.csv`, one `milestone.csv`, one ledger, one
resource page, one nonce, and one gradebook.

The two commands in this preamble are **[course]**. Write the part names to a file, **one per
line**, and read that file wherever this runbook loops over parts. A file, not a variable: `bash` and `zsh` split a variable differently, and
`for p in $PARTS` gives one part named `I II` under `zsh`.

```
python3 -c 'import json,sys
print("\n".join(p["name"] for p in json.load(open(sys.argv[1]))["parts"]))' \
  {{PROJECT}}/parts.json > parts.txt 2>/dev/null || : > parts.txt
cat parts.txt        # one name per line; empty file = single-part project
```

`parts.json` lists only the parts that were built and are to be graded. If it lists a part
with no `tests/hidden/`, stop and ask the professor: grading around a listed-but-unbuilt part
silently reweights the others. Check that now — this runs the same in `bash` and `zsh`:

```
while read -r p; do
  if [ -d "{{PROJECT}}/part-$p/tests/hidden" ]; then
    echo "part $p: tests/hidden ok"
  else
    echo "part $p: NO tests/hidden — stop and ask the professor"
  fi
done < parts.txt
```

---

## Day 0 — Setup (about 30 minutes)

**1. Get the project.** Make `{{PROJECT}}` a **copy** of the professor's project directory,
placed **outside any git checkout** — not the checkout itself, and not a directory inside one.
It contains `project.json`, `tests/hidden/`, the reference specification, and the filled
handout. It does **not** contain `seeds.secret.json`; that arrives on grading day.

```
cp -R <the professor's project> ~/grading/{{PROJECT}}      # ~/grading is not a git checkout
```

The grading directory holds the ledger, and ledger entries carry student IDs and client
addresses. `ledger_server.py` refuses to write a ledger inside a repository working tree for
that reason and stops with:

```
refusing to write the ledger inside a repository: <path>
  the working tree at <repo> contains a .git; ledger entries carry student IDs and
  client addresses, and one `git add .` would commit them. Point --ledger at a path
  outside any checkout (or pass --allow-in-repo if you accept the risk).
```

If you see that on grading day, you are grading inside a checkout: move the copy out rather
than reaching for the flag. `--allow-in-repo` exists for **rehearsals** on the shipped
examples, where the ledger is throwaway; never use it on a real cohort.

**2. Build the sandbox image.** [course] One image serves every part.

```
docker build -t harness-sandbox tools/sandbox/
```

The image pins the harness version. Do not rebuild it with a different pin mid-cohort: the
temperature schedule depends on that version.

**3. Start the model server and confirm the model is present.** [course] Type A projects have
no model and no seeds; skip to step 4.

```
MODEL=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["base_model"])' \
        {{PROJECT_JSON}})
echo "model: $MODEL"
ollama list | grep -F "$MODEL" || echo "NOT PRESENT — run: ollama pull $MODEL"
```

Pull it now if it is missing. It is several gigabytes, and `--create-slots` on Day 1 will
otherwise download it silently in the middle of your grading window.

The model must be one that emits structured tool calls through the harness (`framework.md` §5,
criterion 6); that is checked once at calibration, not on grading day. If a whole batch comes back
with `entry_present: false` and empty working directories, suspect the model or the provider
timeouts before you suspect the specifications, and stop the batch.

**4. Serve the published resource, and leave it running.** [course] The harness fetches it
during every regeneration, so it must be up for the whole batch. One server for the whole
project, including every part. In its own terminal:

**The port is not yours to pick.** Every project fixes it in `project.json` as
`resource_port` (example 04 uses 8083). The student handouts and specifications hard-code the
URL that names it, and the sandbox allowlist is built from the same key, so a server on some
other port serves a page nobody fetches. Read it, then start the server in the `--project`
form, which takes the port from the project:

```
PORT=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("resource_port",8080))' \
       {{PROJECT_JSON}})
echo "resource_port: $PORT"

python3 tools/ledger_server.py --project {{PROJECT_JSON}} \
  --base-url http://host.docker.internal:$PORT
```

For a multi-part project pass any part's `project.json` (`{{PROJECT_JSON}}` is the first
program's); every part shares the resource directory, the ledger and the nonce.

If the port is busy the server exits with one sentence rather than a traceback:

```
port N is already in use: another resource server is probably still running (stop it, or
pass --port to use another port)
```

Almost always that is your own server from an earlier attempt. Stop it; do not move the port,
because the students' URL does not move with you.

**Two projects graded at the same time need two different `resource_port` values**, and the
professor chooses them **before release** — the port is baked into the handout and the
resource URL students were given, so it cannot be changed at grading time.

**Check it is actually serving before you go any further**, because a 404 here fails the
whole cohort for a reason that is yours, not theirs:

```
curl -sf http://localhost:$PORT/ | head -3 || echo "NOT SERVING — check resource_dir in project.json"
```

The sandbox reaches it at `host.docker.internal:$PORT`, which is what `resource_host` and
`resource_port` in `project.json` name.

**5. Lay out the submissions.** [course] Everything students hand in goes under **one**
course-level `{{PROJECT}}/submissions/` directory, in the layout the handout asked for:

```
{{PROJECT}}/submissions/<student_id>/                 individual        [single-part]
{{PROJECT}}/submissions/<id1>-<id2>/                  a pair            [single-part]

{{PROJECT}}/submissions/<student_id>/                 multi-part: the student layout
    part-I-opening/SPEC.md                            one directory per program
    part-I-game/SPEC.md
    …
    WRITTEN.md                                        one page for the whole project
    PROCESS.md                                        one page for the whole project
```

The runner works per program, from `{{PROJECT}}/part-<program>/submissions/<id>/`. You do not
build those directories by hand: `tools/fan_out.py` (Day 1 step 1) copies each program's
`SPEC.md` into its part directory and copies the one course-level `WRITTEN.md` and `PROCESS.md`
into every one of them.

The directory name is the key for `status.csv`, `written.csv`, `milestone.csv`, the variant
roster and the gradebook, and it is the same in every part. A pair is one directory and one
row everywhere: both ids, hyphen, alphabetical.

A pair's id is written three ways: `<id1>-<id2>` as a directory, `<id1>+<id2>` in the ledger,
`<id1>,<id2>` in a variant roster. Where a **tool** compares two ids it splits both on `+`,
`,` and `-` and accepts them as the same submission when they share **any** member, so you do
not have to normalise them:

- `milestone.py check` matches a record to its `status.csv` row on any shared member, so a
  pair's record may name either partner or the pair in any form.
- `runner.py` matches a submission directory to its row in the variant roster the same way.
- The specification's ledger line may name either partner; `prescan.py` accepts any member
  and reports `spec-id-mismatch` only when the submission names some *other* student's id.

Two places are **not** tool comparisons and need the single-id form yourself: grepping the
ledger (step 4 below — grep one partner, never the hyphenated key) and the keys you type into
`status.csv`, `written.csv` and `milestone.csv`, which must equal the directory name exactly.
`grade.py` and `combine_parts.py` join those files on the literal key.

**6. Type A only: the variant roster.** [course] A Type A project whose `project.json` has a
`variants` key generates its hidden tests per student, and `variants.csv` — the file named by
`variants.roster`, default `variants.csv`, beside `project.json` — says which variant each
submission gets. **The professor supplies it**; there is no other copy, and the runner marks
anyone missing from it `SKIPPED` rather than guessing. It is two columns:

```
student_id,variant
JKL333444,JKL333444
ABC123456,ABC123456
MNO777888+PQR999000,MNO777888
```

The roster decides, not the submission: a `variant.txt` inside a submission is written by the
student and is ignored. A pair takes one row and one variant, in any of the pair forms. If you
are **rehearsing** rather than grading, write the file yourself — one row per submission
directory, the variant usually being the student id — since the professor's roster only exists
for a real cohort.

**Rehearsing with the shipped samples.** The example submissions under `examples/` are the way
to practise this runbook before grading day, but they are one student's work: their
specifications carry the student id `ABC123456` (or the example's own id) in the ledger line,
and `examples/04`'s sample deliberately fails one public test. So when you copy a sample under
an invented id, **change that id inside the copy too** — the pre-scan compares the id in the
submission against the directory name and reports `spec-id-mismatch` otherwise — and expect
`milestone 0` for a copy of the `examples/04` sample, which is a candor example and is
supposed to fail `twist_class`. Add a `variants.csv` and a `status.csv` of your own for the
invented ids; neither ships with the samples. A rehearsal is the one place `--allow-in-repo` is
appropriate: the example ledgers sit inside this checkout and are throwaway.

Six more things a rehearsal needs, each of which cost a cold run:

- **Remove the shipped sample after copying it.** `submissions/ABC123456/` ships with the
  example. Copy it to your invented ids and then `rm -rf` the original, or it stays an extra
  row in every pre-scan, gradebook and readiness count.
- **The ledger gate will report zero entries**, because nobody signed a ledger you started
  five minutes ago. Sign it yourself, once per invented id, against the server from Day 0
  step 4 (the nonce is the `nonce` key of `{{PROJECT_JSON}}`; the run tag must be lowercase
  letters, digits, `-` or `_`, and the gate greps for `grading-k<N>`):

  ```
  curl -s -X POST http://localhost:$PORT/ledger \
    -d student_id=<XXXNNNNNN> -d nonce=<nonce from project.json> -d run_tag=grading-k1
  ```

  The accepted fields are exactly `student_id` (one ID, or two comma-separated, each three
  upper-case letters and six digits), `nonce`, `run_tag` (optional, default `practice`) and
  `variant` (optional) — add `-d variant=<variant>` on a variant project. The server replies
  `ok` or a 400 with a plain reason.
- **Copy the professor's `variants.csv` aside before writing your own.** An example ships one;
  overwrite it and you have lost the roster the example's own tests were built against.
- **`grade_all.py` writes `gb-<program>.csv` files** into the project directory as it goes —
  one per part — or into `--work <dir>` if you give one. They are intermediate files, not the
  gradebook; the gradebook is what the command prints on stdout.
- **`milestone.py record --student-id` accepts a pair in any form**: `A+B`, `A-B`, `A,B`, or
  just one partner. You do not have to guess which one the sample used.
- **Expect `milestone 0` for a copy of the `examples/04` sample** — see above; it is a candor
  example and is supposed to fail `twist_class`.

---

## Day 1 morning — Triage and the safety read (about half a day)

**1. Fan the submissions out to the parts.** [course] Multi-part submissions arrive in the
**student layout** of Day 0 step 5: `submissions/<id>/<program>/SPEC.md` for each program, plus
one `WRITTEN.md` and one `PROCESS.md` at the top of the student's directory. The runner reads
per-program directories instead, so fan them out first:

```
python3 tools/fan_out.py --project {{PROJECT}} --submissions {{PROJECT}}/submissions
```

It writes `{{PROJECT}}/part-<program>/submissions/<id>/` for every program in `parts.json`,
copying that program's `SPEC.md` and a copy of the one course-level `WRITTEN.md` and
`PROCESS.md` into each. It prints one row per student — which programs are present, which are
missing, and the word count of each `SPEC.md` — and exits 1 with a named reason for any layout
problem (a program directory that is not in `parts.json`, a missing `SPEC.md`, two `WRITTEN.md`
files, a stray file where a program directory was expected). `--check` validates and prints the
same rows without writing anything, which is the safe thing to run while submissions are still
arriving.

A single-part project has nothing to fan out; skip to step 2.

**2. Pre-scan, course level.** [course] One row per student, over the layout the student
actually submitted:

```
python3 tools/prescan.py --course {{PROJECT}}
```

This is where `PROCESS.md` and `WRITTEN.md` are checked, because both are course-level — one of
each per student for the whole project, scored once (see Day 2 step 2).

**3. Pre-scan, per program.** [per part] The project supplies the allowed hosts, so a
conforming specification that contains the mandatory ledger line is not flagged.

Single-part:

```
python3 tools/prescan.py {{PROJECT}}/submissions/ --project {{PROJECT}}/project.json
```

**A multi-part project has no `project.json` and no `submissions/` at its top level** — both live in
each part directory — so run it once per part, over the submissions the fan-out wrote and with that
part's project:

```
while read -r p; do
  echo "== part $p"
  python3 tools/prescan.py "{{PROJECT}}/part-$p/submissions/" --project "{{PROJECT}}/part-$p/project.json"
done < parts.txt
```

The per-program pre-scan looks for `PROCESS.md` and `WRITTEN.md` inside **every** submission
directory it is given; the fan-out has already put a copy of each into every part, so those rows
are clean, and you still score the course-level pages once.

**4. Read every specification.** [course] They are capped at 1,500 words, so this is three to five
minutes each. You are looking for instructions that are not about the task: shell commands,
network calls to anywhere but the resource, attempts to read `/tests`, credential paths, or
text addressed to you as the grader. The pre-scan misses paraphrases, which is why you read
them all.

Also check the **student ID inside the specification** matches the submission directory. The
pre-scan does this for you and reports `spec-id-mismatch:<id>`. **A pair's specification may
name either member** — whoever signs the ledger — so either id is correct for a
`<id1>-<id2>` directory, and a specification that names no id at all is not reported. A
specification that tells the harness to sign the ledger as somebody *else* is either a copied
template or an attempt to sign for another student; either way it is a `flagged`, not a
correction you make yourself.

The pre-scan reports three outcomes, and they mean different things:

| Outcome | Meaning | Status you set |
|---|---|---|
| `OK` | Nothing to act on | `graded`, after your read |
| `INCOMPLETE` | A required page is missing or over its cap | `incomplete` |
| `FLAG` | Content a human must judge: shell commands, offsite URLs, attempts to read the tests, text addressed to you | `flagged` |

Anything marked `FLAG`: read it line by line, set its status to `flagged`, do not run it, and
send it to the professor. **You do not decide misconduct.**

**5. The caps and the required files are checked by the pre-scans in steps 2 and 3.** It reports
`missing:WRITTEN.md` for an absent page and `WRITTEN.md:over-page-cap:900` for one over the
600-word limit, alongside `words=` for the specification against its 1,500-word cap. Set any
submission it reports to `incomplete`. Nothing here is counted by hand.

**6. Type A only: the ledger gate.** [course] Confirm each student has an entry.

**Find the ledger; do not assume `{{PROJECT}}/ledger.tsv`.** It is whatever the resource
server printed at start-up on the `ledger -> ...` line of Day 0 step 4, which is the `ledger`
key of the `project.json` you passed to the server, resolved **relative to that file**. In a
multi-part project the parts usually set `"ledger": "../ledger.tsv"`, so the one course ledger
sits beside `parts.json` and not inside the part you served. Derive it rather than typing it:

```
# {{PROJECT_JSON}} is the same project.json you gave the server in Day 0 step 4
LEDGER=$(python3 -c 'import json,os,sys
p=sys.argv[1]
print(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(p)),
      json.load(open(p)).get("ledger","ledger.tsv"))))' {{PROJECT_JSON}})
echo "$LEDGER"     # must equal the path the server printed after `ledger ->`
```

That file is the one the resource server has been appending to since the project was
published. **Starting the server in Day 0 step 4 creates the file**, so "the file exists"
proves nothing. What matters is whether it has entries:

```
grep -vc '^#' "$LEDGER"    # entries, ignoring the two header lines
```

If that is 0, or far below the cohort size, the students never signed it: do not fail
everyone. Stop and ask the professor whether the server was running during the project. If
you started a fresh server on a fresh file, ask for the term's ledger before applying the
gate.

```
# one student, or one partner of a pair
cut -f2 "$LEDGER" | grep -c "ABC123456"

# every submission at once: prints the ones with no entry
for d in {{PROJECT}}/submissions/*/; do
  sid=$(basename "$d"); first=${sid%%-*}
  cut -f2 "$LEDGER" | grep -q "$first" || echo "NO LEDGER ENTRY: $sid"
done
```

Match a **single student id**, never the hyphenated pair key: the ledger joins a pair with
`+`, so grepping `ABC123456-DEF654321` finds nothing and would mark every pair incomplete.

Ledger entries carry the student ID, a timestamp, a run tag and the client address. They do
**not** carry the nonce, so do not try to match one. The nonce is what the resource page
required in order to write the entry at all.

**7. Write `status.csv`.** [course] This is the file that decides what runs.

```
student_id,status,grad,note
ABC123456,graded,0,
BBB222222,graded,1,
CCC333333,flagged,0,pre-scan: shell command in spec
DDD444444-EEE555555,graded,0,pair
```

- `status` is `graded` for every clean submission. **The runner only runs rows marked
  `graded` or `appeal`.** A submission with no row does not run.
- `grad` is `1` for graduate students and `0` otherwise. **It comes from the professor's
  course roster, and there is no roster file anywhere in the project directory** — nothing
  the tools can read tells you who is a graduate student, so ask the professor for the list
  and type it in. The tools refuse to run without this column, because defaulting it would
  grade every graduate on the undergraduate bar. (Rehearsing: pick the values yourself.)
- `incomplete` for a missing file, an exceeded cap, or (Type A) a missing ledger entry.

---

## Day 1 evening — The batch (unattended)

**Type A projects skip steps 1 to 3 entirely.** There is no regeneration, so there are no
seeds and no slot models. Go to step 4 and add `--type A`.

**1. Get the seeds from the professor** [per part] and put `seeds.secret.json` in each part
directory. Do not paste them into chat, a ticket, or a commit.

**2. Create the slot models.** [per part] They cannot exist before this point, because they
are built from the seeds.

```
python3 tools/runner.py --project {{PROJECT_JSON}} --create-slots
```

This builds one model per slot from the base model. If the base model is not present it will
be downloaded first, several gigabytes, which is why step 3 of Day 0 exists.

**3. Confirm the schedule reaches the model.** [per part]

```
python3 tools/runner.py --project {{PROJECT_JSON}} --verify-slots
```

This must print `slot check: ok`. It asks the model server what temperature and seed each
slot model actually has, and fails if they do not match the schedule the handout promises or
do not differ from one another.

If it reports it could not reach the model server, the project's `ollama_host` is written for
the sandbox and the check runs on your machine. It translates a container-only name to
loopback automatically; if your model server is somewhere else, set `ollama_host_local` in
`project.json` to the URL **you** can reach, and tell the professor so it ships that way.

If it reports a temperature mismatch, re-run `--create-slots`. If that does not fix it, stop
and tell the professor: grading with a schedule the model is not using would be unfair.

**4. Run the batch.** [per part]

```
python3 tools/runner.py --project {{PROJECT_JSON}} \
  --submissions {{PROJECT}}/submissions/ \
  --status {{PROJECT}}/status.csv \
  --out {{PROJECT}}/runs/
```

Type A adds `--type A`; it runs the hidden tests once per submission and takes minutes, not
hours. Multi-part runs this once per part, with that part's `project.json` and its
`part-<program>/submissions/` (written by the fan-out) and `part-<program>/runs/`.

**The records it writes**, once, so the names below are not a surprise: a grading run writes
`runs/<id>/k<N>.json` beside its working directory `runs/<id>/grading-k<N>-work`; a student's
practice run writes `practice-k<N>.json` beside `practice-k<N>-work`; any other run tag writes
`<tag>-k<N>.json` beside `<tag>-k<N>-work` (so an appeal is `appeal-k2.json`); and a `--dry-run`
writes `<tag>-k<N>.dry.json` beside `<tag>-k<N>-dry-work`, which the grading tools skip.

**Read the last lines.** The runner prints a `SKIPPED` summary and exits non-zero if nobody
was graded. A skipped submission is almost always a `status.csv` key that does not match the
directory name, or a student missing from the variant roster.

**How long it takes.** Measure, do not guess. The professor's calibration run recorded the
wall-clock time of one regeneration; the batch is roughly that × 3 × the number of
submissions you are running, on one machine. Ask the professor for the number and plan the
window before you start. If a regeneration takes 10 minutes, 65 submissions is about 32
machine-hours, which is more than one night.

**If it stops with `BATCH ABORTED`.** Three regenerations failed in a row for environment
reasons: the model server is down, docker is broken, or the disk is full. Nothing was scored
against those students. Fix the machine and re-run the **same command**; completed slots are
skipped and incomplete ones are retried.

**The retry pass.** Isolated environment failures leave a slot incomplete and the batch
carries on. When the batch finishes, re-run the same command once. Anything still incomplete
after that is a real problem to raise, not a grade.

```
# [course] slots still to retry, across every part. Prints 0 and succeeds when there are none.
find {{PROJECT}} -name '*.json' -path '*/runs/*' -exec grep -l '"complete": false' {} + 2>/dev/null | wc -l
```

---

## Day 2 — The gradebook

**1. The milestone.** [course] Students submitted milestone records during the project.
Collect them into one directory, one `.json` per student, then validate them. For a
multi-part project pass the part the handout told students to produce their record against
(`part-I-opening/project.json` unless the handout says otherwise): a record names the part it was
made for, and `check` only accepts records for the part you name.

```
# single-part: {{PROJECT}}/project.json
# multi-part:  the part the handout named, e.g. {{PROJECT}}/part-I-opening/project.json
python3 tools/milestone.py check \
  --project {{PROJECT}}/project.json \
  --records {{PROJECT}}/milestone-records/ \
  --status {{PROJECT}}/status.csv > {{PROJECT}}/milestone.csv
```

**2. The written component.** [course] One page per student, scored once. In a multi-part
project the student submits **one** `WRITTEN.md` and one `PROCESS.md` at the top of their
submission directory (`submissions/<id>/`), as the shipped sample does; the fan-out copies both
into every program directory so the per-program pre-scan finds them, but there is still only
one of each and you score the course-level one once. If the professor instead asked for one per
part, score the part the handout names and say so to the professor.

Score with `templates/rubric.md`, which gives a mechanical decision rule per band. Ten
minutes each; time-box it.

**Graduate rows need the hidden results first.** The prediction dimension compares what the
student predicted would fail against what did. So for a cohort with graduate students: run
step 3 once without `--written` to get the hidden scores, score the pages, then run step 3
again with `--written`. Undergraduate-only cohorts can score in any order.

Record the dimension scores, not a total:

```
student_id,accuracy,twist,candor,prediction
ABC123456,3,2,3,
BBB222222,3,3,2,1
```

Leave `prediction` empty for undergraduates. Values outside 0–3 are rejected by the tools.

**3. Produce the gradebook.** [course] One command, single-part or multi-part:

```
python3 tools/grade_all.py --project {{PROJECT}} \
  --submissions {{PROJECT}}/submissions \
  --status {{PROJECT}}/status.csv \
  --written {{PROJECT}}/written.csv \
  --milestone {{PROJECT}}/milestone.csv \
  > {{PROJECT}}/gradebook.csv
```

If `{{PROJECT}}` contains `parts.json` this grades each part on its own and combines them,
adding the milestone and written component once. Otherwise it grades the project directly.
There is no shell loop to get wrong, and a part that was never run stops the command with a
message rather than producing a gradebook with holes in it.

`--submissions` names the course-level submissions directory of Day 0 step 5, and
`grade_all.py` runs the fan-out itself before grading, so the per-program directories are
always current with what the students handed in. Leave it out on a single-part project.
It also writes one intermediate gradebook per program, `gb-<program>.csv`, into the project
directory — or into `--work <dir>` if you give one. The gradebook is what it prints on stdout.

**4. Check before you send it.** [course] A row's `note` says why it is not ready. A note reading
`N slot(s) never completed` means the student was graded on fewer runs than everyone else:
raise it rather than sending it. Every row should read `graded` with a total. A row marked
`incomplete` has a `note` saying what is missing. Fix the input and re-run; do not hand-edit
the gradebook, because the next run overwrites it.

A total is not enough on its own: a row can read `graded` with a total and still carry
`1 slot(s) never completed` or a `missing:` note. The check below flags those too and prints
the note, because an earlier cold run read "3 of 3 ready to send" over exactly such a row.

```
# rows that are not ready to send: no total, or a note that says something is wrong
python3 - {{PROJECT}}/gradebook.csv <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1], newline="")))


def not_ready(r):
    note = (r.get("note") or "").lower()
    return (r.get("status") != "graded" or not r.get("total")
            or "never completed" in note or "missing:" in note)


bad = [r for r in rows if not_ready(r)]
print(f"{len(rows) - len(bad)} of {len(rows)} ready to send")
for r in bad:
    print(f"  {r['student_id']}: {r.get('status')} "
          f"total={r.get('total') or '-'} note={r.get('note','') or '-'}")
PY
```

---

## Day 3 — Release and appeals

1. Send `gradebook.csv` to the professor.
2. Submit the specifications (Type B) or solutions (Type A) to {{SIMILARITY_TOOL}} per the
   course's process; the professor handles anything it flags.
3. After the professor releases grades, publish `tests/hidden/` and `seeds.secret.json`.
4. **Appeals.** There are two kinds, and only one of them has a milestone precondition.

**Type B — a re-run appeal.** A student may request one additional run at the middle
temperature, and only if they show their work passes the public suite on the reference
harness. **What counts as showing their work passes:** the student sends the milestone-record
command's output for the current state of their submission (`tools/milestone.py record`). If
it says `FAIL`, the precondition is not met and the appeal is refused; say so and point at the
public-suite line. If they have no record, that is also a refusal. You are not judging the
specification, only whether the stated precondition holds.

**Type A — no milestone precondition at all.** A Type A appeal is not a re-run (see below),
so nothing about the public suite gates it. A student disputing the hidden tests, a status
that was mis-scored, or a written score is entitled to that hearing whether or not their code
passes the public suite — and on a project like `examples/04`, whose sample deliberately fails
one public test, requiring a passing milestone would refuse every appeal automatically. Do not
apply the paragraph above to a Type A appeal.

**Type B** (the specification is regenerated). An appeal is scoped to **one part** [per part];
name that part's project, submissions and runs:

```
# set that student's status to `appeal` in status.csv, then, for the part under appeal:
python3 tools/runner.py --project {{PROJECT}}/part-II-opening/project.json \
  --submission {{PROJECT}}/part-II-opening/submissions/ABC123456 \
  --run-tag appeal --slot 2 \
  --out {{PROJECT}}/part-II-opening/runs/
```

Single-part projects drop the `part-II-opening/` segments. Re-run `grade_all.py` afterwards; it
re-grades every part, so an appeal on one part does not disturb the others.

The appeal writes its own record (`appeal-k2.json`) alongside the grading records, so it
neither overwrites the original nor is skipped as already done. Re-run `grade.py`, which
considers every complete record and takes the best.

**Type A** grading is deterministic: the same code against the same tests gives the same
result, so re-running changes nothing. An appeal on a Type A project means one of three
things, and none of them is a re-run: the student says the hidden tests are wrong (a question
for the professor), the submission was mis-scored because a required file was missing (fix
`status.csv` and re-grade), or the written score is disputed (a second reader). If you do
want a fresh record for the file, `--run-tag appeal` writes `appeal-a.json` beside `a.json`.

Set the status back to `graded` when the appeal is resolved.

---

## Things not to do

- Do not edit a student's specification to make it run. A specification that does not work
  scores what it scores; best-of-K exists for the rest.
- Do not run a student's code outside the sandbox. `--no-sandbox` is for students practising
  on their own machines. The one exception is `milestone.py check`, which only reads and
  validates JSON records and never executes anything a student wrote.
- Do not grade the process note.
- Do not judge a specification's style, length or elegance. Only the rubric and the tests.
- Do not hand-edit the gradebook. Fix the input and re-run.
- Do not share the seeds before grades are released.

## When to stop and ask the professor

- `--verify-slots` fails after re-creating the slots.
- The batch aborts twice for the same reason.
- A specification contains something addressed to you, or anything you would not want to run.
- A student's grade turns on a judgement the rubric does not cover.
