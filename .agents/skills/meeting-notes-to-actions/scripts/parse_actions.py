#!/usr/bin/env python3
"""
parse_actions.py
----------------
Parses a plain-text meeting notes file and extracts structured action items.

For each action item found, the script:
  - Extracts the task description, assignee, and raw due date
  - Parses and normalizes the due date into ISO 8601 format (YYYY-MM-DD)
  - Validates the due date: not in the past, not a weekend, within 180 days
  - Flags any item with a missing assignee or unparseable date
  - Outputs a Markdown table to stdout and an optional JSON file

Why this must be code and not prose:
  A language model cannot reliably normalize mixed date formats, determine
  whether a date falls on a weekend, or enforce consistent future-date logic.
  These operations are deterministic and calendar-dependent; prose alone fails.

Usage:
  python parse_actions.py <notes_file> [--output <output.json>] [--today <YYYY-MM-DD>]

Arguments:
  notes_file         Path to the plain-text meeting notes file (required)
  --output           Optional path to write structured JSON results
  --today            Override today's date for testing (YYYY-MM-DD format)
  --strict           Exit with code 1 if any validation warnings are found

Examples:
  python parse_actions.py meeting_2026_04_26.txt
  python parse_actions.py notes.txt --output actions.json
  python parse_actions.py notes.txt --today 2026-04-26 --output out.json

Action item detection:
  Lines are recognized as action items when they contain one of these patterns
  (case-insensitive):
    - ACTION:, ACTION ITEM:, TODO:, TASK:
    - [ ] (unchecked Markdown checkbox)
  
  Assignee detection looks for "@name" patterns or "Owner: Name" or "Assigned to: Name"
  Date detection supports these formats:
    YYYY-MM-DD, MM/DD/YYYY, MM-DD-YYYY, Month DD YYYY, DD Month YYYY,
    Month DD, YYYY (with or without comma)
"""

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta

# Ensure UTF-8 output on Windows terminals (needed for the ✓ character)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

# Ordered list of (regex_pattern, strptime_format) pairs to try in sequence.
DATE_PATTERNS = [
    (r"\b(\d{4}-\d{2}-\d{2})\b",              "%Y-%m-%d"),          # 2026-04-30
    (r"\b(\d{1,2}/\d{1,2}/\d{4})\b",          "%m/%d/%Y"),          # 04/30/2026
    (r"\b(\d{1,2}-\d{1,2}-\d{4})\b",          "%m-%d-%Y"),          # 04-30-2026
    (r"\b([A-Z][a-z]+ \d{1,2},? \d{4})\b",    "%B %d %Y"),          # April 30 2026
    (r"\b(\d{1,2} [A-Z][a-z]+ \d{4})\b",      "%d %B %Y"),          # 30 April 2026
]

MONTH_ABBREVS = {
    "jan": "January", "feb": "February", "mar": "March",
    "apr": "April",   "may": "May",      "jun": "June",
    "jul": "July",    "aug": "August",   "sep": "September",
    "oct": "October", "nov": "November", "dec": "December",
}


def _expand_month_abbrev(text: str) -> str:
    """Expand three-letter month abbreviations to full names for reliable parsing."""
    for abbrev, full in MONTH_ABBREVS.items():
        # Match abbreviation followed by a space or digit (not inside a longer word)
        text = re.sub(rf"\b{abbrev}\b", full, text, flags=re.IGNORECASE)
    return text


def parse_date(raw: str) -> date | None:
    """
    Attempt to parse a raw date string into a Python date object.
    Returns None if no supported format matches.
    """
    raw = _expand_month_abbrev(raw.strip())
    # Remove trailing commas inside the string (e.g., "April 30, 2026" → "April 30 2026")
    raw = raw.replace(",", "")

    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, raw, re.IGNORECASE)
        if match:
            candidate = match.group(1).replace(",", "")
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

MAX_DAYS_AHEAD = 180  # Items more than 180 days out are flagged as suspicious


def validate_due_date(due: date, today: date) -> list[str]:
    """
    Return a list of warning strings for a parsed due date.
    An empty list means the date passed all checks.
    """
    warnings = []
    if due < today:
        warnings.append(f"Due date {due.isoformat()} is in the past (today is {today.isoformat()})")
    if due.weekday() in (5, 6):  # Saturday = 5, Sunday = 6
        day_name = due.strftime("%A")
        warnings.append(f"Due date {due.isoformat()} falls on a {day_name}")
    days_ahead = (due - today).days
    if days_ahead > MAX_DAYS_AHEAD:
        warnings.append(
            f"Due date is {days_ahead} days away (>{MAX_DAYS_AHEAD}); confirm this is intentional"
        )
    return warnings


