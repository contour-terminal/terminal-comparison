# Terminal emulator comparison

Unicode, VT sequence and GUI feature comparison across terminal emulators.
Measurements are reproducible: see [README.md](README.md).

## How this was produced

- **linux** — 2026-07-19 11:54:50 +0200, `Linux-7.1.3-201.fc44.x86_64-x86_64-with-glibc2.43`
  - ucs-detect pinned at `ea4510a4bc6e`, patches: `0001-vs15-must-not-narrow.patch` (076283770c66aa4f)
  - arguments: `--probe-silently --no-final-summary --limit-category-time 240 --detect-all-dec-modes`

### Terminals measured

| Terminal | Version | Platform | Display | Status | Run time |
|---|---|---|---|---|---|
| Contour | `0.7.0-lead-out-1269f24a` | linux | x11 | ok | 30.5s |
| kitty | `0.47.1` | linux | x11 | ok | 95.6s |
| Ghostty | `1.3.1` | linux | x11 | ok | 7.0s |
| WezTerm | `wezterm 20260716_195552_76b606ec` | linux | x11 | ok | 43.5s |
| Konsole | `26.04.3` | linux | x11 | ok | 4.0s |
| GNOME Terminal (VTE) | `3.60.0` | linux | x11 | ok | 54.5s |
| Alacritty | `0.17.0` | linux | x11 | ok | 7.0s |
| xterm | `406` | linux | x11 | ok | 4.5s |
| foot | `1.27.0` | linux | wayland | ok | 5.5s |

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
| Sixel graphics | yes | no | no | yes | yes | yes | no | no | yes |
| Kitty graphics protocol | yes | yes | yes | no | yes | yes | no | no | no |
| Kitty keyboard protocol | yes | yes | yes | yes | ? | ? | ? | yes | ? |
| Kitty clipboard (OSC 5522) | yes | yes | no | no | no | no | no | no | no |
| Kitty notifications | yes | yes | no | no | no | no | no | no | no |
| Kitty pointer shapes (OSC 22) | yes | yes | no | no | no | no | no | no | no |
| OSC 52 clipboard | yes | yes | yes | yes | yes | no | no | no | no |
| Styled underlines (CSI 4:x) | yes | yes | yes | yes | yes | no | no | no | no |
| Underline colour (SGR 58) | yes | yes | yes | yes | yes | no | no | no | no |
| DECRQSS (request selection or setting) | yes | yes | yes | yes | yes | no | yes | no | yes |
| DECRQCRA (checksum of rectangular area) | yes | no | no | no | no | no | no | no | yes |

**Caveats**

- **Sixel graphics** — xterm gates Sixel on its *graphics* ID rather than its terminal ID, and ships with it off. The harness now starts xterm with `decGraphicsID: vt340`, which enables Sixel without dropping the terminal below VT420 and losing the rectangular operations, so xterm's row reflects what it can do rather than what it does out of the box.
- **OSC 52 clipboard** — Detected by what the terminal advertises -- DA1 extension 52 and the XTGETTCAP `Ms` capability -- not by writing to the clipboard, which would raise a permission prompt. A terminal that implements OSC 52 without advertising it, or that ships it disabled for security reasons, therefore reads as "no".
- **Styled underlines (CSI 4:x)** — Asked through XTGETTCAP, so this measures whether the terminal *advertises* the capability, not whether it draws a curly underline. Several terminals that render them -- VTE, Konsole and Alacritty among the ones measured here -- do not answer the capability query, and the documented matrix records them as supporting the feature. Read a "no" as "not advertised".
- **Underline colour (SGR 58)** — Asked through XTGETTCAP, with the same caveat as styled underlines: this is what the terminal advertises, not what it renders.
- **DECRQCRA (checksum of rectangular area)** — xterm gates this on two things at once (charproc.c:5612): a VT420 terminal level, which is already its default, and `AllowWindowOps(ewGetChecksum)`, which is not. The harness now starts xterm with `allowWindowOps: true` and xterm answers. Note also that the reply's final byte is contested -- xterm answers `* y`, not `$ y` -- so a probe written against the other reading can still record a false negative.

### DEC private modes (DECRQM)

`n/a` marks a terminal that answers no DECRQM at all, which is a fact about it rather than a gap in the measurement: Konsole can set and reset modes but never report one, so no mode row can be filled in for it by query. The documented matrix below covers those features instead.

