#!/usr/bin/env python3
"""
parse_actions.py
----------------
Parses a plain-text meeting notes file and extracts structured action items.

For each action item found, the script:
  - Extracts the task description, assignee, and raw due date
  - Parses and normalizes the due date into ISO 8601 format (YYYY-MM-DD)
  - Resolves relative expressions: "next Friday", "tomorrow", "end of month", etc.
  - Validates the due date: not in the past, not a weekend, within 180 days
  - Flags any item with a missing assignee or unparseable date
  - Outputs a Markdown table or CSV to stdout and an optional JSON file

Why this must be code and not prose:
  A language model cannot reliably normalize mixed date formats, resolve
  "next Monday" to a specific calendar date, determine whether that date
  falls on a weekend, or enforce consistent future-date logic. These
  operations are deterministic and calendar-dependent; prose alone fails.

Usage:
  python parse_actions.py <notes_file> [--format markdown|csv]
                          [--output <output.json>] [--today <YYYY-MM-DD>]
                          [--strict]

Arguments:
  notes_file         Path to the plain-text meeting notes file (required)
  --format           Output format: markdown (default) or csv
  --output           Optional path to write structured JSON results
  --today            Override today's date for testing (YYYY-MM-DD format)
  --strict           Exit with code 1 if any validation warnings are found

Examples:
  python parse_actions.py notes.txt
  python parse_actions.py notes.txt --format csv
  python parse_actions.py notes.txt --output actions.json
  python parse_actions.py notes.txt --today 2026-04-26 --output out.json

Action item detection:
  Lines are recognized as action items when they contain one of these patterns
  (case-insensitive):
    - ACTION:, ACTION ITEM:, TODO:, TASK:
    - [ ] (unchecked Markdown checkbox)

  Assignee detection looks for "@name" patterns or "Owner: Name" / "Assigned to: Name"

  Absolute date formats supported:
    YYYY-MM-DD, MM/DD/YYYY, MM-DD-YYYY, Month DD YYYY, DD Month YYYY,
    Month DD, YYYY (with or without comma)

  Relative date expressions supported (resolved against today's date):
    tomorrow, next week, end of week, end of month,
    next Monday/Tuesday/Wednesday/Thursday/Friday/Saturday/Sunday
"""

import argparse
import csv
import io
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
# Absolute date parsing
# ---------------------------------------------------------------------------

# Ordered list of (regex_pattern, strptime_format) pairs to try in sequence.
DATE_PATTERNS = [
    (r"\b(\d{4}-\d{2}-\d{2})\b",              "%Y-%m-%d"),   # 2026-04-30
    (r"\b(\d{1,2}/\d{1,2}/\d{4})\b",          "%m/%d/%Y"),   # 04/30/2026
    (r"\b(\d{1,2}-\d{1,2}-\d{4})\b",          "%m-%d-%Y"),   # 04-30-2026
    (r"\b([A-Z][a-z]+ \d{1,2},? \d{4})\b",    "%B %d %Y"),   # April 30 2026
    (r"\b(\d{1,2} [A-Z][a-z]+ \d{4})\b",      "%d %B %Y"),   # 30 April 2026
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
        text = re.sub(rf"\b{abbrev}\b", full, text, flags=re.IGNORECASE)
    return text


# ---------------------------------------------------------------------------
# Relative date parsing
# ---------------------------------------------------------------------------

WEEKDAY_NAMES = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def _next_weekday(ref: date, weekday: int) -> date:
    """Return the next occurrence of weekday (0=Mon, 6=Sun) strictly after ref."""
    days_ahead = weekday - ref.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return ref + timedelta(days=days_ahead)


def _end_of_month(ref: date) -> date:
    """Return the last calendar day of ref's month."""
    if ref.month == 12:
        return date(ref.year + 1, 1, 1) - timedelta(days=1)
    return date(ref.year, ref.month + 1, 1) - timedelta(days=1)


# Each entry: (regex pattern, resolver callable(today: date) -> date)
RELATIVE_PATTERNS: list[tuple[str, object]] = [
    (r"\btomorrow\b",         lambda t: t + timedelta(days=1)),
    (r"\bnext\s+week\b",      lambda t: t + timedelta(days=7)),
    (r"\bend\s+of\s+week\b",  lambda t: _next_weekday(t, 4)),   # Friday
    (r"\bend\s+of\s+month\b", lambda t: _end_of_month(t)),
]
# Add "next <weekday>" for each named day, capturing loop variable correctly
for _day_name, _day_num in WEEKDAY_NAMES.items():
    RELATIVE_PATTERNS.append(
        (rf"\bnext\s+{_day_name}\b", lambda t, n=_day_num: _next_weekday(t, n))
    )


def _try_relative(raw: str, today: date) -> date | None:
    """Return a resolved date if raw matches a relative expression, else None."""
    for pattern, resolver in RELATIVE_PATTERNS:
        if re.search(pattern, raw, re.IGNORECASE):
            return resolver(today)
    return None


# ---------------------------------------------------------------------------
# Unified date parser
# ---------------------------------------------------------------------------

def parse_date(raw: str, today: date | None = None) -> date | None:
    """
    Attempt to parse a raw date string into a Python date object.
    Tries relative expressions first (when today is provided), then
    falls back to the ordered list of absolute format patterns.
    Returns None if nothing matches.
    """
    stripped = raw.strip()

    # Relative expressions require a reference date
    if today is not None:
        resolved = _try_relative(stripped, today)
        if resolved is not None:
            return resolved

    # Absolute formats
    normalized = _expand_month_abbrev(stripped).replace(",", "")
    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, normalized, re.IGNORECASE)
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

