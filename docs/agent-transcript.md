# Agent Transcript — meeting-notes-to-actions

This document records three real Claude Code sessions demonstrating the skill being
discovered and invoked. Each session uses the sample input files in `sample_inputs/`.

---

## Session 1 — Normal case

**User prompt:**
> Here are my notes from today's Q2 planning kickoff. Can you pull out all the action
> items and show me a table with the owner and due date for each one?
>
> *(contents of `sample_inputs/sample_normal.txt` pasted)*

**Claude Code (skill discovery):**
The request matches the `meeting-notes-to-actions` skill: the user has shared meeting
notes and wants action items organized into a structured, validated list. Activating skill.

**Claude Code (runs script):**
```
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py sample_inputs/sample_normal.txt --today 2026-04-26
```

**Script output:**
```
## Action Item Summary

- **Total items found:** 6
- **Items with no warnings:** 4
- **Items with warnings:** 2
- **Unassigned items:** 0


| # | Description | Assignee | Due Date (ISO) | Warnings |
|---|-------------|----------|----------------|----------|
| 1 | Draft updated onboarding documentation | maya | 2026-05-02 | Due date 2026-05-02 falls on a Saturday |
| 2 | Review and approve Q2 budget proposal | jordan | 2026-05-09 | Due date 2026-05-09 falls on a Saturday |
| 3 | Schedule stakeholder briefing for program leads | priya | 2026-05-07 | ✓ |
| 4 | Send meeting invites for May sync series | marcus | 2026-05-04 | ✓ |
| 5 | Confirm vendor contract renewal | Maya | 2026-05-12 | ✓ |
| 6 | Prepare slide deck for board update | jordan | 2026-05-15 | ✓ |
```

**Claude Code (presents result):**
Here are the 6 action items from your Q2 planning kickoff:

| # | Description | Assignee | Due Date (ISO) | Warnings |
|---|-------------|----------|----------------|----------|
| 1 | Draft updated onboarding documentation | maya | 2026-05-02 | Due date 2026-05-02 falls on a Saturday |
| 2 | Review and approve Q2 budget proposal | jordan | 2026-05-09 | Due date 2026-05-09 falls on a Saturday |
| 3 | Schedule stakeholder briefing for program leads | priya | 2026-05-07 | ✓ |
| 4 | Send meeting invites for May sync series | marcus | 2026-05-04 | ✓ |
| 5 | Confirm vendor contract renewal | Maya | 2026-05-12 | ✓ |
| 6 | Prepare slide deck for board update | jordan | 2026-05-15 | ✓ |

Two items need your attention before you share this list: items 1 and 2 have due dates
that fall on a Saturday (May 2 and May 9). Did you mean the Friday before or the Monday
after? I won't adjust the dates automatically — please confirm or correct them.

---

## Session 2 — Edge case

**User prompt:**
> These are notes from our incident retrospective. Several of the action items have
> issues. Can you extract them and validate the due dates?
>
> *(contents of `sample_inputs/sample_edge.txt` pasted)*

**Claude Code (skill discovery):**
The user has shared meeting notes and explicitly asked for due-date validation.
This matches the `meeting-notes-to-actions` skill. Activating skill.

**Claude Code (runs script):**
```
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py sample_inputs/sample_edge.txt --today 2026-04-26
```

**Script output:**
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

**Claude Code (presents result):**
All 6 items from the incident retrospective have warnings. Here's what needs to be
resolved before this list can be actioned:

| # | Description | Assignee | Due Date (ISO) | Warnings |
|---|-------------|----------|----------------|----------|
| 1 | Write post-mortem report | sam | 2026-04-20 | Due date 2026-04-20 is in the past (today is 2026-04-26) |
| 2 | Update runbook documentation | Unassigned | 2026-04-26 | Due date 2026-04-26 falls on a Sunday |
| 3 | Notify affected clients by Saturday | dana | 2026-04-25 | Due date 2026-04-25 is in the past (today is 2026-04-26); Due date 2026-04-25 falls on a Saturday |
| 4 | Archive incident logs | kenji | _missing_ | Could not parse due date from: 'next quarter' |
| 5 | Reassign on-call rotation — no assignee | Unassigned | 2026-05-03 | Due date 2026-05-03 falls on a Sunday |
| 6 | Present findings to leadership | sam | 2026-12-31 | Due date is 249 days away (>180); confirm this is intentional |

Issues to resolve:
- **Items 1 and 3** have dates already in the past. Confirm the new target dates.
- **Item 3** is also a Saturday — both problems apply.
- **Items 2 and 5** fall on Sundays. Please shift to business days.
- **Item 4** uses "next quarter" — the script cannot resolve that to a specific date.
  Please provide an explicit date (e.g., `Due: 2026-06-30`).
- **Items 2 and 5** have no assignee. Please confirm ownership.
- **Item 6** is 249 days out. If December 31 is intentional, no action needed.

I won't guess at corrections. Please update the notes and re-run when ready.

---

## Session 3 — Cautious case (no action items)

**User prompt:**
> Can you extract the action items from these all-hands notes?
>
> *(contents of `sample_inputs/sample_cautious.txt` pasted)*

**Claude Code (skill discovery):**
The user has shared meeting notes and asked to extract action items. Activating
`meeting-notes-to-actions` skill.

**Claude Code (runs script):**
```
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py sample_inputs/sample_cautious.txt --today 2026-04-26
```

**Script output:**
```
## Action Item Summary

- **Total items found:** 0
- **Items with no warnings:** 0
- **Items with warnings:** 0
- **Unassigned items:** 0


_No action items detected._
```

**Claude Code (presents result):**
The script found no action items in these all-hands notes.

The notes contain substantive content — revenue figures, product update, policy
discussion, a next meeting date — but no lines that begin with a recognized action-item
marker. The skill looks for these patterns (case-insensitive):

- `Action:` or `Action item:`
- `TODO:`
- `Task:`
- `[ ]` (unchecked Markdown checkbox)

The skill does not invent tasks from prose. If the CEO or presenter verbally assigned
work that wasn't marked up in the notes, those tasks won't appear here.

To proceed, you can either:
1. Re-share notes that include explicit action-item markers, or
2. Tell me which specific tasks you'd like to track and I'll help you format them.