| Mode | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm |
|---|---|---|---|---|---|---|---|---|---|
| 2027 — Grapheme clustering | yes | no | yes | yes | yes | n/a | no | no | no |
| 2026 — Synchronized output | yes | yes | yes | yes | yes | n/a | no | yes | no |
| 2048 — In-band resize notification | yes | yes | yes | yes | no | n/a | no | no | no |
| 2004 — Bracketed paste | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| 1049 — Alternate screen buffer | yes | yes | yes | yes | no | n/a | yes | yes | yes |
| 7 — Auto-wrap (DECAWM) | yes | yes | yes | yes | yes | n/a | yes | yes | yes |

### Mouse reporting modes (DECRQM)

| Mode | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm |
|---|---|---|---|---|---|---|---|---|---|
| `9` — X10 compatibility mouse reporting | yes | no | yes | no | no | n/a | yes | no | yes |
| `1000` — VT200 mouse — report button press and release | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1001` — Highlight mouse tracking | yes | no | no | no | no | n/a | yes | no | yes |
| `1002` — Button-event tracking (motion while pressed) | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1003` — Any-event tracking (motion always) | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1004` — Focus in/out events | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1005` — UTF-8 extended coordinates | yes | yes | yes | no | yes | n/a | no | yes | yes |
| `1006` — SGR extended coordinates | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1007` — Alternate-scroll mode | yes | no | yes | yes | no | n/a | yes | yes | yes |
| `1015` — urxvt extended coordinates | yes | no | yes | yes | no | n/a | no | no | yes |
| `1016` — SGR-pixel coordinates | yes | yes | yes | yes | yes | n/a | no | no | yes |
| `2029` — Passive mouse tracking (Contour extension) | yes | no | no | no | no | n/a | no | no | no |

- **2029** — Lets an application receive mouse position without taking the mouse away from the user's selection. Contour's own extension; no other terminal implements it yet.

## Page memory and the DEC locator (measured by probe)

Neither is a DEC private mode, so DECRQM cannot answer for them. These rows come from `harness/vt_probe.py`, which uses the sequence inside the terminal and reads the reply.

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm |
|---|---|---|---|---|---|---|---|---|---|
| DECXCPR (extended cursor position report) | yes | yes | no | no | no | no | yes | no | yes |
| Reports a page number | yes | no | no | no | no | no | yes | no | yes |
| DEC page memory (more than one page) | yes | no | no | no | no | no | no | no | no |
| Pages reached | 15 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| NP / PP (next and preceding page) | yes | no | no | no | no | no | no | no | no |
| DEC locator (DECELR / DECRQLP) | yes | no | no | no | no | no | no | no | no |
| Locator reports a position | yes | no | no | no | no | no | no | no | no |
| DECRLM actually moves the cursor leftwards | no | no | no | no | no | no | no | no | no |

**Caveats**

- **Reports a page number** — A terminal can answer DECXCPR without the third (page) parameter. That is recorded here as "no": it answers the report but has no page memory to describe.
- **DEC page memory (more than one page)** — Confirmed by moving with PPA and asking DECXCPR which page the cursor is on, so a terminal that accepts PPA and ignores it is not counted.
- **Pages reached** — The walk stops at 32, well above any implementation found, and the probe records whether it hit that ceiling. Contour reaches 15, which matches its source exactly: MaxPageCount is 16 and the last index is reserved for the alternate screen, leaving 15 DEC-addressable pages. An earlier ceiling of 8 understated it, and the number here was the probe's limit rather than the terminal's.
- **DEC locator (DECELR / DECRQLP)** — A terminal with no locator answers nothing at all. xterm's case is a build option, not a runtime one: OPT_DEC_LOCATOR is `#undef` by default in xtermcfg.h and needs `--enable-dec-locator` at configure time, so a stock xterm has no locator code compiled in and its "no" is correct for the binary measured here, while the documented row records that the implementation exists in the source.
- **Locator reports a position** — DECLRP with Pe=0 means "locator unavailable" -- the sequence is implemented but no pointing device answered. Under a headless display that is the expected reply, so this row separates "implements the locator" from "a device was there".
- **DECRLM actually moves the cursor leftwards** — Functional, not declarative. The probe writes one Hebrew letter from column 40 with DECRLM (mode 34) reset and again with it set, and compares the cursor advance. Only a reversal counts: +1 then -1 is honoured, +1 then +1 means the mode is recognised and does nothing. Measuring both directions also proves the terminal was answering DSR 6 at all, so a "no" here cannot be a silent timeout.

