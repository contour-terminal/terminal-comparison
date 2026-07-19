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
tables instead of the contested subset), `--no-languages`.

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
harness/          measurement and report generation
  terminals.py      registry: one row per terminal, per platform
  display.py        off-screen display servers (Linux)
  run_ucs_detect.py the driver
  make_report.py    results + data -> REPORT.md and docs/index.html
  setup-ucs-detect.sh
patches/          corrections applied to the pinned measurement tool
data/             curated matrices and the definition of what gets reported
results/<platform>/  recorded runs, one YAML per terminal, plus run-summary.json
docs/             the published site (GitHub Pages)
REPORT.md         the same report as markdown
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
