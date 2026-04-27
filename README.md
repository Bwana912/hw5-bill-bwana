# Homework 5 — meeting-notes-to-actions

[![CI](https://github.com/Bwana912/hw5-bill-bwana/actions/workflows/ci.yml/badge.svg)](https://github.com/Bwana912/hw5-bill-bwana/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Course:** BU 330.760 — AI for Business  
**Submission:** hw5-bwana  
**Video:** [Insert video link here]

---

## What this skill does

`meeting-notes-to-actions` is a reusable agent skill that parses plain-text meeting notes and produces a validated, structured table of action items. For each detected task, it extracts the description, assignee, and due date, normalizes the date into ISO 8601 format, and flags calendar problems deterministically: past dates, weekend due dates, and suspiciously far-future deadlines.

The skill ships with a Python script (`parse_actions.py`) that handles all date logic. A language model is orchestrating the workflow and formatting the response, but the script is the part that reliably determines whether April 30 is a Saturday, whether a date has already passed, and whether a raw string like "May 9, 2026" or "09/15/2026" resolves to the same calendar day. Prose alone cannot do that consistently across different input formats.

---

## Why I chose this skill

Meeting notes are one of the most common types of unstructured professional text, and turning them into action items is a recurring, high-friction workflow that knowledge workers do by hand. The task has a natural split: a model reads the prose well but fails at date arithmetic; code handles date arithmetic deterministically but needs the model to make sense of free-form language.

This meant the Python script would be genuinely load-bearing rather than decorative. The script does not dress up the output; it does the part of the job that code uniquely handles: parsing mixed date formats, checking weekend status, computing days ahead, and emitting consistent ISO dates. That made the skill a strong fit for the assignment's core requirement.

---

## How to use it

### Prerequisites
- Python 3.10 or later (standard library only — no `pip install` required)

### Run the script directly

```bash
# Normal usage (Markdown table)
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py notes.txt

# CSV output — import directly into Excel or Google Sheets
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py notes.txt --format csv

# With JSON output
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py notes.txt --output actions.json

# Override today's date (useful for testing)
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py notes.txt --today 2026-04-26

# Strict mode: exit code 1 if any warnings present (useful in CI)
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py notes.txt --strict

# Run the automated test suite
python run_tests.py
```

### Invoke via agent

When the skill is registered under `.agents/skills/meeting-notes-to-actions/`, an agent will discover it through the `name` and `description` fields in `SKILL.md`. Any prompt that asks to "extract action items," "parse these meeting notes," "pull out the to-dos," or "create an action table" should activate the skill.

The agent saves the pasted notes to a temporary file, runs the script, and presents the resulting Markdown table with a plain-English summary of any warnings.

### Recognized action item markers (case-insensitive)
- `Action:` / `Action item:` / `TODO:` / `Task:` at the start of a line
- `[ ]` (Markdown unchecked checkbox)

### Recognized date formats
`YYYY-MM-DD`, `MM/DD/YYYY`, `MM-DD-YYYY`, `Month DD YYYY`, `Month DD, YYYY`, `DD Month YYYY`  
Preceded by `Due:`, `Due date:`, `By:`, or `Deadline:`, or as a bare date on the line.

---

## Folder structure

```
hw5-bill-bwana/
├─ .github/
│  └─ workflows/
│     └─ ci.yml                        # GitHub Actions CI (Python 3.10, 3.11, 3.12)
├─ .agents/
│  └─ skills/
│     └─ meeting-notes-to-actions/
│        ├─ SKILL.md                   # Agent-facing skill definition and instructions
│        ├─ scripts/
│        │  └─ parse_actions.py        # Load-bearing deterministic Python script
│        └─ references/
│           └─ REFERENCES.md           # Design rationale and library pointers
├─ docs/
│  ├─ agent-transcript.md              # Full Claude Code session transcript (3 scenarios)
│  └─ design.md                        # Architecture and model-vs-code design decisions
├─ sample_inputs/
│  ├─ sample_normal.txt                # Normal test case
│  ├─ sample_edge.txt                  # Edge case: past dates, weekends, bad formats
│  └─ sample_cautious.txt             # Cautious case: no action items present
├─ sample-outputs/
│  ├─ normal-case-output.md            # Actual terminal output — normal case
│  ├─ edge-case-output.md             # Actual terminal output — edge case
│  └─ cautious-case-output.md         # Actual terminal output — cautious case
├─ run_tests.py                        # Deterministic PASS/FAIL test runner (5 cases)
├─ CHANGELOG.md                        # Version history
├─ CONTRIBUTING.md                     # How to extend the skill
├─ LICENSE                             # MIT
└─ README.md
```

---

## What the script does

`parse_actions.py` is a single-file, dependency-free Python script (~300 lines) that does the following in sequence:

1. **Reads** the notes file and splits it into lines.
2. **Detects** action item lines by matching trigger patterns (`Action:`, `TODO:`, `[ ]`, etc.) at the start of a line. Multi-line continuation (indented lines) is accumulated into a single item.
3. **Extracts the assignee** using `@mention` syntax or labeled patterns like `Owner: Name` or `Assigned to: Name`, stopping before due-date keywords to avoid over-capture.
4. **Extracts the raw due date** by matching `Due:`, `By:`, or `Deadline:` prefixes, then falling back to any bare date-shaped token on the line.
5. **Parses the date** in two stages: first checks for relative expressions (`next Monday`, `next Friday`, `tomorrow`, `next week`, `end of week`, `end of month`) and resolves them against today's date using `timedelta` math; then tries a prioritized list of absolute format patterns (`YYYY-MM-DD`, `MM/DD/YYYY`, etc.) via `strptime`. No external libraries.
6. **Validates the date** against three rules: not in the past, not on a Saturday or Sunday, and not more than 180 days ahead.
7. **Outputs** a Markdown table (default) or CSV (`--format csv`) to stdout and, if `--output` is passed, writes a structured JSON file.

The script uses only Python's standard library (`argparse`, `csv`, `json`, `re`, `sys`, `datetime`).

---

## Test prompts and expected behavior

### Prompt 1 — Normal case
> "Here are my notes from today's Q2 planning kickoff. Can you pull out all the action items and show me a table with the owner and due date for each one?"
> *(Paste: `sample_inputs/sample_normal.txt`)*

**Expected behavior:** The agent invokes the skill, runs the script, and returns a clean Markdown table with 6 items. Four items pass all checks (✓). Two items are flagged because their due dates fall on a Saturday (May 2 and May 9, 2026). The agent notes the weekend warnings and asks the user to confirm or shift those dates.

---

### Prompt 2 — Edge case
> "These are notes from our incident retrospective. Several of the action items have issues. Can you extract them and validate the due dates?"
> *(Paste: `sample_inputs/sample_edge.txt`)*

**Expected behavior:** The script finds 6 items, none of which pass cleanly. Warnings include: two past dates, two weekend dates (one item has both), one unparseable natural-language date ("next quarter"), and one far-future date (249 days ahead). The agent presents the table with all warnings visible and asks the user to resolve each one rather than guessing at corrections.

---

### Prompt 3 — Cautious / no-action-items case
> "Can you extract the action items from these all-hands notes?"
> *(Paste: `sample_inputs/sample_cautious.txt`)*

**Expected behavior:** The script finds zero action items (the text contains no recognized trigger patterns). The agent reports that no action items were detected in the notes and explains what markers the skill looks for (`Action:`, `TODO:`, `[ ]`, etc.). It does not invent tasks from the prose. It suggests the user re-share notes that include explicit action item markers, or manually identify the tasks they want tracked.

---

## What worked well

- **The parsing pipeline held up across mixed formats.** The prioritized regex approach correctly handled ISO dates, slash-delimited dates, and spelled-out month formats without any external library.
- **Validation produces genuinely useful flags.** The Saturday/Sunday check caught real scheduling problems in the sample data that a model alone would have silently accepted.
- **Zero dependencies keeps the skill portable.** Any environment with Python 3.10 can run the script without a setup step, which is important for a skill meant to be reused by others.
- **The three-test-case structure revealed real edge behavior**, not just happy-path output. The edge case made me fix the greedy/non-greedy comma issue in date capture mid-build.

---

## Limitations that remain

- **Relative date expressions are supported without any library.** `next Monday`, `next Friday`, `tomorrow`, `next week`, `end of week`, and `end of month` are resolved deterministically against today's date using only `datetime` math. Inputs like "end of quarter" or "ASAP" are still flagged as unparseable.
- **English-only month names.** The month expansion step handles English only. Notes written with French, Spanish, or other month names will fail to parse dates.
- **No inference on missing fields.** If an assignee or due date is absent, the script reports it and stops. It does not attempt to infer ownership from conversational context in the notes.
- **No task-tracker integration.** The skill outputs a Markdown table and optional JSON. Pushing items to Asana, Jira, or Linear is out of scope and would require a separate integration layer.
- **Multi-line action items require indentation.** Continuation lines must begin with four spaces or a tab. Arbitrarily wrapped prose is not handled.

---

## AI-use acknowledgement

I acknowledge the use of AI tools to support editing, idea evaluation, organization, clarity, and alignment of my work with the assignment requirements. The skill concept, implementation decisions, testing approach, and final submitted work remain my responsibility. AI assistance was used as a drafting and review aid, not as a substitute for my own analysis, judgment, or understanding.

---

## Materials consulted

- Homework 5 assignment instructions (BU 330.760, Spring 2026, Canvas)
- Week 5 Module materials on agent systems, prompts, skills, tools/scripts, progressive disclosure, and workflow architecture
- Python standard library documentation: `datetime`, `re`, `argparse`, `json`, `sys` (https://docs.python.org/3/)
- Sample input files created for this submission (`sample_normal.txt`, `sample_edge.txt`, `sample_cautious.txt`)

No external datasets, third-party Python packages, or other public sources were used.
