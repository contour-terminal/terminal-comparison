# Terminal emulator comparison

Unicode, VT sequence and GUI feature comparison across terminal emulators.
Measurements are reproducible: see [README.md](README.md).

## How this was produced

- **linux** — 2026-07-19 10:50:54 +0200, `Linux-7.1.3-201.fc44.x86_64-x86_64-with-glibc2.43`
  - ucs-detect pinned at `ea4510a4bc6e`, patches: `0001-vs15-must-not-narrow.patch` (076283770c66aa4f)
  - arguments: `--probe-silently --no-final-summary --limit-category-time 240 --detect-all-dec-modes`

### Terminals measured

| Terminal | Version | Platform | Display | Status | Run time |
|---|---|---|---|---|---|
| Contour | `0.7.0-lead-out-1269f24a` | linux | x11 | ok | 30.5s |
| kitty | `0.47.1` | linux | x11 | ok | 94.1s |
| Ghostty | `1.3.1` | linux | x11 | ok | 4.5s |
| WezTerm | `wezterm 20260716_195552_76b606ec` | linux | x11 | ok | 42.0s |
| Konsole | `26.04.3` | linux | x11 | ok | 3.0s |
| GNOME Terminal (VTE) | `3.60.0` | linux | x11 | ok | 51.5s |
| Alacritty | `0.17.0` | linux | x11 | ok | 5.0s |
| xterm | `406` | linux | x11 | ok | 4.0s |
| foot | `1.27.0` | linux | wayland | ok | 3.5s |

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
| Styled underlines (CSI 4:x) | yes | yes | no | yes | yes | no | no | no | no |
| Underline colour (SGR 58) | yes | yes | no | yes | yes | no | no | no | no |
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
| 1016 — SGR-pixel mouse reporting | yes | yes | yes | yes | yes | ? | no | no | yes |
| 1049 — Alternate screen buffer | yes | yes | yes | yes | no | ? | yes | yes | yes |
| 7 — Auto-wrap (DECAWM) | yes | yes | yes | yes | yes | ? | yes | yes | yes |

### Every DEC private mode any terminal supports

105 modes, collected from the measurements rather than a hand-kept list. Modes that no terminal recognised are omitted.

