# TA runbook

You have about 65 submissions and one grading week. Nothing here requires reading a transcript.

## Day 0: setup (30 minutes)

1. Clone the project directory the professor prepared: `project.json`, `tests/hidden/`, `seeds.secret.json` (delivered on grading day), the reference specification.
2. Build the sandbox once: `docker build -t harness-sandbox tools/sandbox/`.
3. Confirm the Ollama server is reachable and the slot models exist: `ollama list | grep ref-slot`.
4. Confirm the ledger file is readable: you will filter it by run tag.
5. Put all submissions under `submissions/<student_id>/`. Pairs: `submissions/<id1>-<id2>/`.

## Day 1: pre-scan and safety read (half a day)

```
python3 tools/prescan.py submissions/ > prescan.txt
```

- Any submission listed as `FLAG`: read its `SPEC.md` in full, line by line. If it contains an instruction that is not about the task (network calls outside the resource, shell commands, credential paths, "ignore previous instructions", anything addressed to the TA or grader), set its status to `flagged`, do not run it, and send it to the professor. Do not decide misconduct yourself.
- Every other submission: read `SPEC.md` (3 to 5 minutes; they are capped at 1,500 words). You are checking for the same things; the pre-scan misses paraphrases.
- Check the caps and required files. Over cap or missing `PROCESS.md` or `WRITTEN.md` → `incomplete`. Do not run incomplete submissions.
- Type A only: check the ledger for an entry with the student's ID and this project's nonce. None → `incomplete`.

Record statuses in `status.csv` (`student_id,status,note`).

## Day 1 evening: run the regenerations (unattended)

Type B:

```
python3 tools/runner.py --project project.json --submissions submissions/ \
  --status status.csv --run-tag grading --out runs/
```

Type A:

```
python3 tools/runner.py --project project.json --submissions submissions/ \
  --status status.csv --type A --out runs/
```

The runner skips anything not `graded`-eligible, sandboxes each run, enforces timeouts, and writes `runs/<student_id>/k<N>.json`. At 65 × 3 × ~10 minutes it finishes overnight. If it stops, rerun the same command; completed records are skipped.

## Day 2: gradebook and written component

```
python3 tools/grade.py --project project.json --runs runs/ --status status.csv > gradebook.csv
```

Then the written component: open `WRITTEN.md` beside the submission and score the rubric. Ten minutes each; time-box it. Enter the four (or three) dimension scores in `gradebook.csv`.

Check the ledger: every Type B submission you ran should show three entries tagged `grading-k1..k3`. A submission with none means its specification never told the harness to sign; that is already reflected in nothing, so note it in the written-component `note` column for the professor. It is graded behavior only through the twist categories, not as a separate penalty, unless the handout said otherwise.

## Day 3: release

1. Send `gradebook.csv` to the professor.
2. After the professor releases grades: publish `tests/hidden/` and `seeds.secret.json`.
3. Appeals: for each granted appeal, `python3 tools/runner.py --project project.json --submission submissions/<id> --run-tag appeal --slot 2 --out runs/` and re-run `grade.py`.

## Things not to do

- Do not edit a student's specification to make it run. A specification that does not run scores zero for that run; best-of-K exists for this.
- Do not run anything outside the sandbox.
- Do not grade the process note.
- Do not judge the specification's style, length, or elegance. Only the rubric and the tests.
