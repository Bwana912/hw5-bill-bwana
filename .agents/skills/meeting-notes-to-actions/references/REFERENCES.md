# References

## Assignment specification
- Homework 5 — Week 5: Build a Reusable AI Skill (BU 330.760, Spring 2026)
- agentskills.io skill creation quickstart: https://agentskills.io/skill-creation/quickstart

## Python standard library
- `datetime` — date, time, and timedelta: https://docs.python.org/3/library/datetime.html
- `re` — regular expression operations: https://docs.python.org/3/library/re.html
- `argparse` — command-line argument parsing: https://docs.python.org/3/library/argparse.html
- `json` — JSON encoder and decoder: https://docs.python.org/3/library/json.html

## Design decisions
- ISO 8601 date format (YYYY-MM-DD): https://www.iso.org/iso-8601-date-and-time-format.html
- `datetime.weekday()` returns 5 for Saturday and 6 for Sunday — used for weekend detection.
- The 180-day forward threshold is a practical heuristic: most meeting action items are within
  a six-month window; dates beyond that are almost always typos or placeholders.

## Why no external libraries?
`dateparser`, `arrow`, and `pendulum` all handle natural-language and multi-locale date parsing
well, but they require `pip install` and add version-management overhead. For a skill intended
to be portable across any Python 3.10+ environment, standard-library-only keeps the skill
deployable without a setup step.