| Mode | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm |
|---|---|---|---|---|---|---|---|---|---|
| `1` — Cursor Keys Mode | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `2` — ANSI/VT52 Mode | yes | no | no | no | yes | ? | yes | no | yes |
| `3` — Column Mode | yes | yes | yes | no | yes | ? | yes | no | yes |
| `4` — Scrolling Mode | yes | no | yes | no | no | ? | no | no | yes |
| `5` — Screen Mode (light or dark screen) | yes | yes | yes | yes | no | ? | yes | no | yes |
| `6` — Origin Mode | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `7` — Auto Wrap Mode | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `8` — Auto Repeat Mode | yes | yes | yes | no | no | ? | yes | no | no |
| `9` — Interlace Mode / Mouse X10 tracking | yes | no | yes | no | no | ? | yes | no | yes |
| `10` — Editing Mode / Show toolbar (rxvt) | yes | no | no | no | no | ? | no | no | no |
| `12` — Katakana Shift Mode / Blinking cursor (xterm) | yes | no | yes | yes | yes | ? | no | yes | yes |
| `13` — Space Compression/Field Delimiter Mode / Start blinking cursor (xterm) | no | no | no | no | no | ? | no | no | yes |
| `14` — Transmit Execution Mode / Enable XOR of blinking cursor control (xterm) | no | no | no | no | no | ? | no | no | yes |
| `18` — Print Form Feed | yes | no | no | no | no | ? | no | no | yes |
| `19` — Printer Extent | yes | no | no | no | no | ? | no | no | yes |
| `25` — Text Cursor Enable Mode | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `30` — Show scrollbar (rxvt) | yes | no | no | no | no | ? | no | no | yes |
| `34` — Cursor Right to Left Mode | yes | no | no | no | no | ? | no | no | no |
| `35` — Hebrew (Keyboard) Mode / Enable font-shifting functions (rxvt) | yes | no | no | no | no | ? | no | no | yes |
| `36` — Hebrew Encoding Mode | yes | no | no | no | no | ? | no | no | no |
| `38` — Tektronix 4010/4014 Mode | no | no | no | no | no | ? | no | no | yes |
| `40` — Carriage Return/New Line Mode / Allow 80⇒132 mode (xterm) | yes | no | yes | no | no | ? | yes | no | yes |
| `41` — Unidirectional Print Mode / more(1) fix (xterm) | yes | no | no | no | no | ? | no | no | yes |
| `42` — National Replacement Character Set Mode | yes | no | no | no | no | ? | no | no | yes |
| `44` — Graphics Print Color Mode / Turn on margin bell (xterm) | no | no | no | no | no | ? | no | no | yes |
| `45` — Graphics Print Color Syntax / Reverse-wraparound mode (xterm) | yes | no | yes | yes | yes | ? | no | no | yes |
| `46` — Graphics Print Background Mode / Start logging (xterm) | yes | no | no | no | no | ? | no | no | no |
| `47` — Graphics Rotated Print Mode / Use Alternate Screen Buffer (xterm) | yes | no | yes | yes | no | ? | yes | no | yes |
| `57` — Greek/N-A Keyboard Mapping Mode | yes | no | no | no | no | ? | no | no | no |
| `59` — Kanji/Katakana Display Mode | no | no | no | no | no | ? | yes | no | no |
| `61` — Vertical Cursor Coupling Mode | yes | no | no | no | no | ? | yes | no | no |
| `64` — Page Cursor Coupling Mode | yes | no | no | no | no | ? | yes | no | no |
| `66` — Numeric Keypad Mode | yes | no | yes | yes | no | ? | yes | no | yes |
| `67` — Backarrow Key Mode | yes | no | no | no | no | ? | no | no | yes |
| `68` — Keyboard Usage Mode | yes | no | no | no | no | ? | no | no | no |
| `69` — Vertical Split Screen Mode / DECLRMM - Left Right Margin Mode | yes | no | yes | no | yes | ? | yes | no | yes |
| `73` — Transmission Rate Limiting | yes | no | no | no | no | ? | no | no | no |
| `80` — Sixel Display Mode | yes | no | no | yes | yes | ? | yes | no | yes |
| `81` — Key Position Mode | yes | no | no | no | no | ? | no | no | no |
| `95` — No Clearing Screen on Column Change Mode | yes | no | no | no | no | ? | no | no | no |
| `96` — Right to Left Copy Mode | yes | no | no | no | no | ? | no | no | no |
| `97` — CRT Save Mode | yes | no | no | no | no | ? | no | no | no |
| `98` — Auto Resize Mode | yes | no | no | no | no | ? | no | no | no |
| `99` — Modem Control Mode | yes | no | no | no | no | ? | no | no | no |
| `100` — Auto Answerback Mode | yes | no | no | no | no | ? | no | no | no |
| `101` — Conceal Answerback Message Mode | yes | no | no | no | no | ? | no | no | no |
| `102` — Ignore Null Mode | yes | no | no | no | no | ? | no | no | no |
| `103` — Half Duplex Mode | yes | no | no | no | no | ? | no | no | no |
| `104` — Secondary Keyboard Language Mode | yes | no | no | no | no | ? | no | no | no |
| `106` — Overscan Mode | yes | no | no | no | no | ? | no | no | no |
| `112` — Review Previous Lines Mode | no | no | no | no | no | ? | yes | no | no |
| `1000` — Send Mouse X & Y on button press | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `1001` — Use Hilite Mouse Tracking | yes | no | no | no | no | ? | yes | no | yes |
| `1002` — Use Cell Motion Mouse Tracking | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `1003` — Use All Motion Mouse Tracking | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `1004` — Send FocusIn/FocusOut events | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `1005` — Enable UTF-8 Mouse Mode | yes | yes | yes | no | yes | ? | no | yes | yes |
| `1006` — Enable SGR Mouse Mode | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `1007` — Enable Alternate Scroll Mode | yes | no | yes | yes | no | ? | yes | yes | yes |
| `1010` — Scroll to bottom on tty output | no | no | no | no | no | ? | no | no | yes |
| `1011` — Scroll to bottom on key press | no | no | no | no | no | ? | no | no | yes |
| `1014` — Enable fastScroll resource | no | no | no | no | no | ? | no | no | yes |
| `1015` — Enable urxvt Mouse Mode | yes | no | yes | yes | no | ? | no | no | yes |
| `1016` — Enable SGR Mouse PixelMode | yes | yes | yes | yes | yes | ? | no | no | yes |
| `1021` — Bold/italic implies high intensity | no | no | no | no | no | ? | yes | no | no |
| `1034` — Interpret "meta" key | no | no | no | yes | no | ? | no | no | yes |
| `1035` — Enable special modifiers for Alt and NumLock keys | no | no | yes | yes | no | ? | no | no | yes |
| `1036` — Send ESC when Meta modifies a key | no | no | yes | yes | no | ? | yes | no | yes |
| `1037` — Send DEL from the editing-keypad Delete key | no | no | no | no | no | ? | no | no | yes |
| `1039` — Send ESC when Alt modifies a key | no | no | yes | no | no | ? | no | no | yes |
| `1040` — Keep selection even if not highlighted | no | no | no | no | no | ? | no | no | yes |
| `1041` — Use the CLIPBOARD selection | no | no | no | no | no | ? | no | no | yes |
| `1042` — Enable Urgency window manager hint when Control-G is received | no | no | no | yes | no | ? | no | yes | yes |
| `1043` — Enable raising of the window when Control-G is received | no | no | no | no | no | ? | no | no | yes |
| `1044` — Reuse the most recent data copied to CLIPBOARD | no | no | no | no | no | ? | no | no | yes |
| `1045` — Extended Reverse-wraparound mode (XTREVWRAP2) | yes | no | yes | no | no | ? | no | no | yes |
| `1046` — Enable switching to/from Alternate Screen Buffer | no | no | no | no | no | ? | yes | no | yes |
| `1047` — Use Alternate Screen Buffer | yes | no | yes | yes | no | ? | yes | no | yes |
| `1048` — Save cursor as in DECSC | yes | no | yes | no | no | ? | yes | no | yes |
| `1049` — Save cursor as in DECSC and use alternate screen buffer | yes | yes | yes | yes | no | ? | yes | yes | yes |
| `1050` — Set terminfo/termcap function-key mode | no | no | no | no | no | ? | no | no | yes |
| `1051` — Set Sun function-key mode | no | no | no | no | no | ? | no | no | yes |
| `1060` — Set legacy keyboard emulation, i.e, X11R6 | no | no | no | no | no | ? | no | no | yes |
| `1061` — Set VT220 keyboard emulation | no | no | no | no | no | ? | no | no | yes |
| `1070` — Use private color registers for each graphic | yes | no | no | yes | yes | ? | yes | no | yes |
| `1243` — Arrow keys swapping (BiDi) | no | no | no | no | no | ? | yes | no | no |
| `2001` — Enable readline mouse button-1 | no | no | no | no | no | ? | no | no | yes |
| `2002` — Enable readline mouse button-2 | no | no | no | no | no | ? | no | no | yes |
| `2003` — Enable readline mouse button-3 | no | no | no | no | no | ? | no | no | yes |
| `2004` — Set bracketed paste mode | yes | yes | yes | yes | yes | ? | yes | yes | yes |
| `2005` — Enable readline character-quoting | no | no | no | no | no | ? | no | no | yes |
| `2006` — Enable readline newline pasting | no | no | no | no | no | ? | no | no | yes |
| `2026` — Synchronized Output | yes | yes | yes | yes | yes | ? | no | yes | no |
| `2027` — Grapheme Clustering | yes | no | yes | yes | yes | ? | no | no | no |
| `2028` — Text reflow | yes | no | no | no | no | ? | no | no | no |
| `2029` — Passive Mouse Tracking | yes | no | no | no | no | ? | no | no | no |
| `2030` — Report grid cell selection | yes | no | no | no | no | ? | no | no | no |
| `2031` — Color palette updates | yes | yes | yes | yes | no | ? | yes | no | no |
| `2048` — In-Band Window Resize Notifications | yes | yes | yes | yes | no | ? | no | no | no |
| `2500` — Mirror box drawing characters | no | no | no | no | no | ? | yes | no | no |
| `2501` — BiDi autodetection | no | no | no | no | no | ? | yes | no | no |
| `5522` — Bracketed Paste MIME | yes | yes | no | no | no | ? | no | no | no |
| `8452` — Sixel scrolling leaves cursor to right of graphic | yes | no | no | yes | yes | ? | no | no | yes |
| `9001` — win32-input-mode | yes | no | no | no | yes | ? | no | no | no |
| `737769` — Input Method Editor (IME) mode | ? | no | ? | yes | ? | ? | ? | ? | ? |

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