MAX_DAYS_AHEAD = 180  # Dates more than 180 days out are flagged as suspicious


def validate_due_date(due: date, today: date) -> list[str]:
    """
    Return a list of warning strings for a parsed due date.
    An empty list means the date passed all checks.
    """
    warnings = []
    if due < today:
        warnings.append(f"Due date {due.isoformat()} is in the past (today is {today.isoformat()})")
    if due.weekday() in (5, 6):  # Saturday = 5, Sunday = 6
        warnings.append(f"Due date {due.isoformat()} falls on a {due.strftime('%A')}")
    days_ahead = (due - today).days
    if days_ahead > MAX_DAYS_AHEAD:
        warnings.append(
            f"Due date is {days_ahead} days away (>{MAX_DAYS_AHEAD}); confirm this is intentional"
        )
    return warnings


# ---------------------------------------------------------------------------
# Action item extraction
# ---------------------------------------------------------------------------

ACTION_TRIGGERS = re.compile(
    r"^\s*(?:\[[ ]\]|action\s*item\s*:|action\s*:|todo\s*:|task\s*:)",
    re.IGNORECASE,
)

ACTION_PREFIX = re.compile(
    r"^\s*(?:\[[ ]\]\s*|action\s*item\s*:\s*|action\s*:\s*|todo\s*:\s*|task\s*:\s*)",
    re.IGNORECASE,
)

ASSIGNEE_PATTERNS = [
    re.compile(
        r"(?:owner|assigned\s+to|assignee)\s*:\s*([A-Za-z][A-Za-z\-']{1,30}(?:\s+[A-Za-z\-']{1,30})?)"
        r"(?=\s*(?:due|by|deadline|\||$))",
        re.IGNORECASE,
    ),
    re.compile(r"@([A-Za-z][A-Za-z0-9_\-]{1,30})"),
]

DUE_DATE_PREFIXES = re.compile(
    r"(?:due\s*(?:date\s*)?:|by\s*:|deadline\s*:?)\s*(.+?)(?:\s*\||$)",
    re.IGNORECASE,
)


def extract_assignee(text: str) -> tuple[str, str]:
    """Return (assignee, cleaned_text); assignee is 'Unassigned' if none found."""
    for pattern in ASSIGNEE_PATTERNS:
        match = pattern.search(text)
        if match:
            assignee = match.group(1).strip().rstrip(".,;")
            cleaned = text[: match.start()].strip() + " " + text[match.end() :].strip()
            return assignee, cleaned.strip()
    return "Unassigned", text


