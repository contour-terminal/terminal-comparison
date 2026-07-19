# terminal-comparison

Unicode, VT sequence and GUI feature comparison across terminal emulators — measured,
not asserted.

**[→ Read the report](https://contour-terminal.github.io/terminal-comparison/)**

Every number in the report is produced by the harness in this repository, from a
recorded run whose provenance (tool commit, arguments, terminal versions, platform) is
committed alongside the results. Re-running it should reproduce the table.

---

## Why this exists

Terminal feature comparisons are usually tables of claims. This one is a table of
measurements: each terminal is launched off-screen, driven through
[ucs-detect](https://github.com/jquast/ucs-detect), and asked — via Cursor Position
Reports and DEC mode queries — what it actually did. Where a fact cannot be measured
(a GUI feature, or a terminal that does not run on the measuring machine) it is marked
as *documented* rather than *measured*, and cited.

## A correction to the measurement tool

The VS15 test in upstream ucs-detect asserts the opposite of the specification, and
this repository pins a patched oracle.

Variation Selector-15 (`U+FE0E`) selects *text* presentation.
[terminal-unicode-core](https://github.com/contour-terminal/terminal-unicode-core) draws
an explicit asymmetry between the two selectors: VS16 "will force the grapheme cluster's
width to be 2, which may possibly cause reflowing of that symbol to the next line",
whereas VS15 "will **NOT** change the underlying width but only change the display to
prefer textual non-colored presentation".

The reason is mechanical rather than stylistic. A terminal reaches the selector only
after the base character has been placed and the cursor advanced. Growing a cluster
needs more room, which a terminal can still take. Shrinking one means giving a column
back — un-wrapping a line that has already wrapped, un-scrolling content that has
already left the screen — so a terminal that narrows on VS15 ends up with behaviour no
application can predict.

Upstream's table contains only bases that are wide by default, and expected width 1 for
all of them. That inverts the result: a conforming terminal scores 0%, and a terminal is
rewarded for the forbidden behaviour. Measured against xterm 406, which has no
grapheme-clustering mode and can therefore only report the unchanged width:

| ucs-detect | xterm VS15 |
| --- | --- |
| upstream `ea4510a` | 0 / 158 — every entry recorded `measured_by_terminal: 2` against `measured_by_wcwidth: 1` |
| with `patches/0001-vs15-must-not-narrow.patch` | 158 / 158 |

The patch makes the expectation the base character's own width, resolved per sequence
rather than fixed for the table. The correction was
[pointed out by J4James](https://github.com/contour-terminal/contour/pull/2004) on a
Contour pull request; Contour itself narrowed on VS15 until that review, so this is a
correction the project applied to its own terminal as well as to the tool.

The same change is on a branch against upstream, ready to be proposed:
[`christianparpart/ucs-detect@fix/vs15-does-not-narrow`](https://github.com/christianparpart/ucs-detect/tree/fix/vs15-does-not-narrow).
This repository keeps the patch form regardless, so a run is reproducible from the pinned
upstream commit whether or not the change is ever merged.

With the corrected oracle, four of the ten terminals measured here narrow on VS15 — foot,
Ghostty and kitty on every sequence tested, Rio on all but a handful — and two combine
grapheme clustering with the specified behaviour (Contour and WezTerm). Under the old
oracle those verdicts were exactly reversed, which is the point.

## Reproducing a run

Requirements: Python 3.11+, and on Linux `Xvfb`, `weston`, `dbus-run-session`,
`xdpyinfo`.

```sh
git clone https://github.com/contour-terminal/terminal-comparison
cd terminal-comparison

./harness/setup-ucs-detect.sh          # clone pinned ucs-detect, apply patches, venv
python3 harness/terminals.py           # what is installed on this machine
python3 harness/run_ucs_detect.py --outdir results/linux
python3 harness/make_report.py         # regenerate REPORT.md and docs/index.html
```

To measure a Contour build other than the one on `PATH`:

```sh
CONTOUR_BIN=/path/to/contour python3 harness/run_ucs_detect.py --outdir results/linux
```

Useful flags: `--only <key>` (repeatable), `--test-only vs15`, `--all` (full Unicode
tables instead of the contested subset), `--no-languages`, `--all-dec-modes` (probe every
known DEC private mode rather than the notable subset — this is what fills the mode
tables), `--no-vt-probe`.

Note that `--test-only` skips terminal fingerprinting entirely, so a run made with it
produces **no** capability or DEC-mode data, only Unicode scores.

### What gets measured, and how

| Asked by | Covers |
| --- | --- |
| ucs-detect width measurement | Wide, narrow, VS15, VS16, ZWJ, flags, skin tone, languages |
| ucs-detect capability probes | Sixel, kitty graphics/keyboard/clipboard, OSC 52, underline styles, DECRQSS … |
| DECRQM (`--all-dec-modes`) | ~158 DEC private modes, including every mouse-reporting protocol from X10 (9) through SGR-pixel (1016), and Contour's passive mouse tracking (2029) |
| `harness/vt_probe.py` | DEC page memory, the DEC locator, right-to-left cursor movement, Glyph Protocol |

### Where a terminal is not measured at its defaults

One terminal is deliberately not launched with stock settings, because doing so produced a
table that was simply wrong about it.

**xterm** is started with `decGraphicsID: vt340` and `allowWindowOps: true`. Its defaults
understate it in two independent ways, and neither is a conformance level:

- **Sixel** is gated on the *graphics* ID, which is separate from the terminal ID. Raising
  `decGraphicsID` to vt340 enables Sixel without dropping the terminal below VT420 and
  losing the rectangular operations — the two are not in conflict, which is easy to
  assume.
- **DECRQCRA** is gated on two things at once (`charproc.c:5612`): a VT420 terminal level,
  which is already xterm's default, *and* `AllowWindowOps(ewGetChecksum)`, which is not.

With stock settings xterm reports neither, and anyone who knows xterm would rightly
discard the whole table on sight. With these two resources it reports both.

There is a third case the harness cannot fix from the command line: xterm's **DEC locator**
sits behind `#if OPT_DEC_LOCATOR`, which `xtermcfg.h` ships as `#undef` and which needs
`--enable-dec-locator` at *configure* time. A stock xterm binary has no locator compiled
in, so its measured "no" is correct for the binary tested, while the documented matrix
records that the implementation exists in the source.

The general rule: where a terminal ships a capability disabled, the measured table says
what it does and the documented table says what it can do, and the caveats name which.

### What DECRQM cannot answer

These exist because page memory, the locator, right-to-left movement and Glyph Protocol
are **not** DEC private modes, so DECRQM cannot answer for them. The probe uses the
sequences instead: it asks DECXCPR (`CSI ? 6 n`) whether the reply carries a page number,
moves with PPA and NP/PP and re-asks to confirm the cursor actually changed page, and
enables the locator with DECELR before requesting a position with DECRQLP. Each probe
restores what it changed, and each read is bounded by a timeout, because a terminal
without the sequence simply says nothing. The raw replies are kept in the JSON so a
verdict can be re-checked by hand.

### Glyph Protocol

[Glyph Protocol](https://rapha.land/introducing-glyph-protocol-for-terminals/) lets an
application ship a vector glyph to the terminal at runtime and render it from a Private
Use Area codepoint, instead of asking the user to install a patched font. It is new — v1.0
in April 2026, v1.9 by May — and [Rio](https://rioterm.com/), whose author designed it, is
so far the only implementation. Its [spec](https://github.com/raphamorim/rio/blob/main/specs/glyph-protocol.md)
lives in the Rio tree.

It is measured in two parts, because they can disagree:

- **Detection** is the protocol's own `s` verb, `ESC _ 25a1 ; s ESC \`, whose reply is
  defined to be how an application finds out. The messages ride on APC, which a terminal
  is required to ignore when it does not recognise them, so a terminal without the
  protocol answers nothing and that silence is the "no" — the same reading every other
  probe here gives silence. The reply's `fmt=` list is printed rather than reduced to
  yes/no, because *which* payload formats a terminal accepts is the answer to the
  question.
- **Whether a registration is actually stored** is a separate row, on the same principle
  as the DECRLM behaviour check: the probe registers a 29-byte `glyf` triangle at
  U+100000, then asks the `q` verb who covers that codepoint and counts it only when the
  answer names `glossary`. U+100000 is chosen because no known font covers it, so the
  coverage reply cannot be a system font answering in the registration's place. A terminal
  that acknowledged the registration and kept nothing would pass the first row and fail
  this one. The slot is cleared again afterwards.

The `glyf` payload is built by hand in `vt_probe.py` rather than sliced out of a font,
because the probe may not import anything outside the standard library — and 29 bytes of
TrueType is cheaper to write than a dependency.

### How the measurement is isolated

| Mechanism | Why |
| --- | --- |
| Xvfb / weston-in-Xvfb | Runs off-screen and independent of the operator's session. |
| Private D-Bus session | GNOME Terminal, Konsole and Ghostty are single-instance apps; without it the command is handed to an already-running instance on the real display and nothing is measured. |
| Private `XDG_CONFIG_HOME` | Each terminal starts from its own defaults, so numbers describe the shipped configuration. |
| Software rendering | There is no GPU behind Xvfb; GPU-accelerated terminals otherwise exit before running the command. |
| Sentinel exit-status file | Terminals that fork or hand off to a server exit immediately, which would otherwise look like a finished run. |

Wayland uses weston's **x11** backend nested inside Xvfb rather than its headless
backend: the headless backend advertises no `wl_seat`, and clients such as foot abort
with *"no seats available"*.

## Contributing measurements from macOS and Windows

Windows Terminal, Mintty, iTerm2 and Terminal.app cannot be measured on Linux, so
their rows are empty. Filling them needs someone to run the harness on that platform:

```sh
./harness/setup-ucs-detect.sh
python3 harness/run_ucs_detect.py --outdir results/macos      # or results/windows
python3 harness/make_report.py
```

then open a pull request with the new `results/<platform>/` directory. The report
generator picks up any `results/*/run-summary.json` automatically.

The launch definitions for those platforms are in `harness/terminals.py` and are marked
`verified=False`: they were written from each terminal's documented CLI but have not yet
been executed there. Expect to correct them, and please do so in the pull request —
on macOS the two Apple-ecosystem terminals need AppleScript rather than argv, which is
scaffolded but not implemented.

## Layout

```
harness/            measurement and report generation
  terminals.py        registry: one row per terminal, per platform
  display.py          off-screen display servers (Linux)
  run_ucs_detect.py   the driver
  vt_probe.py         probes what DECRQM cannot answer; runs inside the terminal
  make_report.py      results + data -> REPORT.md and docs/index.html
  curated.py          loads data/, normalising YAML's yes/no-as-boolean trap
  validate_data.py    gate: every row covers every terminal, with evidence
  compare_runs.py     compare two runs to show a result is reproducible
  setup-ucs-detect.sh
patches/            corrections applied to the pinned measurement tool
data/               curated matrices and the definition of what gets reported
results/<platform>/ recorded runs: one YAML and one probe JSON per terminal,
                    plus run-summary.json
docs/               the published site (GitHub Pages)
REPORT.md           the same report as markdown
```

`data/` holds the parts that cannot be measured: `vt-features.yaml` and
`gui-features.yaml` are curated from source trees and official documentation, with an
evidence pointer per verdict, and `measured-capabilities.yaml` decides which probes and
DEC modes the report surfaces, along with the caveats printed beneath them.

## Reading the tables honestly

- A **dash** in a measured capability row can mean *not supported*, *not enabled in the
  default configuration*, or *the probe asked the wrong question*. Known instances of
  the latter two are called out as caveats in the report rather than left to imply
  absence — for example xterm answers the Sixel probe only when started at an emulation
  level that enables it, and the DECRQCRA reply's final byte is contested.
- **Unicode percentages are not a ranking of quality.** They measure agreement with one
  width model on one contested subset. A terminal targeting a different Unicode version,
  or deliberately not implementing grapheme clustering, will score lower without being
  wrong for its own goals.
- **Documented rows are weaker evidence than measured ones.** They are cited, but they
  are a reading of source and docs at a point in time.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