## GUI and user-facing features (documented)

Compiled from official documentation and source.

### Accessibility

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Screen-reader / a11y support | yes | no | partial | no | no | yes | yes | no | no | ? | no | partial | ? |
| Caret (cursor) position reporting to a11y APIs | yes | no | partial | no | no | yes | yes | no | no | ? | no | ? | ? |

### Config

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Configuration format | YAML (contour.yml) | Custom key-value kitty.conf | Custom flat key = value text format | INI (foot.ini, [section] key=value) | Lua (~/.wezterm.lua) | KConfig INI-style (konsolerc + per-profile .profile files) | GSettings/dconf (binary key-value database under the org.gnome.Terminal schema), not a text config file | TOML (alacritty.toml) | X resources (~/.Xresources, app-defaults / XrmDatabase) | unknown | Flat key=value text file (.minttyrc) | plist (native Preferences); profiles also as Dynamic Profiles JSON/XML | unknown |
| Live config reload | yes | yes | yes | no | yes | yes | yes | yes | no | ? | partial | yes | ? |
| GUI settings panel | yes | partial | no | no | no | yes | yes | no | partial | ? | yes | yes | ? |
| Per-profile settings | yes | partial | no | partial | partial | yes | yes | no | no | ? | yes | yes | ? |
| Theming / colour-scheme support | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? | yes | yes | ? |

