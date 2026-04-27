#!/usr/bin/env python3
"""
run_tests.py
------------
Validates parse_actions.py against all three sample inputs.

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
TODAY = "2026-04-26"

CASES = [
    {
        "name": "normal case",
        "input": "sample_inputs/sample_normal.txt",
        "expected_total": 6,
        "expected_warnings": 2,
        "expected_clean": 4,
        "expected_exit": 0,
    },
    {
        "name": "edge case",
        "input": "sample_inputs/sample_edge.txt",
        "expected_total": 6,
        "expected_warnings": 6,
        "expected_clean": 0,
        "expected_exit": 0,
    },
    {
        "name": "cautious case (no action items)",
        "input": "sample_inputs/sample_cautious.txt",
        "expected_total": 0,
        "expected_warnings": 0,
        "expected_clean": 0,
        "expected_exit": 0,
    },
]


def run_case(case: dict) -> bool:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), case["input"], "--today", TODAY],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    output = result.stdout
    passed = True
    failures = []

    def check(label, actual, expected):
        nonlocal passed
        if actual != expected:
            passed = False
            failures.append(f"  {label}: expected {expected}, got {actual}")

    # Parse summary block
    total = warnings = clean = None
    for line in output.splitlines():
        if "Total items found:" in line:
            total = int(line.split(":")[-1].strip().lstrip("*").rstrip("*"))
        elif "Items with warnings:" in line:
            warnings = int(line.split(":")[-1].strip().lstrip("*").rstrip("*"))
        elif "Items with no warnings:" in line:
            clean = int(line.split(":")[-1].strip().lstrip("*").rstrip("*"))

    check("total items", total, case["expected_total"])
    check("items with warnings", warnings, case["expected_warnings"])
    check("items with no warnings", clean, case["expected_clean"])
    check("exit code", result.returncode, case["expected_exit"])

    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {case['name']}")
    for f in failures:
        print(f)
    return passed


def main():
    print(f"Running {len(CASES)} test cases against {SCRIPT}\n")
    results = [run_case(c) for c in CASES]
    print(f"\n{sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
