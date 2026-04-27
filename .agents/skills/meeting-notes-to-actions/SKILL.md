---
name: meeting-notes-to-actions
description: Parses plain-text meeting notes to extract action items, normalize due dates into ISO 8601 format, validate that due dates are not in the past or on weekends, and produce a clean Markdown table and optional JSON output. Use this skill when the user shares meeting notes, a call summary, or any text containing tasks, to-dos, or assigned items and wants them organized into a structured, validated action list.
---

# meeting-notes-to-actions

## What this skill does

This skill reads plain-text meeting notes and produces a structured, validated list of action items. For each action item, it extracts the task description, the assignee, and the due date. It then normalizes the due date into ISO 8601 format (YYYY-MM-DD), checks whether the date has already passed, whether it falls on a weekend, and whether it is suspiciously far in the future. The output is a readable Markdown table plus an optional JSON file for downstream use.

The Python script handles all date parsing and validation deterministically. A language model alone cannot reliably normalize mixed date formats, calculate whether a date falls on a weekend, or consistently enforce future-date constraints across different inputs.

---

## When to use this skill

Use this skill when the user:
- Shares meeting notes, a Zoom summary, a call recap, or any text that contains tasks or action items
- Wants to turn informal notes into a clean, structured, assignee-linked action list
- Needs due dates normalized to a consistent format or validated for correctness
- Asks to "pull out the action items," "parse my meeting notes," "summarize the tasks," or similar

Trigger phrases include: "extract action items," "parse these notes," "pull the tasks from this," "what are the action items," "organize the to-dos," "create an action table from this."

---

## When NOT to use this skill

Do not use this skill when:
- The text has no action items, tasks, or to-dos (use general summarization instead)
- The user wants a narrative summary of the meeting content, not a task list
- The input is a formal document such as a contract, report, or agenda with no action-item markup
- The user explicitly asks only for a bullet-point summary or minutes, not a structured table
- The notes are in a language other than English (date parsing may fail on non-English month names)

---

## Expected inputs

| Input | Required | Description |
|---|---|---|
| Meeting notes text | Required | Plain text pasted into the conversation or a `.txt` file path |
| Reference date | Optional | Defaults to today; can be overridden with `--today YYYY-MM-DD` |
| JSON output path | Optional | `--output <file.json>` to write machine-readable results |
| Strict mode | Optional | `--strict` causes the script to exit with code 1 if any warning is present |

**Recognized action item markers** (case-insensitive):
- `Action:`, `Action item:`, `TODO:`, `Task:` at the start of a line
- `[ ]` (unchecked Markdown checkbox)

**Recognized assignee patterns:**
- `@username` anywhere in the line
- `Owner: Name`, `Assigned to: Name`, `Assignee: Name`

**Recognized due date formats:**
- `YYYY-MM-DD` (e.g., 2026-05-02)
- `MM/DD/YYYY` (e.g., 05/02/2026)
- `MM-DD-YYYY` (e.g., 05-02-2026)
- `Month DD YYYY` or `Month DD, YYYY` (e.g., May 2, 2026)
- `DD Month YYYY` (e.g., 2 May 2026)
- Preceded by `Due:`, `Due date:`, `By:`, or `Deadline:`

---

## Step-by-step instructions

**Step 1 — Receive the notes**
If the user pastes notes directly into the conversation, save them to a temporary `.txt` file. If the user provides a file path, use it directly.

**Step 2 — Run the script**
```bash
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py <notes_file> [--output actions.json] [--today YYYY-MM-DD]
```

**Step 3 — Read the script output**
The script prints a summary block and a Markdown table to stdout. Each row contains:
- Item number
- Task description
- Assignee (or "Unassigned" if none detected)
- ISO due date (or "_missing_" if none found)
- Warnings (past date, weekend date, far-future date, unparseable date, or ✓ for clean)

**Step 4 — Interpret and present results**
Present the Markdown table to the user. Call out:
- Any items where the due date is in the past (the owner should confirm or reschedule)
- Any unassigned items (the user should confirm ownership)
- Any items with no due date (the user should supply one)

**Step 5 — Optional: write JSON**
If the user wants a machine-readable file (for import into a task tracker, spreadsheet, or another tool), pass `--output actions.json` and share the resulting file.

**Step 6 — Do not invent or correct**
Do not add assignees, invent due dates, or rewrite task descriptions. If a field is missing or unparseable, report it as a warning and ask the user to clarify.

---

## Expected output format

**Stdout (always produced):**
```
## Action Item Summary

- Total items found: N
- Items with no warnings: N
- Items with warnings: N
- Unassigned items: N

| # | Description | Assignee | Due Date (ISO) | Warnings |
|---|-------------|----------|----------------|----------|
| 1 | Draft onboarding doc | @maya | 2026-05-02 | ✓ |
| 2 | Review budget proposal | Unassigned | _missing_ | No due date found |
| 3 | Send invites | @jordan | 2026-04-19 | Due date 2026-04-19 is in the past |
```

**JSON output (when `--output` is passed):**
```json
{
  "generated_on": "2026-04-26",
  "action_items": [
    {
      "raw_line": "Action: Draft onboarding doc @maya Due: 2026-05-02",
      "description": "Draft onboarding doc",
      "assignee": "maya",
      "raw_due_date": "2026-05-02",
      "iso_due_date": "2026-05-02",
      "warnings": []
    }
  ]
}
```

---

## Limitations and checks

- **Date parsing is format-sensitive.** Natural-language relative dates like "next Friday" or "end of quarter" are not supported. Only explicit calendar dates in the listed formats are parsed.
- **Assignee detection is pattern-based.** If assignees are written in an unusual format (e.g., "Responsibility: Full Name"), they will be reported as "Unassigned." Prompt the user to clarify.
- **Multi-line continuation is limited.** Continuation lines must be indented with at least four spaces or a tab directly after the trigger line.
- **English only.** Month names in languages other than English will not parse correctly.
- **No inference.** The script does not guess at missing fields. If a due date or assignee is missing, it flags it and expects the user or operator to resolve it.
- **Validation window.** Dates more than 180 days in the future receive a warning but are not rejected; the user should confirm they are intentional.
- **The skill does not write to any task tracker.** It produces a table and optionally a JSON file. Integration with Asana, Jira, or similar tools is out of scope for this skill.
