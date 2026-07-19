# Terminal emulator comparison

Unicode, VT sequence and GUI feature comparison across terminal emulators.
Measurements are reproducible: see [README.md](README.md).

## How this was produced

- **linux** — 2026-07-19 10:40:20 +0200, `Linux-7.1.3-201.fc44.x86_64-x86_64-with-glibc2.43`
  - ucs-detect pinned at `ea4510a4bc6e`, patches: `0001-vs15-must-not-narrow.patch` (076283770c66aa4f)
  - arguments: `--probe-silently --no-final-summary --limit-category-time 240`

### Terminals measured

| Terminal | Version | Platform | Display | Status | Run time |
|---|---|---|---|---|---|
| Contour | `0.7.0-lead-out-1269f24a` | linux | x11 | ok | 30.0s |
| kitty | `0.47.1` | linux | x11 | ok | 94.6s |
| Ghostty | `1.3.1` | linux | x11 | ok | 4.5s |
| WezTerm | `wezterm 20260716_195552_76b606ec` | linux | x11 | ok | 41.0s |
| Konsole | `26.04.3` | linux | x11 | ok | 2.0s |
| GNOME Terminal (VTE) | `3.60.0` | linux | x11 | ok | 48.0s |
| Alacritty | `0.17.0` | linux | x11 | ok | 4.5s |
| xterm | `406` | linux | x11 | ok | 4.0s |
| foot | `1.27.0` | linux | wayland | ok | 3.0s |

### Not measured here

| Terminal | Why |
|---|---|
| Windows Terminal | Windows only. Run the harness on Windows to fill this row. |
| Mintty | Cygwin/MSYS2 on Windows. Run the harness there to fill this row. |
| iTerm2 | macOS only. Driven through AppleScript; run the harness on macOS. |
| Terminal.app | macOS only. Driven through AppleScript; run the harness on macOS. |

These rows are filled by running the same harness on macOS or Windows and committing the results; see README.md.

## Unicode support (measured)

Each cell is the share of measurements whose cursor advance matched the expected column width. Higher is better.

| Terminal | Wide | Narrow | VS16 | VS15 | ZWJ | Flags (RI) | Lone RI | Skin tone | **Overall** |
|---|---|---|---|---|---|---|---|---|---|
| Contour | 100.0% | 92.5% | 97.2% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | **99.1%** |
| Ghostty | 99.8% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | **94.7%** |
| kitty | 100.0% | 87.7% | 97.9% | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | **93.7%** |
| Konsole | 72.7% | 93.0% | 100.0% | 100.0% | 96.0% | 100.0% | 100.0% | 100.0% | **93.1%** |
| foot | 94.9% | 93.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0.0% | 100.0% | **92.6%** |
| WezTerm | 94.9% | 92.5% | 50.0% | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | **90.7%** |
| xterm | 94.9% | 95.7% | 50.0% | 100.0% | 0.7% | 100.0% | 0.0% | 100.0% | **43.3%** |
| Alacritty | 94.9% | 87.2% | 50.0% | 100.0% | 0.7% | 100.0% | 0.0% | 100.0% | **42.8%** |
| GNOME Terminal (VTE) | 54.9% | 93.0% | 50.0% | 100.0% | 0.7% | 100.0% | 0.0% | 100.0% | **36.5%** |

- **Wide** — Characters that must occupy two columns.
- **Narrow** — Characters that must occupy exactly one column.
- **VS16** — Emoji presentation selector. VS16 may promote a cluster to two columns, so the expectation is a width of 2.
- **VS15** — Text presentation selector. VS15 must NOT change the cluster's width, so a wide base is still expected to measure 2. See the VS15 section of the report.
- **ZWJ** — Zero-width-joiner emoji sequences, which must measure as a single cluster.
- **Flags (RI)** — Regional-indicator pairs forming flag emoji.
- **Lone RI** — A single regional indicator, with no pair to join.
- **Skin tone** — Fitzpatrick skin-tone modifiers applied to a base emoji.

## Capabilities (measured by probe)

Answered by the terminal during the run. A dash can mean *not supported*, *not enabled by default*, or *the probe asked the wrong question* — caveats are noted beneath the table.

| Capability | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm |
|---|---|---|---|---|---|---|---|---|---|
| Sixel graphics | yes | no | no | yes | yes | yes | no | no | no |
| Kitty graphics protocol | yes | yes | yes | no | yes | yes | no | no | no |
| Kitty keyboard protocol | yes | yes | yes | yes | ? | ? | ? | yes | ? |
| Kitty clipboard (OSC 5522) | yes | yes | no | no | no | no | no | no | no |
| Kitty notifications | yes | yes | no | no | no | no | no | no | no |
| Kitty pointer shapes (OSC 22) | yes | yes | no | no | no | no | no | no | no |
| OSC 52 clipboard | yes | yes | yes | yes | yes | no | no | no | no |
| Styled underlines (CSI 4:x) | yes | yes | yes | yes | yes | no | no | no | no |
| Underline colour (SGR 58) | yes | yes | yes | yes | yes | no | no | no | no |
| DECRQSS (request selection or setting) | yes | yes | yes | yes | yes | no | yes | no | yes |
| DECRQCRA (checksum of rectangular area) | yes | no | no | no | no | no | no | no | no |

**Caveats**

- **Sixel graphics** — xterm implements Sixel but answers this probe only when started with an emulation level that enables it (for example `-ti vt340`); the harness starts it with defaults, so its "no" reflects the default configuration, not a missing implementation.
- **OSC 52 clipboard** — Several terminals ship OSC 52 disabled by default for security reasons, so a "no" here may be policy rather than absence.
- **DECRQCRA (checksum of rectangular area)** — The reply's final byte is contested: xterm answers `* y`, and a probe expecting `$ y` records a false negative. Treat a "no" here as unconfirmed rather than absent.

### DEC private modes (DECRQM)

| Mode | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm |
|---|---|---|---|---|---|---|---|---|---|
| 2027 — Grapheme clustering | yes | no | yes | yes | yes | ? | no | no | no |
| 2026 — Synchronized output | yes | yes | yes | yes | yes | ? | no | yes | no |
| 2048 — In-band resize notification | yes | yes | yes | yes | no | ? | no | no | no |
| 2004 — Bracketed paste | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| 1004 — Focus in/out events | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| 1006 — SGR mouse reporting | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| 1016 — SGR-pixel mouse reporting | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| 1049 — Alternate screen buffer | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| 7 — Auto-wrap (DECAWM) | ? | ? | ? | ? | ? | ? | ? | ? | ? |

## Licence

Apache-2.0. Results and report generated by the harness in this repository.