### Every DEC private mode any terminal supports

105 modes, collected from the measurements rather than a hand-kept list. Modes that no terminal recognised are omitted.

| Mode | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm |
|---|---|---|---|---|---|---|---|---|---|
| `1` — Cursor Keys Mode | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `2` — ANSI/VT52 Mode | yes | no | no | no | yes | n/a | yes | no | yes |
| `3` — Column Mode | yes | yes | yes | no | yes | n/a | yes | no | yes |
| `4` — Scrolling Mode | yes | no | yes | no | no | n/a | no | no | yes |
| `5` — Screen Mode (light or dark screen) | yes | yes | yes | yes | no | n/a | yes | no | yes |
| `6` — Origin Mode | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `7` — Auto Wrap Mode | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `8` — Auto Repeat Mode | yes | yes | yes | no | no | n/a | yes | no | no |
| `9` — Interlace Mode / Mouse X10 tracking | yes | no | yes | no | no | n/a | yes | no | yes |
| `10` — Editing Mode / Show toolbar (rxvt) | yes | no | no | no | no | n/a | no | no | no |
| `12` — Katakana Shift Mode / Blinking cursor (xterm) | yes | no | yes | yes | yes | n/a | no | yes | yes |
| `13` — Space Compression/Field Delimiter Mode / Start blinking cursor (xterm) | no | no | no | no | no | n/a | no | no | yes |
| `14` — Transmit Execution Mode / Enable XOR of blinking cursor control (xterm) | no | no | no | no | no | n/a | no | no | yes |
| `18` — Print Form Feed | yes | no | no | no | no | n/a | no | no | yes |
| `19` — Printer Extent | yes | no | no | no | no | n/a | no | no | yes |
| `25` — Text Cursor Enable Mode | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `30` — Show scrollbar (rxvt) | yes | no | no | no | no | n/a | no | no | yes |
| `34` — Cursor Right to Left Mode | yes | no | no | no | no | n/a | no | no | no |
| `35` — Hebrew (Keyboard) Mode / Enable font-shifting functions (rxvt) | yes | no | no | no | no | n/a | no | no | yes |
| `36` — Hebrew Encoding Mode | yes | no | no | no | no | n/a | no | no | no |
| `38` — Tektronix 4010/4014 Mode | no | no | no | no | no | n/a | no | no | yes |
| `40` — Carriage Return/New Line Mode / Allow 80⇒132 mode (xterm) | yes | no | yes | no | no | n/a | yes | no | yes |
| `41` — Unidirectional Print Mode / more(1) fix (xterm) | yes | no | no | no | no | n/a | no | no | yes |
| `42` — National Replacement Character Set Mode | yes | no | no | no | no | n/a | no | no | yes |
| `44` — Graphics Print Color Mode / Turn on margin bell (xterm) | no | no | no | no | no | n/a | no | no | yes |
| `45` — Graphics Print Color Syntax / Reverse-wraparound mode (xterm) | yes | no | yes | yes | yes | n/a | no | no | yes |
| `46` — Graphics Print Background Mode / Start logging (xterm) | yes | no | no | no | no | n/a | no | no | no |
| `47` — Graphics Rotated Print Mode / Use Alternate Screen Buffer (xterm) | yes | no | yes | yes | no | n/a | yes | no | yes |
| `57` — Greek/N-A Keyboard Mapping Mode | yes | no | no | no | no | n/a | no | no | no |
| `59` — Kanji/Katakana Display Mode | no | no | no | no | no | n/a | yes | no | no |
| `61` — Vertical Cursor Coupling Mode | yes | no | no | no | no | n/a | yes | no | no |
| `64` — Page Cursor Coupling Mode | yes | no | no | no | no | n/a | yes | no | no |
| `66` — Numeric Keypad Mode | yes | no | yes | yes | no | n/a | yes | no | yes |
| `67` — Backarrow Key Mode | yes | no | no | no | no | n/a | no | no | yes |
| `68` — Keyboard Usage Mode | yes | no | no | no | no | n/a | no | no | no |
| `69` — Vertical Split Screen Mode / DECLRMM - Left Right Margin Mode | yes | no | yes | no | yes | n/a | yes | no | yes |
| `73` — Transmission Rate Limiting | yes | no | no | no | no | n/a | no | no | no |
| `80` — Sixel Display Mode | yes | no | no | yes | yes | n/a | yes | no | yes |
| `81` — Key Position Mode | yes | no | no | no | no | n/a | no | no | no |
| `95` — No Clearing Screen on Column Change Mode | yes | no | no | no | no | n/a | no | no | no |
| `96` — Right to Left Copy Mode | yes | no | no | no | no | n/a | no | no | no |
| `97` — CRT Save Mode | yes | no | no | no | no | n/a | no | no | no |
| `98` — Auto Resize Mode | yes | no | no | no | no | n/a | no | no | no |
| `99` — Modem Control Mode | yes | no | no | no | no | n/a | no | no | no |
| `100` — Auto Answerback Mode | yes | no | no | no | no | n/a | no | no | no |
| `101` — Conceal Answerback Message Mode | yes | no | no | no | no | n/a | no | no | no |
| `102` — Ignore Null Mode | yes | no | no | no | no | n/a | no | no | no |
| `103` — Half Duplex Mode | yes | no | no | no | no | n/a | no | no | no |
| `104` — Secondary Keyboard Language Mode | yes | no | no | no | no | n/a | no | no | no |
| `106` — Overscan Mode | yes | no | no | no | no | n/a | no | no | no |
| `112` — Review Previous Lines Mode | no | no | no | no | no | n/a | yes | no | no |
| `1000` — Send Mouse X & Y on button press | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1001` — Use Hilite Mouse Tracking | yes | no | no | no | no | n/a | yes | no | yes |
| `1002` — Use Cell Motion Mouse Tracking | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1003` — Use All Motion Mouse Tracking | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1004` — Send FocusIn/FocusOut events | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1005` — Enable UTF-8 Mouse Mode | yes | yes | yes | no | yes | n/a | no | yes | yes |
| `1006` — Enable SGR Mouse Mode | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `1007` — Enable Alternate Scroll Mode | yes | no | yes | yes | no | n/a | yes | yes | yes |
| `1010` — Scroll to bottom on tty output | no | no | no | no | no | n/a | no | no | yes |
| `1011` — Scroll to bottom on key press | no | no | no | no | no | n/a | no | no | yes |
| `1014` — Enable fastScroll resource | no | no | no | no | no | n/a | no | no | yes |
| `1015` — Enable urxvt Mouse Mode | yes | no | yes | yes | no | n/a | no | no | yes |
| `1016` — Enable SGR Mouse PixelMode | yes | yes | yes | yes | yes | n/a | no | no | yes |
| `1021` — Bold/italic implies high intensity | no | no | no | no | no | n/a | yes | no | no |
| `1034` — Interpret "meta" key | no | no | no | yes | no | n/a | no | no | yes |
| `1035` — Enable special modifiers for Alt and NumLock keys | no | no | yes | yes | no | n/a | no | no | yes |
| `1036` — Send ESC when Meta modifies a key | no | no | yes | yes | no | n/a | yes | no | yes |
| `1037` — Send DEL from the editing-keypad Delete key | no | no | no | no | no | n/a | no | no | yes |
| `1039` — Send ESC when Alt modifies a key | no | no | yes | no | no | n/a | no | no | yes |
| `1040` — Keep selection even if not highlighted | no | no | no | no | no | n/a | no | no | yes |
| `1041` — Use the CLIPBOARD selection | no | no | no | no | no | n/a | no | no | yes |
| `1042` — Enable Urgency window manager hint when Control-G is received | no | no | no | yes | no | n/a | no | yes | yes |
| `1043` — Enable raising of the window when Control-G is received | no | no | no | no | no | n/a | no | no | yes |
| `1044` — Reuse the most recent data copied to CLIPBOARD | no | no | no | no | no | n/a | no | no | yes |
| `1045` — Extended Reverse-wraparound mode (XTREVWRAP2) | yes | no | yes | no | no | n/a | no | no | yes |
| `1046` — Enable switching to/from Alternate Screen Buffer | no | no | no | no | no | n/a | yes | no | yes |
| `1047` — Use Alternate Screen Buffer | yes | no | yes | yes | no | n/a | yes | no | yes |
| `1048` — Save cursor as in DECSC | yes | no | yes | no | no | n/a | yes | no | yes |
| `1049` — Save cursor as in DECSC and use alternate screen buffer | yes | yes | yes | yes | no | n/a | yes | yes | yes |
| `1050` — Set terminfo/termcap function-key mode | no | no | no | no | no | n/a | no | no | yes |
| `1051` — Set Sun function-key mode | no | no | no | no | no | n/a | no | no | yes |
| `1060` — Set legacy keyboard emulation, i.e, X11R6 | no | no | no | no | no | n/a | no | no | yes |
| `1061` — Set VT220 keyboard emulation | no | no | no | no | no | n/a | no | no | yes |
| `1070` — Use private color registers for each graphic | yes | no | no | yes | yes | n/a | yes | no | yes |
| `1243` — Arrow keys swapping (BiDi) | no | no | no | no | no | n/a | yes | no | no |
| `2001` — Enable readline mouse button-1 | no | no | no | no | no | n/a | no | no | yes |
| `2002` — Enable readline mouse button-2 | no | no | no | no | no | n/a | no | no | yes |
| `2003` — Enable readline mouse button-3 | no | no | no | no | no | n/a | no | no | yes |
| `2004` — Set bracketed paste mode | yes | yes | yes | yes | yes | n/a | yes | yes | yes |
| `2005` — Enable readline character-quoting | no | no | no | no | no | n/a | no | no | yes |
| `2006` — Enable readline newline pasting | no | no | no | no | no | n/a | no | no | yes |
| `2026` — Synchronized Output | yes | yes | yes | yes | yes | n/a | no | yes | no |
| `2027` — Grapheme Clustering | yes | no | yes | yes | yes | n/a | no | no | no |
| `2028` — Text reflow | yes | no | no | no | no | n/a | no | no | no |
| `2029` — Passive Mouse Tracking | yes | no | no | no | no | n/a | no | no | no |
| `2030` — Report grid cell selection | yes | no | no | no | no | n/a | no | no | no |
| `2031` — Color palette updates | yes | yes | yes | yes | no | n/a | yes | no | no |
| `2048` — In-Band Window Resize Notifications | yes | yes | yes | yes | no | n/a | no | no | no |
| `2500` — Mirror box drawing characters | no | no | no | no | no | n/a | yes | no | no |
| `2501` — BiDi autodetection | no | no | no | no | no | n/a | yes | no | no |
| `5522` — Bracketed Paste MIME | yes | yes | no | no | no | n/a | no | no | no |
| `8452` — Sixel scrolling leaves cursor to right of graphic | yes | no | no | yes | yes | n/a | no | no | yes |
| `9001` — win32-input-mode | yes | no | no | no | yes | n/a | no | no | no |
| `737769` — Input Method Editor (IME) mode | ? | no | ? | yes | ? | n/a | ? | ? | ? |

