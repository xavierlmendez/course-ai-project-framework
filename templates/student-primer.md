# Working with an AI harness: a primer for this project

*Read this before the milestone. It explains what the tool the course grades with actually does, how to run it yourself, what the grading run looks like, and where to read more. Commands and configuration below were checked against the vendor documentation on 8 September 2026; links are given so you can re-check.*

## 1. Chatbot, model, harness: three different things

- A **model** is the network that turns text into text. `qwen2.5-coder:14b` is a model. On its own it cannot read a file, run a program, or fetch a web page.
- A **chatbot** (the ChatGPT or Claude web page) is a model behind a text box. You paste, it answers, you paste again. Everything that touches your files goes through your hands.
- A **harness** is a program that runs a model in a loop with **tools**: it lets the model read and write files in a directory, run shell commands, and fetch URLs, and it feeds the results back to the model until the model says it is done. OpenCode is a harness. Claude Code, Gemini CLI, Codex CLI and Aider are harnesses.

This project is graded by a harness, not a chatbot. That matters because the harness is what fetches the published resource, signs the ledger, writes the program, and runs it. Your specification is instructions to the harness, and the harness decides which tools to use to follow them.

## 2. What the reference harness is

The course grades with **OpenCode** running the **`qwen2.5-coder:14b`** model through **Ollama** on a machine the TAs control. Three consequences:

1. **It is free and local.** Ollama runs the model on your own laptop, or on the shared course server. No account, no card.
2. **It is small.** A 14-billion-parameter model is far weaker than the frontier chat models you may have used. It follows precise instructions well and guesses badly. A specification that works on a frontier model and fails here has left something unsaid.
3. **It is pinned.** The TAs run your specification three times, at temperatures 0.2, 0.6 and 1.0, each with a fixed seed that is published after grades. Your best run counts. Nothing about the model changes between your practice runs and the grading run except the seed.

Develop with whatever you like. The grade comes only from this setup, so anything that only works elsewhere is wasted effort.

## 3. Install and run it yourself

### Ollama and the model

Install Ollama for your platform from https://ollama.com/download (Linux: `curl -fsSL https://ollama.com/install.sh | sh`; macOS: open the `.dmg`; Windows: the installer). Then:

```
ollama pull qwen2.5-coder:14b      # about 9 GB on disk
ollama run qwen2.5-coder:14b       # a quick chat to confirm it works; /bye to exit
```

If your machine cannot run the 14B model (it needs roughly 9 GB of free memory), use the course server. Set the address of that server before running OpenCode:

```
export OLLAMA_HOST=http://<course-server>:11434
```

Model tags and sizes: https://ollama.com/library/qwen2.5-coder. CLI reference: https://docs.ollama.com/cli.

### OpenCode

