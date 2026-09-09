# TA runbook

You have about 65 submissions and one grading week. Every command below runs as written.
Nothing here requires reading a harness transcript.

Replace `{{PROJECT}}` with the project directory the professor gave you.

**Single-part or multi-part.** If `{{PROJECT}}` contains `parts.json`, the project is
multi-part: each `part-*/` directory is graded on its own and the results are combined once.
Commands below are marked **[per part]** or **[course]**. Everything student-facing is
course-level: one `status.csv`, one `written.csv`, one `milestone.csv`, one ledger, one
resource page, one nonce, and one gradebook.

Write the part names to a file, **one per line**, and read that file wherever this runbook
loops over parts. A file, not a variable: `bash` and `zsh` split a variable differently, and
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

**1. Get the project.** Clone or copy the professor's project directory. It contains
`project.json`, `tests/hidden/`, the reference specification, and the filled handout. It
does **not** contain `seeds.secret.json`; that arrives on grading day.

**2. Build the sandbox image.**

```
docker build -t harness-sandbox tools/sandbox/
```

The image pins the harness version. Do not rebuild it with a different pin mid-cohort: the
temperature schedule depends on that version.

**3. Start the model server and confirm the model is present.** [course] Type A projects have
no model and no seeds; skip to step 4.

```
MODEL=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["base_model"])' \
        {{PROJECT}}/project.json)      # multi-part: use {{PROJECT}}/part-I-opening/project.json
echo "model: $MODEL"
ollama list | grep -F "$MODEL" || echo "NOT PRESENT — run: ollama pull $MODEL"
```

Pull it now if it is missing. It is several gigabytes, and `--create-slots` on Day 1 will
otherwise download it silently in the middle of your grading window.

**4. Serve the published resource, and leave it running.** [course] The harness fetches it
during every regeneration, so it must be up for the whole batch. One server for the whole
project, including every part. In its own terminal:

```
python3 tools/ledger_server.py --project {{PROJECT}}/project.json \
  --port 8080 --base-url http://host.docker.internal:8080
```

For a multi-part project pass any part's `project.json`; every part shares the resource
directory, the ledger and the nonce.

**Check it is actually serving before you go any further**, because a 404 here fails the
whole cohort for a reason that is yours, not theirs:

```
curl -sf http://localhost:8080/ | head -3 || echo "NOT SERVING — check resource_dir in project.json"
```

The sandbox reaches it at `host.docker.internal:8080`, which is what `resource_host` and
`resource_port` in `project.json` must name. Grading two projects at once needs two ports
and matching `resource_port` values.

**5. Lay out the submissions.**

```
{{PROJECT}}/submissions/<student_id>/                 individual        [single-part]
{{PROJECT}}/submissions/<id1>-<id2>/                  a pair            [single-part]
{{PROJECT}}/part-I-opening/submissions/<student_id>/          the same names    [multi-part, per part]
```

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

**6. Type A only: the variant roster.** A Type A project whose `project.json` has a
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
invented ids; neither ships with the samples.

---

## Day 1 morning — Triage and the safety read (about half a day)

**1. Pre-scan.** The project supplies the allowed hosts, so a conforming specification that
contains the mandatory ledger line is not flagged.

```
python3 tools/prescan.py {{PROJECT}}/submissions/ --project {{PROJECT}}/project.json
```

**2. Read every specification.** They are capped at 1,500 words, so this is three to five
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

**3. The caps and the required files are checked by the pre-scan in step 1.** It reports
`missing:WRITTEN.md` for an absent page and `WRITTEN.md:over-page-cap:900` for one over the
600-word limit, alongside `words=` for the specification against its 1,500-word cap. Set any
submission it reports to `incomplete`. Nothing here is counted by hand.

**4. Type A only: the ledger gate.** Confirm each student has an entry.

**Find the ledger; do not assume `{{PROJECT}}/ledger.tsv`.** It is whatever the resource
server printed at start-up on the `ledger -> ...` line of Day 0 step 4, which is the `ledger`
key of the `project.json` you passed to the server, resolved **relative to that file**. In a
multi-part project the parts usually set `"ledger": "../ledger.tsv"`, so the one course ledger
sits beside `parts.json` and not inside the part you served. Derive it rather than typing it:

