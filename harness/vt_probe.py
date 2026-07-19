#!/usr/bin/env python3
"""Probe VT features that DECRQM cannot answer, from inside the terminal.

DEC private modes are easy: DECRQM asks and the terminal answers, which is how the
mouse modes and mode 2027 get measured.  Page memory and the DEC locator are not modes,
so the only way to find out whether a terminal has them is to use them and look at what
comes back.

This script runs *inside* the terminal under test, on its tty, and writes JSON.  It only
uses the standard library so it needs no virtualenv.

  python3 vt_probe.py --out /path/to/result.json

Every probe restores what it changed.  A terminal that does not implement a sequence
usually answers nothing at all, so each read is bounded by a timeout and a missing reply
is recorded as unsupported rather than hanging the run.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import select
import sys
import termios
import tty

TIMEOUT = 0.6


class Tty:
    """The terminal's tty in raw mode, with bounded request/response."""

    def __init__(self, fd: int):
        self.fd = fd
        self.saved = termios.tcgetattr(fd)

    def __enter__(self) -> "Tty":
        tty.setraw(self.fd)
        return self

    def __exit__(self, *_exc) -> None:
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.saved)

    def write(self, text: str) -> None:
        os.write(self.fd, text.encode("ascii"))

    def drain(self) -> None:
        """Discard anything already pending, so a reply cannot be mistaken."""
        while select.select([self.fd], [], [], 0.0)[0]:
            try:
                if not os.read(self.fd, 4096):
                    break
            except OSError:
                break

    def ask(self, request: str, final: str, timeout: float = TIMEOUT) -> str:
        """Send *request*; collect the reply up to and including a byte in *final*.

        Returns "" when the terminal says nothing, which is the normal answer from a
        terminal that does not implement the sequence.
        """
        self.drain()
        self.write(request)
        out: list[str] = []
        while True:
            ready = select.select([self.fd], [], [], timeout)[0]
            if not ready:
                break
            try:
                chunk = os.read(self.fd, 1)
            except OSError:
                break
            if not chunk:
                break
            char = chunk.decode("latin-1")
            out.append(char)
            if char in final:
                break
            if len(out) > 256:
                break
        return "".join(out)


def probe_pages(term: Tty) -> dict:
    """Probe DEC page memory: DECXCPR, and whether PPA can reach a second page.

    DECXCPR (`CSI ? 6 n`) answers `CSI ? Pr ; Pc ; Pp R` -- the third parameter is the
    page number, and its presence is what distinguishes a terminal with page memory from
    one that only knows DSR 6.  A terminal can still report a page number and have only
    one page, so the second half moves to page 2 with PPA and asks again.
    """
    result: dict = {
        "decxcpr": False, "reports_page": False,
        "multiple_pages": False, "pages_reachable": 1, "raw": {},
    }

    reply = term.ask("\x1b[?6n", "R")
    result["raw"]["decxcpr"] = repr(reply)
    match = re.match(r"\x1b\[\??(\d+);(\d+)(?:;(\d+))?R", reply)
    if not match:
        return result
    result["decxcpr"] = True
    if match.group(3) is None:
        # Answers DECXCPR but without a page parameter: no page memory.
        return result
    result["reports_page"] = True
    home_page = int(match.group(3))

    # Walk forward with PPA (`CSI Pn SP P`) and believe only what DECXCPR confirms.
    reachable = 1
    for page in range(2, 9):
        term.write(f"\x1b[{page} P")
        confirm = term.ask("\x1b[?6n", "R")
        seen = re.match(r"\x1b\[\??(\d+);(\d+)(?:;(\d+))?R", confirm)
        if not (seen and seen.group(3) and int(seen.group(3)) == page):
            break
        reachable = page
    result["pages_reachable"] = reachable
    result["multiple_pages"] = reachable >= 2

    term.write(f"\x1b[{home_page} P")   # restore
    return result


def probe_locator(term: Tty) -> dict:
    """Probe the DEC locator: DECELR to enable, DECRQLP to ask for a position.

    A terminal with no locator answers nothing.  One that has the sequence but no
    pointing device answers DECLRP with Pe=0 ("locator unavailable"), which is still
    evidence that the locator is implemented.
    """
    result = {"decrqlp": False, "locator_available": False, "raw": {}}

    term.write("\x1b[1;0'z")                      # DECELR: enable, character cells
    reply = term.ask("\x1b[1'|", "w")             # DECRQLP: request position
    result["raw"]["decrqlp"] = repr(reply)
    match = re.match(r"\x1b\[(\d+)(?:;(\d+))*&w", reply)
    if match:
        result["decrqlp"] = True
        result["locator_available"] = match.group(1) != "0"
    term.write("\x1b[0;0'z")                      # DECELR: disable
    term.drain()
    return result


def probe_page_sequences(term: Tty) -> dict:
    """Check that NP and PP move between pages, not just PPA."""
    result = {"np_pp": False, "raw": {}}
    before = term.ask("\x1b[?6n", "R")
    start = re.match(r"\x1b\[\??(\d+);(\d+)(?:;(\d+))?R", before)
    if not (start and start.group(3)):
        return result
    home = int(start.group(3))

    term.write("\x1b[1U")                          # NP: next page
    moved = term.ask("\x1b[?6n", "R")
    result["raw"]["after_np"] = repr(moved)
    seen = re.match(r"\x1b\[\??(\d+);(\d+)(?:;(\d+))?R", moved)
    if seen and seen.group(3) and int(seen.group(3)) != home:
        result["np_pp"] = True
        term.write("\x1b[1V")                      # PP: previous page
    term.write(f"\x1b[{home} P")
    term.drain()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    fd = os.open("/dev/tty", os.O_RDWR)
    results: dict = {}
    try:
        with Tty(fd) as term:
            results["pages"] = probe_pages(term)
            results["page_sequences"] = probe_page_sequences(term)
            results["locator"] = probe_locator(term)
    except Exception as error:           # a probe must never fail the whole run
        results["error"] = f"{type(error).__name__}: {error}"
    finally:
        os.close(fd)

    with open(args.out, "w") as handle:
        json.dump(results, handle, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
