# Sample Output — Normal Case

**Command run:**
```
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py sample_inputs/sample_normal.txt --today 2026-04-26
```

**Input:** `sample_inputs/sample_normal.txt` — Q2 Planning Kickoff notes with 6 explicit action items.

**Output:**

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

**What this shows:** The skill correctly parsed 6 items across four different action-item marker styles
(`Action:`, `Action item:`, `TODO:`, `[ ]`), three different date formats (`YYYY-MM-DD`, `Month DD, YYYY`,
`MM/DD/YYYY`), and two assignee patterns (`@name` and `assigned to: Name`). Two Saturday dates were
caught automatically — the skill flags them rather than silently accepting them.