## Modes a terminal declares but does not honour

DECRQM reports what a terminal *recognises*; a functional probe reports what it *does*. Where this report has both for the same feature, the two are compared. A terminal listed here answers a mode query affirmatively and then does not act on the mode -- which is the one failure a mode query cannot detect by construction, and is worse for an application than an honest "not recognised", because there is nothing left to test.

| Mode | Terminal | DECRQM says | Behaviour |
|---|---|---|---|
| `34` — DECRLM (right-to-left mode) | Contour | supported | not honoured |

- Declaring DECRLM tells an application it may rely on right-to-left layout. A terminal that answers DECRQM affirmatively and then advances the cursor rightwards is worse than one that answers "not recognised", because the application has no way to find out.

## Where measurement and documentation disagree

8 of the features covered by both a runtime probe and the documented matrix disagree. Every case runs the same way — the source says yes, the running terminal says no — and each has a reason worth knowing. Some are **shipped disabled**: xterm and Alacritty gate OSC 52 behind a setting. The rest are **implemented but not advertised**: the underline probes ask XTGETTCAP, and VTE, Konsole and Alacritty draw styled underlines perfectly well without answering the capability query. Two former entries are gone because the harness now launches xterm correctly — Sixel is gated on its graphics ID and DECRQCRA on a window-op permission, neither of which is a conformance level. Where they still differ, the documented column is the better guide to what the terminal can do, and the measured column to what it will admit to.

