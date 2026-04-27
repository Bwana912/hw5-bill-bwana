# Design Notes — meeting-notes-to-actions

## The core architecture decision: model + code, not model alone

The skill splits the workflow into two layers with a hard boundary:

| Layer | Handles | Why |
|---|---|---|
| Language model | Reading free-form prose, identifying which lines are action items, presenting results in conversational context | Models read natural language well but produce inconsistent output for calendar math |
| Python script | Date parsing, date normalization, weekend detection, past-date detection, far-future flagging, CSV/JSON formatting | Deterministic; same input always produces the same output; does not depend on phrasing |

The boundary is enforced by design: the script never makes prose judgments and the
model never does calendar arithmetic. If either layer tried to do the other's job,
reliability would drop — the model would occasionally accept a Saturday deadline
without flagging it, and the script cannot distinguish "this is an action item" from
"this is a header."

---

## Why date parsing requires code

A language model given the text `Due: 05/09/2026` might correctly identify this as
May 9 in one response and September 5 in another, depending on context and model
temperature. The same model given `next Friday` cannot deterministically resolve it
to a specific calendar date without knowing today's date, and even then it may
produce different answers across sessions.

The script resolves both problems:

- **Absolute formats** — `YYYY-MM-DD`, `MM/DD/YYYY`, `Month DD YYYY`, and three
  others are tried in a fixed priority order. The first match wins. The result is
  always the same for the same input.

- **Relative expressions** — `next Friday`, `tomorrow`, `end of month`, and eight
  other expressions are matched by regex and resolved against a reference date
  (`--today`, or the system date). The resolution is deterministic: `next Friday`
  from a Monday always produces the Friday of that week.

---

## Why weekend and past-date validation requires code

A model asked "is May 2, 2026 a Saturday?" might answer correctly most of the time,
but it cannot guarantee correctness across all dates, especially near year boundaries.
`date.weekday()` in Python's standard library always returns the correct answer.

Similarly, comparing a due date to today's date requires knowing today's date — which
a model without a tool call cannot do reliably. The script always has an accurate
reference point.

---

## Progressive disclosure in SKILL.md

The skill follows the Week 5 progressive-disclosure pattern:

1. **Frontmatter** (4 lines) — name and description. Enough for an agent to decide
   whether to activate the skill. Loaded on every request.

2. **When to use / When not to use** (short section) — loaded when the agent is
   deciding whether to invoke the skill for a specific request.

3. **Step-by-step instructions + output format** — loaded when the agent is actually
   running the skill.

4. **Limitations** — loaded last, when the agent needs to explain what the skill
   cannot do and why.

This structure keeps the common path cheap: most requests only need the frontmatter
and the first two sections.

---

## Why no external libraries

`dateparser`, `arrow`, and `pendulum` all handle relative and multi-locale date
parsing well. They were deliberately excluded because:

1. The skill is meant to be portable: any Python 3.10+ environment can run it
   without a setup step.
2. The assignment's design goal was to show that code is load-bearing — not to
   wrap a library. Using `dateparser` for the relative expressions would make the
   script mostly glue code.
3. The relative expressions needed here (`next Monday`, `tomorrow`, `end of month`)
   are finite and fully covered by `timedelta` and `date.weekday()`.

The one remaining limitation from this choice is that locale-specific month names
(French, Spanish, etc.) are not supported. That is documented explicitly.

---

## Output format design

Three output modes were implemented deliberately:

- **Markdown table** (default) — renders directly in GitHub, agent chat, and most
  documentation tools. Best for human review in a coding assistant context.

- **CSV** — directly importable into Excel or Google Sheets without any conversion
  step. This is the actual workflow of the business audience this skill serves.

- **JSON** (`--output file.json`) — machine-readable for downstream tool integration
  (task trackers, APIs, other scripts). Not printed to stdout to avoid noise.

All three share the same validation pipeline; the format flag only affects rendering.
