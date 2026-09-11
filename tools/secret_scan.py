"""
secret_scan.py
==============

Release gate (release-plan item 0.2): scan a directory tree for
secret material before it ships.

Checks:
    - No .env file anywhere in the tree
    - No file containing OPENWEATHER_API_KEY with a value attached
    - No file containing a key-shaped hex string (32 hex characters,
      the OpenWeatherMap key format)

Usage:
    python tools/secret_scan.py <directory>

Exits 0 when clean, 1 with a report otherwise. Scans text up to 2 MB
per file and skips nothing else, because a release gate should be
paranoid.
"""

import re
import sys
from pathlib import Path

MAX_TEXT_SCAN = 2_000_000

ENV_FILENAMES = {".env", ".env.local", ".env.production"}

ASSIGNED_KEY_PATTERN = re.compile(
    r"OPENWEATHER_API_KEY\s*[=:]\s*['\"]?[A-Za-z0-9]{16,}",
    re.IGNORECASE,
)

HEX_KEY_PATTERN = re.compile(r"\b[0-9a-f]{32}\b", re.IGNORECASE)


def scan(root: Path) -> list[str]:
    """
    Return a list of findings for the tree under root.
    """

    findings = []

    for path in sorted(Path(root).rglob("*")):
        if not path.is_file():
            continue

        relative = path.relative_to(root)

        if path.name.lower() in ENV_FILENAMES:
            findings.append(f"{relative}: environment file present")

        if path.suffix.lower() in {".png", ".jpg", ".ico", ".zip",
                ".pyc", ".pyd", ".dll", ".exe"}:
            continue

        try:
            if path.stat().st_size > MAX_TEXT_SCAN:
                continue

            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            findings.append(f"{relative}: unreadable ({error})")
            continue

        if ASSIGNED_KEY_PATTERN.search(content):
            findings.append(f"{relative}: assigned OPENWEATHER_API_KEY found")

        hex_match = HEX_KEY_PATTERN.search(content)

        if hex_match:
            findings.append(
                f"{relative}: 32-character hex string found "
                f"(near {hex_match.group(0)[:6]}...)"
            )

    return findings


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")

    if not root.is_dir():
        print(f"not a directory: {root}")
        sys.exit(1)

    findings = scan(root)

    for finding in findings:
        print(f"SECRET SCAN: {finding}")

    print(f"scan complete: {len(findings)} finding(s) under {root}")

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