| Feature | Terminal | Measured | Documented |
|---|---|---|---|
| OSC 52 clipboard set/query | Alacritty | no | yes |
| OSC 52 clipboard set/query | xterm | no | yes |
| SGR 58/59 underline color | Konsole | no | yes |
| SGR 58/59 underline color | GNOME Terminal (VTE) | no | yes |
| SGR 58/59 underline color | Alacritty | no | yes |
| Extended underline styles via CSI 4:Ps m (curly/dotted/dashed/double) | Konsole | no | yes |
| Extended underline styles via CSI 4:Ps m (curly/dotted/dashed/double) | GNOME Terminal (VTE) | no | yes |
| Extended underline styles via CSI 4:Ps m (curly/dotted/dashed/double) | Alacritty | no | yes |

## VT sequences and extensions (documented)

Compiled from each terminal's source tree and documentation rather than measured, so it also covers terminals this machine cannot run. Where a row overlaps the measured tables above -- the DEC mode rows especially -- the two were derived independently and can be read against each other.

### Colors

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 24-bit true color (SGR 38;2 / 48;2) | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? |
| OSC 4/10/11 dynamic palette, foreground, background color (set + query) | yes | yes | yes | yes | yes | partial | yes | yes | yes | yes | yes | yes | ? |
| DECSCUSR set cursor style | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? |
| Extended underline styles via CSI 4:Ps m (curly/dotted/dashed/double) | yes | yes | yes | yes | yes | yes | yes | yes | no | yes | yes | yes | ? |
| SGR 58/59 underline color | yes | yes | yes | yes | yes | yes | yes | yes | no | yes | yes | yes | ? |

