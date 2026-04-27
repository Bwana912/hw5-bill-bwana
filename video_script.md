# Video Walkthrough Script
# meeting-notes-to-actions — Homework 5
# Target length: 60–75 seconds

---

[SCREEN: Show the repository root in VS Code or terminal]

"This is my Homework 5 skill — it's called meeting-notes-to-actions."

[Navigate into .agents/skills/meeting-notes-to-actions/]

"The folder lives under .agents/skills, which is where a coding assistant like Claude Code 
or VS Code Copilot looks for registered skills. Inside you'll see SKILL.md and a scripts 
folder."

[Open SKILL.md, scroll slowly to show the frontmatter and the first two sections]

"The SKILL.md has the name and description in the frontmatter — that's what the agent 
reads to know when to activate this skill. The description is specific: it says 'use this 
when the user shares meeting notes and wants action items organized into a structured, 
validated list.' Then the body covers when to use it, when not to, expected inputs, 
step-by-step instructions, and limitations."

[Open parse_actions.py and scroll slowly through the top section]

"The Python script is the load-bearing part. A model can read meeting notes just fine, 
but it cannot reliably tell you whether a date falls on a weekend, whether it's already 
passed, or whether 'May 9, 2026' and '05/09/2026' are the same day. The script does 
that deterministically using only Python's standard library — no pip install required."

[Switch to terminal, run the normal case]

python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py sample_inputs/sample_normal.txt --today 2026-04-26

[Pause on the output table for two seconds]

"Six items extracted. Four are clean. Two are flagged because their due dates fall on a 
Saturday. The agent would surface those warnings and ask the user to confirm or adjust."

[Quickly run the edge case]

python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py sample_inputs/sample_edge.txt --today 2026-04-26

[Pause briefly on the output]

"Edge case: all six items have warnings — past dates, weekend dates, an unparseable 
natural-language date, and one date that's over 200 days out. The skill reports all of 
that and does not invent corrections."

[Run the cautious case]

python .agents/skills/meeting-notes-to-actions/scripts/parse_actions.py sample_inputs/sample_cautious.txt --today 2026-04-26

"And when there are no action item markers in the text, the skill correctly returns zero 
items rather than guessing."

[Return to SKILL.md or README.md]

"The design works because the skill separates what the model does well — reading free-form 
language — from what code does better: calendar math and consistent formatting. That's 
the point of a reusable skill. Thanks."

---
# End of script
# Estimated read time at a natural pace: ~65 seconds
