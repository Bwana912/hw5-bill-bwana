# Changelog

All notable changes to this project are documented here.

---

## [1.2.0] — 2026-04-27

### Added
- **Relative date parsing** — `next Monday`, `next Friday`, `tomorrow`, `next week`,
  `end of week`, `end of month` are now resolved deterministically against today's date
  using only the Python standard library. No external packages required.
- **CSV output** — `--format csv` flag produces a spreadsheet-ready table, suitable for
  direct import into Excel or Google Sheets.
- **GitHub Actions CI** — automated test suite runs on Python 3.10, 3.11, and 3.12
  on every push and pull request.
- **`docs/agent-transcript.md`** — complete written record of the skill being discovered
  and invoked inside Claude Code, covering all three test scenarios.
- **`docs/design.md`** — architecture document explaining the model-plus-code split and
  why each layer handles what it does.
- **`CONTRIBUTING.md`** — contribution guide covering setup, test runner, and extension
  points (new date formats, new assignee patterns).
- **`LICENSE`** — MIT license.
- **`CHANGELOG.md`** — this file.

---

## [1.1.0] — 2026-04-27

### Added
- **`run_tests.py`** — deterministic PASS/FAIL test runner for all three sample cases.
- **`sample-outputs/`** — actual terminal output from normal, edge, and cautious cases,
  committed as Markdown files for easy review without running the script.
- **`references/REFERENCES.md`** — pointers to Python stdlib docs and design rationale
  for the 180-day threshold and weekend validation rules.
- **`.gitignore`** — Python, editor, and `.claude/` exclusions.

### Fixed
- Trailing em-dash (`—`) left in description when an assignee uses separator syntax
  (`Confirm vendor contract renewal — assigned to: Maya`). Description is now cleaned
  using a trailing-separator regex rather than a fixed character strip.

---

## [1.0.0] — 2026-04-27

### Added
- Initial release: `meeting-notes-to-actions` skill package.
- `SKILL.md` with frontmatter, when-to-use, when-not-to-use, step-by-step instructions,
  expected output format, and limitations.
- `parse_actions.py` — dependency-free Python script handling: action item detection
  (`Action:`, `TODO:`, `[ ]`, etc.), assignee extraction (`@mention`, `Owner:`,
  `Assigned to:`), multi-format date parsing (ISO, slash, spelled-out month),
  weekend validation, past-date validation, far-future-date warning, Markdown table
  output, and optional JSON output.
- Three sample input files: `sample_normal.txt`, `sample_edge.txt`, `sample_cautious.txt`.
- `README.md` with full project documentation and video walkthrough script.