### Graphics

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sixel graphics | yes | no | no | yes | yes | yes | partial | no | yes | yes | yes | yes | ? |
| iTerm2 inline images (OSC 1337 File=) | yes | no | no | ? | yes | yes | no | no | no | no | ? | yes | ? |
| Kitty graphics protocol | yes | yes | yes | no | yes | yes | no | no | no | no | ? | no | ? |
| ReGIS vector graphics | yes | no | no | no | no | no | no | no | yes | no | no | no | ? |

### Hyperlinks

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OSC 8 hyperlinks | yes | yes | yes | yes | yes | partial | yes | yes | no | yes | yes | yes | ? |
| OSC 52 clipboard set/query | yes | yes | yes | yes | yes | partial | no | yes | yes | partial | yes | partial | ? |
| Kitty clipboard protocol (OSC 5522) | yes | yes | no | no | no | no | no | no | no | no | no | no | ? |

### Input

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Kitty keyboard protocol | yes | yes | yes | yes | yes | yes | no | yes | no | yes | no | no | ? |
| xterm modifyOtherKeys | yes | no | yes | yes | yes | no | no | no | yes | no | yes | yes | ? |
| Bracketed paste | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? |
| Focus in/out reporting | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? |
| SGR extended mouse reporting | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? |
| SGR-Pixel mouse reporting | yes | yes | yes | yes | yes | yes | no | no | yes | no | yes | no | ? |
| DEC locator (DECELR / DECSLE / DECRQLP) | yes | no | no | no | no | no | no | no | partial | no | yes | no | ? |
| X10 mouse reporting (mode 9) | yes | no | yes | no | no | no | yes | no | yes | no | yes | no | ? |
| VT200 mouse reporting (mode 1000) | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? |
| Highlight mouse tracking (mode 1001) | partial | no | no | no | no | no | partial | no | yes | no | no | no | ? |
| Button-event tracking (mode 1002) | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? |
| Any-event tracking (mode 1003) | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? |
| SGR-pixel coordinates (mode 1016) | yes | yes | yes | yes | yes | yes | partial | no | yes | no | yes | yes | ? |
| Passive mouse tracking (mode 2029) | yes | no | no | no | no | no | partial | no | no | no | no | no | ? |

