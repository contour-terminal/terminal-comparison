#!/usr/bin/env python3
"""Registry of the terminal emulators under test.

Everything the harness needs in order to drive a terminal lives in this one table:
where its binary is on each platform, how to hand it a command, which display server
it needs, and how to ask it for its version.  Adding a terminal is adding a row;
teaching an existing terminal about another platform is adding a `Launch` to its map.

A note on honesty, because this data is published: the Linux launch definitions below
are exercised on every run.  The macOS and Windows definitions are *scaffolding* --
written from each terminal's documented CLI but not yet executed on that platform.
They are marked `verified=False` and the report says so, rather than implying a
coverage we do not have.
"""
from __future__ import annotations

import dataclasses
import os
import re
import shutil
import subprocess
import sys

LINUX, MACOS, WINDOWS = "linux", "darwin", "win32"


def current_platform() -> str:
    """Return the platform key for the machine we are running on."""
    if sys.platform.startswith("linux"):
        return LINUX
    if sys.platform == "darwin":
        return MACOS
    if sys.platform in ("win32", "cygwin", "msys"):
        return WINDOWS
    return sys.platform


@dataclasses.dataclass(frozen=True)
class Launch:
    """How to start one terminal on one platform."""

    binary: str
    #: Arguments placed between the binary and the command to run.
    exec_args: tuple[str, ...] = ()
    #: Linux only.  "x11" runs under Xvfb; "wayland" under weston nested in Xvfb.
    #: On macOS and Windows the terminal runs in the user's real session.
    display: str = "x11"
    version_args: tuple[str, ...] = ("--version",)
    version_re: str = r"(\d+\.\d+(?:\.\d+)?)"
    #: Extra environment for this terminal only.
    env: dict[str, str] = dataclasses.field(default_factory=dict)
    #: True once a real run on this platform has been observed to work.
    verified: bool = False
    #: Set when the command must be delivered by a script rather than argv
    #: (macOS .app bundles driven through AppleScript).
    applescript_app: str | None = None
    #: Candidate absolute paths tried before falling back to PATH lookup.
    candidates: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class Terminal:
    """One terminal emulator, across every platform it runs on."""

    key: str
    name: str
    launches: dict[str, Launch]
    homepage: str = ""
    notes: str = ""

    def launch_for(self, platform: str | None = None) -> Launch | None:
        """Return the Launch for *platform*, or None if unsupported there."""
        return self.launches.get(platform or current_platform())

    def resolve(self, platform: str | None = None) -> str | None:
        """Return the absolute path of the binary, or None when not installed."""
        launch = self.launch_for(platform)
        if launch is None:
            return None
        for candidate in launch.candidates:
            if os.access(candidate, os.X_OK):
                return candidate
        if os.path.isabs(launch.binary):
            return launch.binary if os.access(launch.binary, os.X_OK) else None
        return shutil.which(launch.binary)

    def argv(self, command: list[str], platform: str | None = None) -> list[str]:
        """Return the full argv that launches this terminal running *command*."""
        launch = self.launch_for(platform)
        path = self.resolve(platform)
        if launch is None or path is None:
            raise RuntimeError(f"{self.key} is not available on this platform")
        return [path, *launch.exec_args, *command]

    def probe_version(self, platform: str | None = None) -> str:
        """Return the terminal's version string, or a marker when unavailable."""
        launch = self.launch_for(platform)
        path = self.resolve(platform)
        if launch is None or path is None:
            return "not-installed"
        try:
            out = subprocess.run([path, *launch.version_args],
                                 capture_output=True, text=True, timeout=20)
        except (subprocess.TimeoutExpired, OSError):
            return "unknown"
        blob = (out.stdout or "") + (out.stderr or "")
        match = re.search(launch.version_re, blob)
        if match:
            return match.group(1)
        first = blob.strip().splitlines()
        return first[0][:60] if first else "unknown"


def _contour_binary() -> str:
    """Prefer an explicitly built Contour, else whatever is installed."""
    return os.environ.get("CONTOUR_BIN", "contour")


