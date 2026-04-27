# Sample Output — Cautious Case

**Command run:**
```
python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py sample_inputs/sample_cautious.txt --today 2026-04-26
```

**Input:** `sample_inputs/sample_cautious.txt` — Monthly all-hands notes with no action item markers.

**Output:**

```
## Action Item Summary

- **Total items found:** 0
- **Items with no warnings:** 0
- **Items with warnings:** 0
- **Unassigned items:** 0


_No action items detected._
```

**What this shows:** The notes contain genuine business content (revenue figures, product updates,
upcoming meeting dates) but no recognized action-item markers (`Action:`, `TODO:`, `[ ]`, etc.).
The script returns zero items rather than inferring tasks from the prose. This is the correct behavior:
the skill does not hallucinate action items that were not explicitly marked.

An agent invoking this skill would report that no action items were detected and explain what markers
the skill looks for, rather than guessing at what the CEO might have meant to assign.
