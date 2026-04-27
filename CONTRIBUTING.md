# Contributing

Thank you for your interest in `meeting-notes-to-actions`. Contributions that improve date
format coverage, assignee detection, or output options are welcome.

---

## Prerequisites

- Python 3.10 or later
- No `pip install` needed — the project uses only the standard library

---

## Running the tests

```bash
python run_tests.py
```

Expected output:

```
Running 3 test cases against .agents\skills\meeting-notes-to-actions\scripts\parse_actions.py

[PASS] normal case
[PASS] edge case
[PASS] cautious case (no action items)
[PASS] relative dates
[PASS] CSV output format

5/5 passed
```

All tests must pass before submitting a pull request.

---

## Project layout

```
hw5-bill-bwana/
├─ .agents/skills/meeting-notes-to-actions/
│  ├─ SKILL.md              # Agent-facing activation instructions
│  ├─ scripts/
│  │  └─ parse_actions.py   # All parsing, validation, and output logic
│  └─ references/
│     └─REFERENCES.md       # Design rationale and library pointers
├─ docs/
│  ├─ agent-transcript.md   # Real Claude Code session transcript
│  └─ design.md             # Architecture and design decisions
├─ sample_inputs/           # Three test cases (normal, edge, cautious)
├─ sample-outputs/          # Expected output committed for easy review
├─ run_tests.py             # Deterministic test runner
└─ README.md
```

---

## Extending the script

### Adding a new absolute date format

Add a `(regex_pattern, strptime_format)` tuple to `DATE_PATTERNS` in `parse_actions.py`.
Patterns are tried in order; place more specific patterns before more general ones.

```python
DATE_PATTERNS = [
    ...
    (r"\b(\d{1,2}\.\d{1,2}\.\d{4})\b", "%d.%m.%Y"),  # European: 30.04.2026
]
```

### Adding a new relative date expression

Add a `(regex, resolver)` tuple to `RELATIVE_PATTERNS`. The resolver receives `today`
as a `date` object and must return a `date` object.

```python
RELATIVE_PATTERNS.append(
    (r"\bnext\s+quarter\b", lambda t: date(t.year + (t.month > 9), (t.month + 2) % 12 + 1, 1))
)
```

### Adding a new assignee pattern

Add a compiled regex to `ASSIGNEE_PATTERNS`. The pattern must capture the assignee
name in group 1. Patterns are tried in order; stop-lookahead on `due|by|deadline`
prevents the date from being consumed as part of the name.

---

## Code style

- Standard library only — do not add `pip` dependencies
- Type annotations on all public functions
- No comments explaining *what* — only *why* when non-obvious
- Run `python run_tests.py` before committing

---

## Submitting changes

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes and ensure `python run_tests.py` passes
4. Open a pull request with a short description of what changed and why
