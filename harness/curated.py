#!/usr/bin/env python3
"""Loading and normalisation for the curated matrices in data/.

One wrinkle deserves its own module.  In YAML 1.1 the bare words `yes` and `no` are
*booleans*, not strings, so a perfectly natural-looking row:

    support:
      contour: yes
      xterm: no

parses as `True` / `False`.  Demanding quotes everywhere would be a trap that fires
silently every time someone edits the file by hand, so the verdicts are normalised on
load instead: booleans map to "yes"/"no", strings are lower-cased, and anything
unrecognised is preserved so the validator can complain about it by name.
"""
from __future__ import annotations

import pathlib

import yaml

VERDICTS = ("yes", "no", "partial", "unknown")


def normalize_verdict(value) -> str:
    """Map a raw YAML verdict onto the closed verdict set."""
    if value is True:
        return "yes"
    if value is False:
        return "no"
    if value is None:
        return "unknown"
    text = str(value).strip().lower()
    aliases = {
        "true": "yes", "y": "yes", "supported": "yes",
        "false": "no", "n": "no", "unsupported": "no", "none": "no",
        "partially": "partial", "some": "partial",
        "?": "unknown", "": "unknown",
    }
    return aliases.get(text, text)


def load_matrix(path: pathlib.Path) -> list[dict]:
    """Load one curated matrix, with its support verdicts normalised."""
    if not path.exists():
        return []
    rows = yaml.safe_load(path.read_text()) or []
    if not isinstance(rows, list):
        return rows
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("support"), dict):
            row["support"] = {k: normalize_verdict(v)
                              for k, v in row["support"].items()}
    return rows
