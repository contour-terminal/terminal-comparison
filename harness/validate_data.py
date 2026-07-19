#!/usr/bin/env python3
"""Check the curated matrices before they are published.

The measured tables cannot really be wrong -- they are whatever the terminals
answered.  The curated ones can, so they get a gate:

* every row covers every terminal, so a missing key never renders as a silent blank
* verdicts come from a closed set, so a typo cannot become a new category
* every non-`unknown` verdict carries an evidence pointer, because a claim about
  someone else's terminal should say where it came from

Exits non-zero on any problem.  Run:  python3 harness/validate_data.py
"""
from __future__ import annotations

import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"

sys.path.insert(0, str(HERE))
from curated import load_matrix, VERDICTS as _VERDICTS  # noqa: E402
from terminals import TERMINALS  # noqa: E402

VERDICTS = set(_VERDICTS)
ALL_KEYS = {t.key for t in TERMINALS}
CURATED = ("vt-features.yaml", "gui-features.yaml")


def check_file(name: str) -> list[str]:
    """Return a list of problems found in one curated matrix."""
    path = DATA / name
    if not path.exists():
        return [f"{name}: missing"]

    try:
        rows = load_matrix(path)
    except yaml.YAMLError as error:
        return [f"{name}: not valid YAML: {error}"]

    if not isinstance(rows, list):
        return [f"{name}: expected a list of rows, got {type(rows).__name__}"]

    problems: list[str] = []
    seen_ids: set[str] = set()

    for index, row in enumerate(rows):
        where = f"{name}[{index}]"
        if not isinstance(row, dict):
            problems.append(f"{where}: expected a mapping")
            continue

        row_id = row.get("id")
        where = f"{name}:{row_id or index}"
        for required in ("id", "name", "category"):
            if not row.get(required):
                problems.append(f"{where}: missing '{required}'")
        if row_id in seen_ids:
            problems.append(f"{where}: duplicate id")
        seen_ids.add(row_id)

        support, values = row.get("support"), row.get("values")
        if (support is None) == (values is None):
            problems.append(f"{where}: needs exactly one of 'support' or 'values'")
            continue

        table = support if support is not None else values
        if not isinstance(table, dict):
            problems.append(f"{where}: 'support'/'values' must be a mapping")
            continue

        missing = ALL_KEYS - set(table)
        if missing:
            problems.append(f"{where}: no verdict for {', '.join(sorted(missing))}")
        unexpected = set(table) - ALL_KEYS
        if unexpected:
            problems.append(f"{where}: unknown terminal {', '.join(sorted(unexpected))}")

        if support is None:
            continue

        bad = {k: v for k, v in table.items() if v not in VERDICTS}
        if bad:
            problems.append(f"{where}: verdicts outside {sorted(VERDICTS)}: {bad}")

        evidence = row.get("evidence") or {}
        unsourced = sorted(
            key for key, verdict in table.items()
            if verdict in ("yes", "no", "partial")
            and key in ALL_KEYS and not evidence.get(key)
        )
        if unsourced:
            problems.append(
                f"{where}: verdict without evidence for {', '.join(unsourced)}")

    return problems


def main() -> int:
    problems: list[str] = []
    for name in CURATED:
        problems.extend(check_file(name))

    if problems:
        print(f"{len(problems)} problem(s) in the curated data:\n", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    print(f"curated data OK ({', '.join(CURATED)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
