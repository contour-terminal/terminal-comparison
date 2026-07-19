#!/usr/bin/env python3
"""Compare two measurement runs, to show that a result is reproducible.

Cursor Position Report round-trips are timing-sensitive, so a run made while the
machine is busy can differ from a quiet one: a probe that times out ends its category
early and the terminal silently gets fewer measurements.  Comparing two runs catches
exactly that, and distinguishes it from a real behavioural difference:

* a change in **n_total** means the run was truncated -- a measurement artefact
* a change in **n_errors** at the same n_total means the terminal genuinely behaved
  differently

Run:  python3 harness/compare_runs.py results/linux other-run/
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

CATEGORIES = (
    "unicode_wide_results", "narrow_results", "emoji_vs16_results",
    "emoji_vs15_results", "emoji_zwj_results", "ri_results",
    "sri_results", "sfz_results",
)


def totals(doc: dict) -> dict[str, tuple[int, int]]:
    """Return {category: (n_total, n_errors)} for one ucs-detect document."""
    out = {}
    for key in CATEGORIES:
        section = (doc.get("test_results") or {}).get(key) or {}
        out[key] = (
            sum((v or {}).get("n_total", 0) for v in section.values()),
            sum((v or {}).get("n_errors", 0) for v in section.values()),
        )
    return out


def load(directory: pathlib.Path) -> dict[str, dict]:
    """Load every terminal YAML in a results directory."""
    return {path.stem: yaml.safe_load(path.read_text())
            for path in sorted(directory.glob("*.yaml"))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=pathlib.Path)
    parser.add_argument("right", type=pathlib.Path)
    args = parser.parse_args()

    left, right = load(args.left), load(args.right)
    shared = sorted(set(left) & set(right))
    if not shared:
        print("no terminals in common", file=sys.stderr)
        return 2

    only_left, only_right = sorted(set(left) - set(right)), sorted(set(right) - set(left))
    for label, keys in (("only in " + str(args.left), only_left),
                        ("only in " + str(args.right), only_right)):
        if keys:
            print(f"{label}: {', '.join(keys)}")

    truncations, differences = 0, 0
    for terminal in shared:
        lt, rt = totals(left[terminal]), totals(right[terminal])
        for category in CATEGORIES:
            (lt_total, lt_err), (rt_total, rt_err) = lt[category], rt[category]
            if lt_total != rt_total:
                truncations += 1
                print(f"  TRUNCATED {terminal:16} {category:22} "
                      f"n_total {lt_total} -> {rt_total}")
            elif lt_err != rt_err:
                differences += 1
                print(f"  DIFFERS   {terminal:16} {category:22} "
                      f"n_errors {lt_err} -> {rt_err}")

    print()
    print(f"{len(shared)} terminal(s) compared, {len(CATEGORIES)} categories each")
    if truncations:
        print(f"{truncations} truncated category/categories -- the runs are NOT "
              f"comparable; re-run on an idle machine")
    if differences:
        print(f"{differences} category/categories differ in errors at equal n_total "
              f"-- a real behavioural difference")
    if not truncations and not differences:
        print("identical: every category measured the same count with the same errors")
    return 1 if (truncations or differences) else 0


if __name__ == "__main__":
    sys.exit(main())