TERMINALS: tuple[Terminal, ...] = (
    Terminal(
        key="contour", name="Contour",
        homepage="https://contour-terminal.org/",
        launches={
            LINUX: Launch(binary=_contour_binary(), version_args=("version",),
                          version_re=r"(\d+\.\d+\.\d+[-\w.]*)", verified=True),
            MACOS: Launch(binary="contour", version_args=("version",),
                          candidates=("/Applications/Contour.app/Contents/MacOS/contour",)),
            WINDOWS: Launch(binary="contour.exe", version_args=("version",)),
        },
    ),
    Terminal(
        key="kitty", name="kitty",
        homepage="https://sw.kovidgoyal.net/kitty/",
        launches={
            # --config NONE keeps the user's kitty.conf out of the measurement.
            LINUX: Launch(binary="kitty",
                          exec_args=("--config", "NONE",
                                     "-o", "close_on_child_death=yes"),
                          verified=True),
            MACOS: Launch(binary="kitty",
                          exec_args=("--config", "NONE",
                                     "-o", "close_on_child_death=yes"),
                          candidates=("/Applications/kitty.app/Contents/MacOS/kitty",)),
        },
    ),
    Terminal(
        key="ghostty", name="Ghostty",
        homepage="https://ghostty.org/",
        launches={
            LINUX: Launch(binary="ghostty", exec_args=("-e",), verified=True),
            MACOS: Launch(binary="ghostty", exec_args=("-e",),
                          candidates=("/Applications/Ghostty.app/Contents/MacOS/ghostty",)),
        },
    ),
    Terminal(
        key="foot", name="foot",
        homepage="https://codeberg.org/dnkl/foot",
        notes="Wayland-only by design.",
        launches={
            LINUX: Launch(binary="foot", display="wayland", verified=True),
        },
    ),
    Terminal(
        key="wezterm", name="WezTerm",
        homepage="https://wezterm.org/",
        launches={
            LINUX: Launch(binary="wezterm",
                          exec_args=("start", "--always-new-process", "--"),
                          verified=True),
            MACOS: Launch(binary="wezterm",
                          exec_args=("start", "--always-new-process", "--"),
                          candidates=("/Applications/WezTerm.app/Contents/MacOS/wezterm",)),
            WINDOWS: Launch(binary="wezterm.exe",
                            exec_args=("start", "--always-new-process", "--")),
        },
    ),
    Terminal(
        key="konsole", name="Konsole",
        homepage="https://konsole.kde.org/",
        launches={
            # --separate forces a private process instead of joining a running one.
            LINUX: Launch(binary="konsole", exec_args=("--separate", "-e"),
                          verified=True),
        },
    ),
    Terminal(
        key="gnome-terminal", name="GNOME Terminal (VTE)",
        homepage="https://gitlab.gnome.org/GNOME/gnome-terminal",
        notes="Measures libvte, the widget behind several GTK terminals.",
        launches={
            # --wait keeps the launcher alive until the child exits.
            LINUX: Launch(binary="gnome-terminal", exec_args=("--wait", "--"),
                          verified=True),
        },
    ),
    Terminal(
        key="alacritty", name="Alacritty",
        homepage="https://alacritty.org/",
        launches={
            LINUX: Launch(binary="alacritty", exec_args=("-e",), verified=True),
            MACOS: Launch(binary="alacritty", exec_args=("-e",),
                          candidates=("/Applications/Alacritty.app/Contents/MacOS/alacritty",)),
            WINDOWS: Launch(binary="alacritty.exe", exec_args=("-e",)),
        },
    ),
    Terminal(
        key="xterm", name="xterm",
        homepage="https://invisible-island.net/xterm/",
        notes="The reference implementation; useful as a control.",
        launches={
            LINUX: Launch(binary="xterm", exec_args=("-geometry", "200x50", "-e"),
                          version_args=("-version",), version_re=r"\((\d+)\)",
                          verified=True),
        },
    ),
    # ---- platforms this machine cannot exercise -------------------------------
    Terminal(
        key="windows-terminal", name="Windows Terminal",
        homepage="https://github.com/microsoft/terminal",
        notes="Windows only. Run the harness on Windows to fill this row.",
        launches={
            WINDOWS: Launch(binary="wt.exe", exec_args=("new-tab", "--"),
                            version_args=("--version",)),
        },
    ),
    Terminal(
        key="mintty", name="Mintty",
        homepage="https://mintty.github.io/",
        notes="Cygwin/MSYS2 on Windows. Run the harness there to fill this row.",
        launches={
            WINDOWS: Launch(binary="mintty.exe", exec_args=("-e",)),
        },
    ),
    Terminal(
        key="iterm2", name="iTerm2",
        homepage="https://iterm2.com/",
        notes="macOS only. Driven through AppleScript; run the harness on macOS.",
        launches={
            MACOS: Launch(binary="osascript", applescript_app="iTerm",
                          version_args=("-e", 'tell application "iTerm" to version')),
        },
    ),
    Terminal(
        key="apple-terminal", name="Terminal.app",
        homepage="https://support.apple.com/guide/terminal/",
        notes="macOS only. Driven through AppleScript; run the harness on macOS.",
        launches={
            MACOS: Launch(binary="osascript", applescript_app="Terminal",
                          version_args=("-e", 'tell application "Terminal" to version')),
        },
    ),
)

BY_KEY = {t.key: t for t in TERMINALS}

#: Stable display order for report columns.
REPORT_ORDER = tuple(t.key for t in TERMINALS)


def installed(platform: str | None = None) -> list[Terminal]:
    """Return the terminals actually present on this machine."""
    return [t for t in TERMINALS if t.resolve(platform) is not None]


if __name__ == "__main__":
    plat = current_platform()
    print(f"platform: {plat}\n")
    for term in TERMINALS:
        launch = term.launch_for(plat)
        if launch is None:
            print(f"{term.key:18} {'-':10} unsupported on this platform")
            continue
        path = term.resolve(plat)
        mark = "verified" if launch.verified else "unverified"
        print(f"{term.key:18} {launch.display:8} {term.probe_version(plat):22} "
              f"{mark:11} {path or 'NOT INSTALLED'}")
