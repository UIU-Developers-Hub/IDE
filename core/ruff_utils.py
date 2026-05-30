"""Shared helpers for Ruff linting and formatting."""

import logging
import re
import subprocess

logger = logging.getLogger(__name__)

STDIN_FILENAME = "code.py"
AUTOFIX_MARKER = re.compile(r"^\[[*\s]\]\s*")


def parse_diagnostic_output(output: str) -> list[dict]:
    """Parse Ruff/flake8-style diagnostic lines."""
    results = []
    for line in output.splitlines():
        parts = line.split(":", 3)
        if len(parts) < 4:
            continue
        try:
            line_no = int(parts[1])
        except ValueError:
            continue
        message = AUTOFIX_MARKER.sub("", parts[3].strip())
        results.append({"line": line_no, "message": message})
    return results


def run_ruff_check(code: str, select_fix: bool = False) -> tuple[str, str, int]:
    """Run ``ruff check`` on source code from stdin."""
    command = ["ruff", "check", "--stdin-filename", STDIN_FILENAME, "-"]
    if select_fix:
        command.insert(2, "--fix")

    process = subprocess.run(
        command,
        input=code,
        capture_output=True,
        text=True,
    )
    return process.stdout, process.stderr, process.returncode


def run_ruff_format(code: str) -> tuple[str, str, int]:
    """Run ``ruff format`` on source code from stdin."""
    process = subprocess.run(
        ["ruff", "format", "--stdin-filename", STDIN_FILENAME, "-"],
        input=code,
        capture_output=True,
        text=True,
    )
    return process.stdout, process.stderr, process.returncode


def run_ruff_import_sort(code: str) -> tuple[str, str, int]:
    """Sort imports with Ruff (isort rules)."""
    process = subprocess.run(
        [
            "ruff", "check",
            "--select", "I",
            "--fix",
            "--stdin-filename", STDIN_FILENAME,
            "-",
        ],
        input=code,
        capture_output=True,
        text=True,
    )
    # Fixed source is written to stdout when using stdin + --fix
    return process.stdout, process.stderr, process.returncode
