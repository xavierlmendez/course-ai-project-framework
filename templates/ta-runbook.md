# TA runbook

You have about 65 submissions and one grading week. Every command below runs as written.
Nothing here requires reading a harness transcript.

Replace `{{PROJECT}}` with the project directory the professor gave you. For a multi-part
project, `{{PROJECT}}` has a `parts.json` and one `part-*/` directory per part; every
per-part command is run once per part.

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

**3. Start the model server and confirm the model is present.**

```
ollama list | grep -F "$(python3 -c 'import json;print(json.load(open("{{PROJECT}}/project.json"))["base_model"])')"
```

If it prints nothing, `ollama pull <the base_model named in project.json>`.

**4. Serve the published resource, and leave it running.** The harness fetches it during
every regeneration, so it must be up for the whole batch. In its own terminal:

```
python3 tools/ledger_server.py --project {{PROJECT}}/project.json \
  --port 8080 --base-url http://host.docker.internal:8080
```

The sandbox reaches it at `host.docker.internal:8080`, which is what `resource_host` and
`resource_port` in `project.json` must name. If the resource is not served, every
regeneration produces a specification-shaped failure and the whole cohort scores badly for
a reason that is yours, not theirs.

**5. Lay out the submissions.**

```
{{PROJECT}}/submissions/<student_id>/                 individual
{{PROJECT}}/submissions/<id1>-<id2>/                  a pair: both ids, hyphen, alphabetical
```