### Interaction

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Search in scrollback | yes | yes | yes | yes | yes | yes | yes | yes | no | ? | yes | yes | ? |
| URL/hyperlink click | yes | yes | yes | partial | yes | yes | yes | yes | partial | ? | yes | yes | ? |
| Copy-on-select | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? | yes | yes | ? |
| Rectangular (block) selection | yes | yes | yes | yes | yes | yes | yes | yes | partial | ? | yes | yes | ? |
| Mouse reporting toggles | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? | yes | yes | ? |
| IME / dead-key support | yes | yes | yes | yes | yes | yes | yes | partial | yes | ? | yes | yes | ? |
| Keyboard-driven vi mode / copy mode | yes | partial | partial | no | yes | no | no | yes | no | ? | partial | yes | ? |

### Layout

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tabs | yes | yes | yes | no | yes | yes | yes | no | no | ? | yes | yes | ? |
| Split panes | yes | yes | yes | no | yes | yes | no | no | no | ? | no | yes | ? |
| Tab/pane detach & reorder | yes | yes | yes | no | partial | yes | yes | no | no | ? | partial | yes | ? |
| Quake/dropdown mode | no | yes | yes | no | no | no | no | no | no | ? | yes | yes | ? |
| Fullscreen mode | yes | yes | yes | yes | yes | yes | yes | yes | yes | ? | yes | yes | ? |

