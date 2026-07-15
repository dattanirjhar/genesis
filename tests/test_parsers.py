"""
Parser regression tests.

For every fixture in tests/fixtures/<tool>/, assert that:
  - the detector routes it to the expected tool,
  - parsing yields at least the expected number of findings,
  - every finding carries exactly the canonical field set.

sqlmap is a stub (routing only). Run from the project root:

    python -m tests.test_parsers
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parser.canonical import CANONICAL_FIELDS  # noqa: E402
from parser.detector import detect_tool  # noqa: E402
from parser.parser import parse_file  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# tool -> minimum findings expected. None = detection only (stub parser).
EXPECT = {
    "nmap": 2, "nuclei": 1, "nikto": 1, "whatweb": 1, "amass": 1,
    "katana": 1, "httpx": 1, "gobuster": 1, "subfinder": 1, "sqlmap": None,
}


def main() -> int:
    failures = []
    for tool, min_findings in EXPECT.items():
        samples = sorted((FIXTURES / tool).glob("sample.*"))
        if not samples:
            print(f"  FAIL  {tool}: no fixture")
            failures.append(tool)
            continue
        src = samples[0]

        detected, _ = detect_tool(src)
        if detected != tool:
            print(f"  FAIL  {tool}: detected as '{detected}'")
            failures.append(tool)
            continue

        if min_findings is None:
            print(f"  PASS  {tool}: routes correctly (stub parser)")
            continue

        doc = parse_file(src)
        n = len(doc["findings"])
        schema_ok = all(set(f) == set(CANONICAL_FIELDS) for f in doc["findings"])
        if n >= min_findings and schema_ok:
            print(f"  PASS  {tool}: {n} finding(s), schema OK")
        else:
            print(f"  FAIL  {tool}: findings={n} (>= {min_findings}?), schema_ok={schema_ok}")
            failures.append(tool)

    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print(f"ALL {len(EXPECT)} PARSERS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