Install with one of (https://opencode.ai/docs):

```
curl -fsSL https://opencode.ai/install | bash
npm install -g opencode-ai
brew install anomalyco/tap/opencode
```

Check with `opencode --version`. In the directory holding your work, create `opencode.json` so OpenCode talks to Ollama (shape verbatim from https://opencode.ai/docs/providers, model changed to ours):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (local)",
      "options": { "baseURL": "http://localhost:11434/v1" },
      "models": { "qwen2.5-coder:14b": { "name": "Qwen2.5 Coder 14B" } }
    }
  },
  "model": "ollama/qwen2.5-coder:14b",
  "share": "disabled"
}
```

`"share": "disabled"` matters: OpenCode's `/share` command uploads a session to a public URL, and your specification and the course resource must not end up there (https://opencode.ai/docs/share).

### Two ways to run

**Interactive.** Run `opencode` in your project directory. You get a terminal UI; type a request, watch the tools it calls, ask for changes. Useful commands: `/models` to confirm the model, `/undo` to revert the last change, `/export` to save the conversation as Markdown, `/sessions` to reopen old ones (https://opencode.ai/docs/tui).

**Non-interactive.** This is how the TAs run you:

```
opencode run -m ollama/qwen2.5-coder:14b "Read SPEC.md in the current directory and carry out its instructions exactly. The finished program must be a file named solve.py in the current directory. Do not ask questions; make reasonable choices and finish."
```

That wrapper sentence is identical for every student. Everything else the harness knows about your task comes from `SPEC.md` and from what it fetches. Run the course runner for the full grading shape, including the tests:

```
python3 tools/runner.py --project project.json --submission <your dir> --run-tag practice --no-sandbox
```

### What the harness can do

OpenCode's built-in tools (https://opencode.ai/docs/tools): `read`, `write`, `edit`, `bash`, `glob`, `grep`, `webfetch`, `websearch`, and a few more. In the grading run, `bash`, `edit` and `webfetch` are allowed without prompting, and the network is limited to the published resource and the model server. Your specification can say "fetch this URL", "run this command", "create this file", and the harness will. It cannot reach anything else.

## 4. What the grading run looks like, step by step

1. A TA reads your `SPEC.md` (the safety read, a few minutes). It is capped at 1,500 words for this reason.
2. The runner copies your submission into a fresh sandbox with no secrets and network only to the resource page and the model.
3. OpenCode starts with the wrapper sentence above, at slot 1 (temperature 0.2, fixed seed). It reads `SPEC.md`, fetches the resource, signs the ledger with the run tag `grading-k1`, writes the program.
4. The hidden test suite runs against what it produced, in a container with no network.
5. Steps 3 and 4 repeat for slots 2 and 3. Your hidden-test score is the best of the three.
6. After grades are released you get the hidden tests and the seeds, and you can rerun the exact grading run at home.

A run that exceeds the time limit or produces a program that does not start scores zero for that slot only.

## 5. Writing a specification a small model can follow

These are the failure patterns observed when small models were asked to reproduce last year's programs from prompts (the full list is in the course repo). Every one is something the prompt left implicit.

| The model… | Because the specification… | Fix |
|---|---|---|
| invented its own board or graph constants | described them in prose | Put the exact tables in the spec and say "copy verbatim, do not recompute" |
| counted the wrong thing | said "count evaluations" | Say exactly when the counter increments |
| wrapped the code in Markdown fences | did not say the output was a file | Say "write the file; do not print code" |
| returned a bound instead of the value | named the algorithm and stopped | Spell out the return value and the comparison (`>=` not `>`) |
| got the sign or a multiplier wrong | wrote a formula in words | Write it as an expression |
| checked conditions in the wrong order | listed them unordered | Number them and say "in this order" |
| used `<` where `==` was meant | said "when down to three" | Write the comparison |
| wrote output to the wrong place | said "output the board" | Name the file, the argument index, the exact line format |

Three habits that follow:

- **State the interface contract in full**, even though the resource has it. The harness reads your spec first.
- **Give one worked example** with exact input and exact expected output. Small models anchor on examples.
- **Tell it to test.** "After writing solve.py, run the public tests with `python3 tools/run_tests.py ...` and fix failures until they pass." The harness can run commands; use that.

And the two lines every specification must contain: fetch the published resource at its URL, and sign the ledger with your student ID and the nonce from the page.

## 6. Temperature, seeds, and why "it worked for me" is not an appeal

Temperature scales how random the model's word choices are. At 0.2 the model is nearly repeatable; at 1.0 it wanders. A **seed** fixes the random draw so the same temperature gives the same output again. Ollama exposes both (https://docs.ollama.com/modelfile), and the course pins them per slot.

The grading run is reproducible: same model, seed, temperature and wrapper. If your specification passes at home on the same setup and fails in grading, the difference is the seed, and best-of-three exists to absorb that. If it passes on a frontier chat model and fails here, the difference is the model, and that is the thing the project measures.

## 7. What is and is not graded

Graded: what the reference harness produces from your specification, the written component, the milestone. Not graded: which tool you developed with, how many times you regenerated, whether you fetched the resource by hand, your process note, the harness's transcript.

## 8. Further reading

- **OpenCode documentation**, https://opencode.ai/docs. The harness: install, config, tools, permissions, rules files, sharing.
- **Ollama documentation**, https://docs.ollama.com. Running models locally, Modelfiles, the OpenAI-compatible endpoint, serving on a network.
- **AGENTS.md convention**, https://agents.md. The plain-Markdown instructions file harnesses read at startup; OpenCode's `/init` creates one.
- **Anthropic, "Building effective agents"**, https://www.anthropic.com/research/building-effective-agents. What a harness loop is and when a simpler workflow beats it.
- **Claude prompt engineering overview**, https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview. Define success criteria first, then technique.
- **OpenAI prompt engineering guide**, https://developers.openai.com/api/docs/guides/prompt-engineering. Structure, roles, examples.
- **Chen et al., "Evaluating Large Language Models Trained on Code"**, https://arxiv.org/abs/2107.03374. HumanEval and the pass@k metric, which is what best-of-K grading is.
- **Jimenez et al., "SWE-bench"**, https://arxiv.org/abs/2310.06770. How agent harnesses are evaluated on real repositories.