The directory name is the key for `status.csv`, `written.csv`, `milestone.csv` and the
gradebook. A pair is one directory and one row everywhere. (The ledger records a pair as
`<id1>+<id2>`; that is the ledger's own format and does not need to match.)

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

Anything the pre-scan marked `FLAG`: read it line by line, set its status to `flagged`, do
not run it, and send it to the professor. **You do not decide misconduct.**

**3. Check the caps and the required files.** Every submission needs the specification (or
the solution, for Type A), `PROCESS.md` and `WRITTEN.md`. `PROCESS.md` and `WRITTEN.md` are
capped at **600 words** each; the specification at 1,500 including any supporting files.

**4. Type A only: the ledger gate.** Confirm each student has an entry.

```
cut -f2 {{PROJECT}}/ledger.tsv | grep -c "^ABC123456"
```

Ledger entries carry the student ID, a timestamp, a run tag and the client address. They do
**not** carry the nonce, so do not try to match one. Any entry for that student counts; the
nonce is what the resource page required in order to write the entry in the first place.

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
- `grad` is `1` for graduate students and `0` otherwise. It comes from the professor's
  roster. The tools refuse to run without this column, because defaulting it would grade
  every graduate on the undergraduate bar.
- `incomplete` for a missing file, an exceeded cap, or (Type A) a missing ledger entry.

---

## Day 1 evening — The batch (unattended)

**1. Get the seeds from the professor** and put `seeds.secret.json` in the project directory.
Do not paste them into chat, a ticket, or a commit.

**2. Create the slot models.** They cannot exist before this point, because they are built
from the seeds.

```
python3 tools/runner.py --project {{PROJECT}}/project.json --create-slots
```

**3. Confirm the schedule reaches the model.**

```
python3 tools/runner.py --project {{PROJECT}}/project.json --verify-slots
```

This must print `slot check: ok`. If it does not, the temperatures the handout promises are
not the ones the model is using, and grading now would be unfair. Re-run `--create-slots`;
if it still fails, stop and tell the professor.

**4. Run the batch.**

```
python3 tools/runner.py --project {{PROJECT}}/project.json \
  --submissions {{PROJECT}}/submissions/ \
  --status {{PROJECT}}/status.csv \
  --out {{PROJECT}}/runs/
```

Type A adds `--type A`; it runs the hidden tests once per submission and takes minutes, not
hours.

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
grep -l '"complete": false' {{PROJECT}}/runs/*/*.json | wc -l   # slots still to retry
```

---

## Day 2 — The gradebook

**1. The milestone.** Students submitted milestone records during the project. Collect them
into one directory, one `.json` per student, then validate them:

```
python3 tools/milestone.py check \
  --project {{PROJECT}}/project.json \
  --records {{PROJECT}}/milestone-records/ \
  --status {{PROJECT}}/status.csv > {{PROJECT}}/milestone.csv
```

**2. The written component.** Open each `WRITTEN.md` beside its submission and score it with
`templates/rubric.md`, which gives a mechanical decision rule per band. Ten minutes each;
time-box it. Record the dimension scores, not a total:

```
student_id,accuracy,twist,candor,prediction
ABC123456,3,2,3,
BBB222222,3,3,2,1
```

Leave `prediction` empty for undergraduates. Values outside 0–3 are rejected by the tools.

**3. Produce the gradebook.** Single-part:

```
python3 tools/grade.py --project {{PROJECT}}/project.json \
  --runs {{PROJECT}}/runs/ --status {{PROJECT}}/status.csv \
  --written {{PROJECT}}/written.csv --milestone {{PROJECT}}/milestone.csv \
  > {{PROJECT}}/gradebook.csv
```

Multi-part: grade each part, then combine once. A part contributes only its hidden score;
the milestone and written component are course-level and counted once.

```
for P in I II III IV; do
  python3 tools/grade.py --project {{PROJECT}}/part-$P/project.json \
    --runs {{PROJECT}}/part-$P/runs/ --status {{PROJECT}}/status.csv \
    > {{PROJECT}}/gb-$P.csv
done

python3 tools/combine_parts.py --parts {{PROJECT}}/parts.json \
  --written {{PROJECT}}/written.csv --milestone {{PROJECT}}/milestone.csv \
  {{PROJECT}}/gb-I.csv {{PROJECT}}/gb-II.csv {{PROJECT}}/gb-III.csv {{PROJECT}}/gb-IV.csv \
  > {{PROJECT}}/gradebook.csv
```

**4. Check before you send it.** Every row should read `graded` with a total. A row marked
`incomplete` has a `note` saying what is missing. Fix the input and re-run; do not hand-edit
the gradebook, because the next run overwrites it.

```
awk -F, '$NF!="" || $(NF-1)=="incomplete"' {{PROJECT}}/gradebook.csv
```

---

## Day 3 — Release and appeals

1. Send `gradebook.csv` to the professor.
2. After the professor releases grades, publish `tests/hidden/` and `seeds.secret.json`.
3. **Appeals.** A student may request one additional run at the middle temperature, and only
   if they show their work passes the public suite on the reference harness.

```
# set that student's status to `appeal` in status.csv, then:
python3 tools/runner.py --project {{PROJECT}}/project.json \
  --submission {{PROJECT}}/submissions/ABC123456 \
  --run-tag appeal --slot 2 \
  --out {{PROJECT}}/runs/
```

The appeal writes its own record (`appeal-k2.json`) alongside the grading records, so it
neither overwrites the original nor is skipped as already done. Re-run `grade.py`, which
considers every complete record and takes the best. Set the status back to `graded` when the
appeal is resolved.

---

## Things not to do

- Do not edit a student's specification to make it run. A specification that does not work
  scores what it scores; best-of-K exists for the rest.
- Do not run anything outside the sandbox. `--no-sandbox` is for students practising on
  their own machines.
- Do not grade the process note.
- Do not judge a specification's style, length or elegance. Only the rubric and the tests.
- Do not hand-edit the gradebook. Fix the input and re-run.
- Do not share the seeds before grades are released.

## When to stop and ask the professor

- `--verify-slots` fails after re-creating the slots.
- The batch aborts twice for the same reason.
- A specification contains something addressed to you, or anything you would not want to run.
- A student's grade turns on a judgement the rubric does not cover.