def extract_due_date_raw(text: str) -> tuple[str, str]:
    """
    Return (raw_date_string, cleaned_text).
    Checks explicit prefixes first, then falls back to bare date-shaped tokens.
    Returns ('', text) if nothing is found.
    """
    match = DUE_DATE_PREFIXES.search(text)
    if match:
        raw = match.group(1).strip()
        cleaned = text[: match.start()].strip() + " " + text[match.end() :].strip()
        return raw, cleaned.strip()

    for pattern, _ in DATE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group(0)
            cleaned = text[: m.start()].strip() + " " + text[m.end() :].strip()
            return raw, cleaned.strip()

    return "", text


def parse_action_line(line: str) -> dict:
    """Parse one action-item line into a structured dict."""
    body = ACTION_PREFIX.sub("", line).strip()
    assignee, body = extract_assignee(body)
    raw_due, body = extract_due_date_raw(body)

    # Strip trailing separator characters left after token removal
    description = re.sub(r'[\s|,;—–\-]+$', '', body.strip()).strip()
    if not description:
        description = line.strip()

    return {
        "raw_line": line.strip(),
        "description": description,
        "assignee": assignee,
        "raw_due_date": raw_due,
        "parsed_due_date": None,
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def extract_actions(text: str) -> list[dict]:
    """
    Scan the full notes text and return raw action item dicts.
    Indented continuation lines are merged into the preceding trigger line.
    """
    actions = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ACTION_TRIGGERS.match(line):
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
    """Add parsed_due_date, iso_due_date, and warnings to each action dict."""
    for item in actions:
        raw = item["raw_due_date"]
        if raw:
            parsed = parse_date(raw, today=today)
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

def render_summary(actions: list[dict]) -> str:
    """Render a brief plain-English summary block."""
    total = len(actions)
    clean = sum(1 for a in actions if not a.get("warnings"))
    unassigned = sum(1 for a in actions if a["assignee"] == "Unassigned")
    return "\n".join([
        "## Action Item Summary",
        "",
        f"- **Total items found:** {total}",
        f"- **Items with no warnings:** {clean}",
        f"- **Items with warnings:** {total - clean}",
        f"- **Unassigned items:** {unassigned}",
    ]) + "\n"


def render_markdown_table(actions: list[dict]) -> str:
    """Render a Markdown table of all action items."""
    if not actions:
        return "_No action items detected._\n"
    rows = [
        "| # | Description | Assignee | Due Date (ISO) | Warnings |",
        "|---|-------------|----------|----------------|----------|",
    ]
    for idx, item in enumerate(actions, start=1):
        desc = item["description"] or "_no description_"
        due = item.get("iso_due_date") or "_missing_"
        warnings = "; ".join(item.get("warnings", [])) or "✓"
        rows.append(f"| {idx} | {desc} | {item['assignee']} | {due} | {warnings} |")
    return "\n".join(rows) + "\n"


def render_csv(actions: list[dict]) -> str:
    """Render action items as CSV, suitable for direct import into Excel or Sheets."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["#", "Description", "Assignee", "Due Date (ISO)", "Warnings"])
    for idx, item in enumerate(actions, start=1):
        writer.writerow([
            idx,
            item.get("description") or "",
            item["assignee"],
            item.get("iso_due_date") or "",
            "; ".join(item.get("warnings", [])),
        ])
    return buf.getvalue()


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
    parser.add_argument(
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="Table output format (default: markdown)",
    )
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

    if args.today:
        try:
            today = datetime.strptime(args.today, "%Y-%m-%d").date()
        except ValueError:
            print(f"ERROR: --today must be in YYYY-MM-DD format, got: {args.today}", file=sys.stderr)
            sys.exit(2)
    else:
        today = date.today()

    actions = extract_actions(text)
    actions = run_validation(actions, today)

    print(render_summary(actions))
    print()
    if args.format == "csv":
        print(render_csv(actions))
    else:
        print(render_markdown_table(actions))

    if args.output:
        serializable = [
            {k: v for k, v in item.items() if k != "parsed_due_date"}
            for item in actions
        ]
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump({"generated_on": today.isoformat(), "action_items": serializable}, f, indent=2)
            print(f"\nJSON written to: {args.output}")
        except OSError as e:
            print(f"ERROR: Could not write JSON: {e}", file=sys.stderr)
            sys.exit(2)

    if args.strict and any(item.get("warnings") for item in actions):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