### Other

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sixel image display | yes | no | no | yes | yes | yes | partial | no | yes | ? | yes | yes | ? |
| Kitty graphics protocol support | yes | yes | yes | no | yes | partial | no | no | no | ? | no | partial | ? |
| Desktop notification support | yes | yes | yes | yes | yes | yes | partial | no | partial | ? | partial | yes | ? |
| Ligature-aware cursor rendering | ? | yes | yes | no | partial | yes | no | no | no | ? | yes | yes | ? |
| Blurred background / transparency | yes | yes | yes | yes | yes | yes | no | partial | no | ? | partial | yes | ? |
| Tab colouring | yes | yes | partial | no | yes | yes | no | no | no | ? | partial | yes | ? |
| Undercurl / styled underlines | yes | yes | yes | yes | yes | yes | yes | yes | no | ? | yes | yes | ? |

### Platform

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Linux/X11 | yes | yes | yes | no | yes | yes | yes | yes | yes | ? | no | no | ? |
| Linux/Wayland | yes | yes | yes | yes | yes | yes | yes | yes | no | ? | no | no | ? |
| macOS | yes | yes | yes | no | yes | partial | no | yes | partial | ? | no | yes | ? |
| Windows | yes | no | no | no | yes | partial | no | yes | no | ? | yes | no | ? |
| BSD | yes | yes | partial | partial | yes | yes | yes | yes | yes | ? | no | no | ? |

### Rendering

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GPU-accelerated rendering | yes | yes | yes | no | yes | no | partial | yes | no | ? | no | yes | ? |
| GPU rendering API | Qt RHI (OpenGL, Vulkan, Metal, or Direct3D 11, selected by Qt's backend at runtime) | OpenGL 3.1+ (Linux, w/ extensions) / OpenGL 3.3 core (macOS) | Metal (macOS), OpenGL 4.3+ (Linux/BSD), WebGL (wasm) | none (software rendering via pixman + Wayland shm buffers) | OpenGL (default); optional WebGpu via wgpu (Vulkan/Metal/DX12); Software fallback | none - CPU/software rasterization via QWidget+QPainter (Qt raster paint engine) | GTK4 GSK scene graph (OpenGL 'NGL' renderer; Vulkan by default on Wayland since GTK 4.16) | OpenGL 3.3 core (GLES 2.0 fallback) | none (Xlib/Xft, CPU-rendered) | unknown | None — GDI raster (CPU); DirectWrite only for glyph-existence probing | Metal | unknown |
| Font ligatures | yes | yes | yes | no | yes | yes | partial | no | no | ? | yes | yes | ? |
| Bitmap/emoji font support | yes | yes | yes | yes | yes | yes | yes | partial | partial | ? | yes | yes | ? |
| Subpixel (LCD) antialiasing | yes | no | no | yes | yes | partial | partial | no | yes | ? | yes | partial | ? |
| Variable font support | ? | yes | yes | ? | partial | ? | yes | yes | ? | ? | ? | ? | ? |

### Session

| Feature | Contour | kitty | Ghostty | foot | WezTerm | Konsole | GNOME Terminal (VTE) | Alacritty | xterm | Windows Terminal | Mintty | iTerm2 | Terminal.app |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Shell integration (semantic prompt marks) | yes | yes | yes | yes | yes | yes | yes | no | no | ? | partial | yes | ? |
| Session restore | no | partial | partial | no | partial | yes | no | no | no | ? | no | yes | ? |
| Remote/SSH integration (e.g. kitten ssh) | no | yes | yes | no | yes | yes | no | no | no | ? | no | yes | ? |
| Built-in multiplexer (detachable, tmux-like) | no | no | no | no | yes | no | no | no | no | ? | no | partial | ? |

## Licence

Apache-2.0. Results and report generated by the harness in this repository.