# ---------------------------------------------------------------------------
# Action item extraction
# ---------------------------------------------------------------------------

# Patterns that mark a line (or the start of a line) as an action item
ACTION_TRIGGERS = re.compile(
    r"^\s*(?:\[[ ]\]|action\s*item\s*:|action\s*:|todo\s*:|task\s*:)",
    re.IGNORECASE,
)

# Strip the trigger prefix from the line so we can parse what's left
ACTION_PREFIX = re.compile(
    r"^\s*(?:\[[ ]\]\s*|action\s*item\s*:\s*|action\s*:\s*|todo\s*:\s*|task\s*:\s*)",
    re.IGNORECASE,
)

# Assignee patterns: @username, "Owner: Name", "Assigned to: Name", "Assignee: Name"
ASSIGNEE_PATTERNS = [
    # "Owner: Name", "Assigned to: Name", "Assignee: Name" — stop before due/by/deadline
    re.compile(
        r"(?:owner|assigned\s+to|assignee)\s*:\s*([A-Za-z][A-Za-z\-']{1,30}(?:\s+[A-Za-z\-']{1,30})?)"
        r"(?=\s*(?:due|by|deadline|\||$))",
        re.IGNORECASE,
    ),
    re.compile(r"@([A-Za-z][A-Za-z0-9_\-]{1,30})"),
]

# Due date prefix: "due: ...", "by: ...", "deadline: ...", or bare date.
# Greedy capture to end of the segment so a comma inside "May 9, 2026" is not
# mistaken for a field delimiter.
DUE_DATE_PREFIXES = re.compile(
    r"(?:due\s*(?:date\s*)?:|by\s*:|deadline\s*:?)\s*(.+?)(?:\s*\||$)",
    re.IGNORECASE,
)


def extract_assignee(text: str) -> tuple[str, str]:
    """
    Return (assignee, cleaned_text) where assignee is the name found or 'Unassigned'
    and cleaned_text has the assignee token removed.
    """
    for pattern in ASSIGNEE_PATTERNS:
        match = pattern.search(text)
        if match:
            assignee = match.group(1).strip().rstrip(".,;")
            cleaned = text[: match.start()].strip() + " " + text[match.end() :].strip()
            return assignee, cleaned.strip()
    return "Unassigned", text


def extract_due_date_raw(text: str) -> tuple[str, str]:
    """
    Return (raw_date_string, cleaned_text) by looking for explicit due-date prefixes
    or bare ISO / slash-delimited dates as a fallback.
    Returns ('', text) if no date is found.
    """
    # Try explicit prefix first
    match = DUE_DATE_PREFIXES.search(text)
    if match:
        raw = match.group(1).strip()
        cleaned = text[: match.start()].strip() + " " + text[match.end() :].strip()
        return raw, cleaned.strip()

    # Fallback: look for any date-shaped token in the line
    for pattern, _ in DATE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group(0)
            cleaned = text[: m.start()].strip() + " " + text[m.end() :].strip()
            return raw, cleaned.strip()

    return "", text