### Other

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DECSCL (select conformance level) | yes | yes | no | no | no | no | yes | no | yes | no | yes | yes | ? |
| DECRQM (request DEC/ANSI mode) | yes | yes | partial | yes | yes | no | yes | yes | yes | yes | yes | yes | ? |
| DECRQCRA (checksum of rectangular area) | yes | no | no | no | partial | partial | partial | no | yes | partial | yes | yes | ? |
| Rectangular area ops (DECCRA copy / DECFRA fill / DECERA erase) | yes | no | no | yes | no | no | yes | no | yes | yes | yes | yes | ? |
| Scroll margins — DECSTBM (top/bottom) and DECLRMM (left/right) | yes | partial | yes | partial | yes | partial | yes | partial | yes | yes | yes | yes | ? |
| DECSCA (select character protection attribute) | yes | no | yes | no | no | no | yes | no | yes | yes | yes | yes | ? |
| OSC 22 mouse pointer shape | yes | yes | yes | yes | no | no | no | no | yes | no | yes | no | ? |
| XTGETTCAP (request termcap/terminfo string) | yes | no | yes | yes | yes | no | no | no | yes | no | no | yes | ? |

### Shell

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OSC 7 current working directory | yes | yes | yes | yes | yes | no | yes | no | no | yes | yes | yes | ? |
| OSC 133 semantic prompt marks | yes | yes | yes | yes | yes | yes | yes | no | no | yes | no | yes | ? |
| Desktop notifications (OSC 9 / OSC 777) | yes | yes | yes | yes | yes | partial | no | no | no | partial | no | partial | ? |

### Unicode

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DEC mode 2027 (grapheme clustering) | yes | partial | yes | yes | yes | no | no | no | no | partial | partial | no | ? |
| DEC mode 2026 (synchronized/batched output) | yes | yes | yes | yes | yes | yes | no | yes | no | yes | yes | yes | ? |
| Kitty text-sizing protocol (OSC 66) | yes | yes | yes | partial | no | no | no | no | no | no | no | no | ? |
| DECDWL / DECDHL (double-width / double-height lines) | yes | no | no | no | yes | yes | no | no | yes | yes | yes | yes | ? |

### Window

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| In-band window resize notifications (DEC mode 2048) | yes | yes | yes | yes | no | no | no | no | no | no | no | yes | ? |
| XTWINOPS window manipulation | yes | partial | partial | partial | partial | partial | partial | partial | yes | partial | yes | yes | ? |
| DECSLPP (set lines per page) | no | no | no | no | no | no | yes | no | yes | no | yes | yes | ? |
| Alternate screen buffer (DEC private modes 47 / 1047 / 1049) | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? |
| DEC page memory (more than one page) | yes | no | no | no | no | no | no | no | no | yes | no | no | ? |
| DECXCPR (extended cursor position report) | yes | partial | no | no | no | no | yes | no | yes | yes | partial | yes | ? |

## GUI and user-facing features (documented)

Compiled from official documentation and source.

### Accessibility

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Screen-reader / a11y support | yes | no | partial | no | no | yes | yes | no | no | yes | no | partial | partial |
| Caret (cursor) position reporting to a11y APIs | yes | no | partial | no | no | yes | yes | no | no | yes | no | ? | ? |

### Config

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Configuration format | YAML (contour.yml) | Custom key-value kitty.conf | Custom flat key = value text format | INI (foot.ini, [section] key=value) | Lua (~/.wezterm.lua) | KConfig INI-style (konsolerc + per-profile .profile files) | GSettings/dconf (binary key-value database under the org.gnome.Terminal schema), not a text config file | TOML (alacritty.toml) | X resources (~/.Xresources, app-defaults / XrmDatabase) | JSON (settings.json) | Flat key=value text file (.minttyrc) | plist (native Preferences); profiles also as Dynamic Profiles JSON/XML | Property List (.plist / .terminal) |
| Live config reload | yes | yes | yes | no | yes | yes | yes | yes | no | yes | partial | yes | no |
| GUI settings panel | yes | partial | no | no | no | yes | yes | no | partial | yes | yes | yes | yes |
| Per-profile settings | yes | partial | no | partial | partial | yes | yes | no | no | yes | yes | yes | yes |
| Theming / colour-scheme support | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |

### Interaction

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Search in scrollback | yes | yes | yes | yes | yes | yes | yes | yes | no | yes | yes | yes | yes |
| URL/hyperlink click | yes | yes | yes | partial | yes | yes | yes | yes | partial | yes | yes | yes | yes |
| Copy-on-select | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | no |
| Rectangular (block) selection | yes | yes | yes | yes | yes | yes | yes | yes | partial | yes | yes | yes | yes |
| Mouse reporting toggles | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| IME / dead-key support | yes | yes | yes | yes | yes | yes | yes | partial | yes | yes | yes | yes | yes |
| Keyboard-driven vi mode / copy mode | yes | partial | partial | no | yes | no | no | yes | no | partial | partial | yes | no |

