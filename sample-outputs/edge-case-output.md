# Sample Output — Edge Case

**Command run:**
```
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py sample_inputs/sample_edge.txt --today 2026-04-26
```

**Input:** `sample_inputs/sample_edge.txt` — Incident retrospective notes with problematic due dates.

**Output:**

```
## Action Item Summary

- **Total items found:** 6
- **Items with no warnings:** 0
- **Items with warnings:** 6
- **Unassigned items:** 2


| # | Description | Assignee | Due Date (ISO) | Warnings |
|---|-------------|----------|----------------|----------|
| 1 | Write post-mortem report | sam | 2026-04-20 | Due date 2026-04-20 is in the past (today is 2026-04-26) |
| 2 | Update runbook documentation | Unassigned | 2026-04-26 | Due date 2026-04-26 falls on a Sunday |
| 3 | Notify affected clients by Saturday | dana | 2026-04-25 | Due date 2026-04-25 is in the past (today is 2026-04-26); Due date 2026-04-25 falls on a Saturday |
| 4 | Archive incident logs | kenji | _missing_ | Could not parse due date from: 'next quarter' |
| 5 | Reassign on-call rotation — no assignee | Unassigned | 2026-05-03 | Due date 2026-05-03 falls on a Sunday |
| 6 | Present findings to leadership | sam | 2026-12-31 | Due date is 249 days away (>180); confirm this is intentional |
```

**What this shows:** All 6 items have at least one warning. The script caught: two past dates, two
weekend-only dates, one item that triggered both past and weekend flags (April 25 was a Saturday that
already passed), one unparseable natural-language date ("next quarter"), and one date 249 days out.
The skill reports every problem and does not invent corrections — the user must resolve each one.
