#!/usr/bin/env python3
"""
run_tests.py
------------
Validates parse_actions.py against all sample inputs and feature flags.

Runs each test case with a fixed reference date (2026-04-26) and checks
that the script produces the expected item count, warning count, and exit
code. Prints PASS or FAIL for each case and exits with code 1 if any
case fails.

Usage:
    python run_tests.py
"""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(".agents/skills/meeting-notes-to-actions/scripts/parse_actions.py")
TODAY = "2026-04-26"  # Sunday — useful for edge-case date math


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def parse_summary(output: str) -> dict:
    """Extract numeric counts from the summary block."""
    result = {"total": None, "warnings": None, "clean": None}
    for line in output.splitlines():
        if "Total items found:" in line:
            result["total"] = int(line.split(":")[-1].strip().strip("*"))
        elif "Items with warnings:" in line:
            result["warnings"] = int(line.split(":")[-1].strip().strip("*"))
        elif "Items with no warnings:" in line:
            result["clean"] = int(line.split(":")[-1].strip().strip("*"))
    return result


def check(label: str, actual, expected, failures: list) -> bool:
    if actual != expected:
        failures.append(f"  {label}: expected {expected!r}, got {actual!r}")
        return False
    return True


def report(name: str, passed: bool, failures: list) -> bool:
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    for f in failures:
        print(f)
    return passed


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_normal_case() -> bool:
    result = run(["sample_inputs/sample_normal.txt", "--today", TODAY])
    s = parse_summary(result.stdout)
    failures = []
    check("total", s["total"], 6, failures)
    check("warnings", s["warnings"], 2, failures)
    check("clean", s["clean"], 4, failures)
    check("exit code", result.returncode, 0, failures)
    return report("normal case", not failures, failures)


def test_edge_case() -> bool:
    result = run(["sample_inputs/sample_edge.txt", "--today", TODAY])
    s = parse_summary(result.stdout)
    failures = []
    check("total", s["total"], 6, failures)
    check("warnings", s["warnings"], 6, failures)
    check("clean", s["clean"], 0, failures)
    check("exit code", result.returncode, 0, failures)
    return report("edge case", not failures, failures)


def test_cautious_case() -> bool:
    result = run(["sample_inputs/sample_cautious.txt", "--today", TODAY])
    s = parse_summary(result.stdout)
    failures = []
    check("total", s["total"], 0, failures)
    check("warnings", s["warnings"], 0, failures)
    check("exit code", result.returncode, 0, failures)
    return report("cautious case (no action items)", not failures, failures)


def test_relative_dates() -> bool:
    """Write a temp file with relative-date action items and verify they resolve."""
    import tempfile, os
    # TODAY is 2026-04-26 (Sunday). "next Monday" should be 2026-04-27.
    # "next Friday" should be 2026-05-01. "tomorrow" should be 2026-04-27.
    # All three are in the future and on weekdays => no warnings expected.
    notes = (
        "Action: Send status update @alice Due: next Monday\n"
        "Action: Prepare demo @bob Due: next Friday\n"
        "Action: Share draft @carol Due: tomorrow\n"
    )
    failures = []
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                    encoding="utf-8", delete=False) as f:
        f.write(notes)
        tmp = f.name
    try:
        result = run([tmp, "--today", TODAY])
        s = parse_summary(result.stdout)
        check("total", s["total"], 3, failures)
        # "tomorrow" from Sunday = Monday (weekday) -> no warning
        # "next Monday" from Sunday = next Monday -> no warning
        # "next Friday" from Sunday = next Friday -> no warning
        check("warnings", s["warnings"], 0, failures)
        check("exit code", result.returncode, 0, failures)
        # Verify ISO dates appear in output
        for iso in ["2026-04-27", "2026-05-01"]:
            if iso not in result.stdout:
                failures.append(f"  expected {iso} in output")
    finally:
        os.unlink(tmp)
    return report("relative dates", not failures, failures)


def test_csv_format() -> bool:
    """Verify --format csv produces parseable CSV with correct column count."""
    import csv as csvlib, io
    result = run(["sample_inputs/sample_normal.txt", "--today", TODAY, "--format", "csv"])
    failures = []
    check("exit code", result.returncode, 0, failures)

    # Extract CSV block (lines after the summary block)
    lines = result.stdout.splitlines()
    csv_start = next(
        (i for i, l in enumerate(lines) if l.startswith("#,")),
        None,
    )
    if csv_start is None:
        failures.append("  CSV header row not found in output")
        return report("CSV output format", False, failures)

    csv_text = "\n".join(lines[csv_start:])
    rows = list(csvlib.reader(io.StringIO(csv_text)))
    check("header columns", len(rows[0]), 5, failures)
    check("data rows", len(rows) - 1, 6, failures)   # 6 action items
    return report("CSV output format", not failures, failures)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    print(f"Running tests against {SCRIPT}\n")
    cases = [
        test_normal_case,
        test_edge_case,
        test_cautious_case,
        test_relative_dates,
        test_csv_format,
    ]
    results = [fn() for fn in cases]
    print(f"\n{sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