### Layout

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tabs | yes | yes | yes | no | yes | yes | yes | no | no | yes | yes | yes | yes |
| Split panes | yes | yes | yes | no | yes | yes | no | no | no | yes | no | yes | yes |
| Tab/pane detach & reorder | yes | yes | yes | no | partial | yes | yes | no | no | yes | partial | yes | partial |
| Quake/dropdown mode | no | yes | yes | no | no | no | no | no | no | yes | yes | yes | no |
| Fullscreen mode | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |

### Other

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sixel image display | yes | no | no | yes | yes | yes | partial | no | yes | yes | yes | yes | no |
| Kitty graphics protocol support | yes | yes | yes | no | yes | partial | no | no | no | no | no | partial | no |
| Desktop notification support | yes | yes | yes | yes | yes | yes | partial | no | partial | yes | partial | yes | no |
| Ligature-aware cursor rendering | ? | yes | yes | no | partial | yes | no | no | no | yes | yes | yes | no |
| Blurred background / transparency | yes | yes | yes | yes | yes | yes | no | partial | no | yes | partial | yes | yes |
| Tab colouring | yes | yes | partial | no | yes | yes | no | no | no | yes | partial | yes | no |
| Undercurl / styled underlines | yes | yes | yes | yes | yes | yes | yes | yes | no | yes | yes | yes | no |

### Platform

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Linux/X11 | yes | yes | yes | no | yes | yes | yes | yes | yes | no | no | no | no |
| Linux/Wayland | yes | yes | yes | yes | yes | yes | yes | yes | no | no | no | no | no |
| macOS | yes | yes | yes | no | yes | partial | no | yes | partial | no | no | yes | yes |
| Windows | yes | no | no | no | yes | partial | no | yes | no | yes | yes | no | no |
| BSD | yes | yes | partial | partial | yes | yes | yes | yes | yes | no | no | no | no |

### Rendering

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GPU-accelerated rendering | yes | yes | yes | no | yes | no | partial | yes | no | yes | no | yes | no |
| GPU rendering API | Qt RHI (OpenGL, Vulkan, Metal, or Direct3D 11, selected by Qt's backend at runtime) | OpenGL 3.1+ (Linux, w/ extensions) / OpenGL 3.3 core (macOS) | Metal (macOS), OpenGL 4.3+ (Linux/BSD), WebGL (wasm) | none (software rendering via pixman + Wayland shm buffers) | OpenGL (default); optional WebGpu via wgpu (Vulkan/Metal/DX12); Software fallback | none - CPU/software rasterization via QWidget+QPainter (Qt raster paint engine) | GTK4 GSK scene graph (OpenGL 'NGL' renderer; Vulkan by default on Wayland since GTK 4.16) | OpenGL 3.3 core (GLES 2.0 fallback) | none (Xlib/Xft, CPU-rendered) | Direct3D 11 (AtlasEngine) | None — GDI raster (CPU); DirectWrite only for glyph-existence probing | Metal | none (CoreGraphics/CoreText, CPU) |
| Font ligatures | yes | yes | yes | no | yes | yes | partial | no | no | yes | yes | yes | partial |
| Bitmap/emoji font support | yes | yes | yes | yes | yes | yes | yes | partial | partial | yes | yes | yes | yes |
| Subpixel (LCD) antialiasing | yes | no | no | yes | yes | partial | partial | no | yes | yes | yes | partial | no |
| Variable font support | ? | yes | yes | ? | partial | ? | yes | yes | ? | yes | ? | ? | ? |

### Session

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Shell integration (semantic prompt marks) | yes | yes | yes | yes | yes | yes | yes | no | no | yes | partial | yes | partial |
| Session restore | no | partial | partial | no | partial | yes | no | no | no | yes | no | yes | yes |
| Remote/SSH integration | yes | yes | yes | no | yes | yes | no | no | no | partial | no | yes | partial |
| Built-in multiplexer (detachable, tmux-like) | no | no | no | no | yes | no | no | no | no | no | no | partial | no |

## Licence

Apache-2.0. Results and report generated by the harness in this repository.