def parse_action_line(line: str) -> dict:
    """
    Parse a single action-item line into a structured dict with keys:
      raw_line, description, assignee, raw_due_date, parsed_due_date
    """
    # Strip the action trigger prefix to get the body
    body = ACTION_PREFIX.sub("", line).strip()

    assignee, body = extract_assignee(body)
    raw_due, body = extract_due_date_raw(body)

    # Whatever remains is the description; strip trailing separator chars
    # (em dashes and pipes often appear when assignee/date tokens are removed)
    description = re.sub(r'[\s|,;—–\-]+$', '', body.strip()).strip()
    if not description:
        description = line.strip()  # fall back to the full line if parsing consumed everything

    return {
        "raw_line": line.strip(),
        "description": description,
        "assignee": assignee,
        "raw_due_date": raw_due,
        "parsed_due_date": None,   # filled in after validation
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def extract_actions(text: str) -> list[dict]:
    """
    Scan the full notes text and return a list of raw action item dicts.
    Multi-line continuation (indented lines after a trigger) is supported.
    """
    actions = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ACTION_TRIGGERS.match(line):
            # Accumulate continuation lines (indented and non-trigger)
            full_line = line
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if next_line.startswith(("    ", "\t")) and not ACTION_TRIGGERS.match(next_line):
                    full_line += " " + next_line.strip()
                    j += 1
                else:
                    break
            actions.append(parse_action_line(full_line))
            i = j
        else:
            i += 1
    return actions


def run_validation(actions: list[dict], today: date) -> list[dict]:
    """
    Add parsed_due_date, iso_due_date, and warnings to each action dict.
    """
    for item in actions:
        raw = item["raw_due_date"]
        if raw:
            parsed = parse_date(raw)
            if parsed:
                item["parsed_due_date"] = parsed
                item["iso_due_date"] = parsed.isoformat()
                item["warnings"] = validate_due_date(parsed, today)
            else:
                item["parsed_due_date"] = None
                item["iso_due_date"] = None
                item["warnings"] = [f"Could not parse due date from: '{raw}'"]
        else:
            item["parsed_due_date"] = None
            item["iso_due_date"] = None
            item["warnings"] = ["No due date found"]
    return actions


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def render_markdown_table(actions: list[dict]) -> str:
    """Render a clean Markdown table of all action items."""
    if not actions:
        return "_No action items detected._\n"

    header = "| # | Description | Assignee | Due Date (ISO) | Warnings |"
    divider = "|---|-------------|----------|----------------|----------|"
    rows = [header, divider]

    for idx, item in enumerate(actions, start=1):
        desc = item["description"] or "_no description_"
        assignee = item["assignee"]
        due = item.get("iso_due_date") or "_missing_"
        warnings = "; ".join(item.get("warnings", [])) or "✓"
        rows.append(f"| {idx} | {desc} | {assignee} | {due} | {warnings} |")

    return "\n".join(rows) + "\n"


def render_summary(actions: list[dict]) -> str:
    """Render a brief plain-English summary."""
    total = len(actions)
    clean = sum(1 for a in actions if not a.get("warnings"))
    with_issues = total - clean
    unassigned = sum(1 for a in actions if a["assignee"] == "Unassigned")

    lines = [
        f"## Action Item Summary",
        f"",
        f"- **Total items found:** {total}",
        f"- **Items with no warnings:** {clean}",
        f"- **Items with warnings:** {with_issues}",
        f"- **Unassigned items:** {unassigned}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Parse meeting notes and extract validated action items.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("notes_file", help="Path to plain-text meeting notes file")
    parser.add_argument("--output", help="Optional path to write JSON output", default=None)
    parser.add_argument(
        "--today",
        help="Override today's date for validation (YYYY-MM-DD). Defaults to system date.",
        default=None,
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any validation warnings are present",
    )
    args = parser.parse_args()

    # --- Load notes file ---
    try:
        with open(args.notes_file, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.notes_file}", file=sys.stderr)
        sys.exit(2)
    except OSError as e:
        print(f"ERROR: Could not read file: {e}", file=sys.stderr)
        sys.exit(2)

    if not text.strip():
        print("ERROR: The notes file is empty.", file=sys.stderr)
        sys.exit(2)

    # --- Determine reference date ---
    if args.today:
        try:
            today = datetime.strptime(args.today, "%Y-%m-%d").date()
        except ValueError:
            print(f"ERROR: --today must be in YYYY-MM-DD format, got: {args.today}", file=sys.stderr)
            sys.exit(2)
    else:
        today = date.today()

    # --- Extract and validate ---
    actions = extract_actions(text)
    actions = run_validation(actions, today)

    # --- Stdout output ---
    print(render_summary(actions))
    print()
    print(render_markdown_table(actions))

    # --- JSON output ---
    if args.output:
        serializable = []
        for item in actions:
            record = {k: v for k, v in item.items() if k != "parsed_due_date"}
            serializable.append(record)
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(
                    {"generated_on": today.isoformat(), "action_items": serializable},
                    f,
                    indent=2,
                )
            print(f"\nJSON written to: {args.output}")
        except OSError as e:
            print(f"ERROR: Could not write JSON: {e}", file=sys.stderr)
            sys.exit(2)

    # --- Strict mode exit code ---
    if args.strict:
        any_warnings = any(item.get("warnings") for item in actions)
        if any_warnings:
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