```
# use the same project.json you gave the server in Day 0 step 4
LEDGER=$(python3 -c 'import json,os,sys
p=sys.argv[1]
print(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(p)),
      json.load(open(p)).get("ledger","ledger.tsv"))))' {{PROJECT}}/project.json)
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

**5. Write `status.csv`.** This is the file that decides what runs.

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

**2. Create the slot models.** They cannot exist before this point, because they are built
from the seeds.

```
python3 tools/runner.py --project {{PROJECT}}/project.json --create-slots
```

This builds one model per slot from the base model. If the base model is not present it will
be downloaded first, several gigabytes, which is why step 3 of Day 0 exists.

**3. Confirm the schedule reaches the model.**

```
python3 tools/runner.py --project {{PROJECT}}/project.json --verify-slots
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

**4. Run the batch.**

```
python3 tools/runner.py --project {{PROJECT}}/project.json \
  --submissions {{PROJECT}}/submissions/ \
  --status {{PROJECT}}/status.csv \
  --out {{PROJECT}}/runs/
```

Type A adds `--type A`; it runs the hidden tests once per submission and takes minutes, not
hours. Multi-part runs this once per part, with that part's `project.json`, `submissions/`
and `runs/`.

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
# slots still to retry, across every part. Prints 0 and succeeds when there are none.
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
python3 tools/milestone.py check \
  --project {{PROJECT}}/project.json \
  --records {{PROJECT}}/milestone-records/ \
  --status {{PROJECT}}/status.csv > {{PROJECT}}/milestone.csv
```

**2. The written component.** [course] One page per student, scored once. In a multi-part
project the student writes one `WRITTEN.md`; if the professor asked for one per part, score
the part the handout names and say so to the professor.

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

**3. Produce the gradebook.** One command, single-part or multi-part:

```
python3 tools/grade_all.py --project {{PROJECT}} \
  --status {{PROJECT}}/status.csv \
  --written {{PROJECT}}/written.csv \
  --milestone {{PROJECT}}/milestone.csv \
  > {{PROJECT}}/gradebook.csv
```

If `{{PROJECT}}` contains `parts.json` this grades each part on its own and combines them,
adding the milestone and written component once. Otherwise it grades the project directly.
There is no shell loop to get wrong, and a part that was never run stops the command with a
message rather than producing a gradebook with holes in it.

**4. Check before you send it.** A row's `note` says why it is not ready. A note reading
`N slot(s) never completed` means the student was graded on fewer runs than everyone else:
raise it rather than sending it. Every row should read `graded` with a total. A row marked
`incomplete` has a `note` saying what is missing. Fix the input and re-run; do not hand-edit
the gradebook, because the next run overwrites it.

```
# rows that are not ready to send: no total, or a note explaining why
python3 - {{PROJECT}}/gradebook.csv <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1], newline="")))
bad = [r for r in rows if r.get("status") != "graded" or not r.get("total")]
print(f"{len(rows) - len(bad)} of {len(rows)} ready to send")
for r in bad:
    print(f"  {r['student_id']}: {r.get('status')} {r.get('note','')}")
PY
```

---

## Day 3 — Release and appeals

1. Send `gradebook.csv` to the professor.
2. Submit the specifications (Type B) or solutions (Type A) to {{SIMILARITY_TOOL}} per the
   course's process; the professor handles anything it flags.
3. After the professor releases grades, publish `tests/hidden/` and `seeds.secret.json`.
4. **Appeals.** A student may request one additional run at the middle temperature, and only
   if they show their work passes the public suite on the reference harness.

**What counts as showing their work passes.** The student sends the milestone-record command's
output for the current state of their submission (`tools/milestone.py record`). If it says
`FAIL`, the precondition is not met and the appeal is refused; say so and point at the
public-suite line. If they have no record, that is also a refusal. You are not judging the
specification, only whether the stated precondition holds.

**Type B** (the specification is regenerated). An appeal is scoped to **one part**; name that
part's project, submissions and runs:

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
