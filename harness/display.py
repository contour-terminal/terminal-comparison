#!/usr/bin/env python3
"""Headless display servers for the measurement run.

Only Linux needs this.  On macOS and Windows the terminals run in the user's real
session, because neither platform has a practical equivalent of "a throwaway display
server for a GUI app", and both keep their terminal emulators tied to the window
server.  `NullDisplay` represents that case.

Why the Wayland backend nests weston inside Xvfb rather than using weston's own
headless backend: the headless backend brings up a compositor but advertises no
`wl_seat`, and a Wayland client such as foot aborts with "no seats available".
Nesting weston's x11 backend inside Xvfb gives it real X input devices, so a seat
exists, while the whole stack stays off-screen.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
import time


class NullDisplay:
    """The machine's own session; used on macOS and Windows."""

    kind = "native"

    def __init__(self, workdir: pathlib.Path):
        self.workdir = workdir
        self.env: dict[str, str] = {}

    def start(self) -> None:
        return

    def stop(self) -> None:
        return


class Display:
    """A private, off-screen display server on Linux."""

    def __init__(self, kind: str, workdir: pathlib.Path):
        self.kind = kind
        self.workdir = workdir
        self.proc: subprocess.Popen | None = None
        self._xvfb: subprocess.Popen | None = None
        self.env: dict[str, str] = {}

    def start(self) -> None:
        if self.kind == "x11":
            self._start_xvfb()
        elif self.kind == "wayland":
            self._start_weston()
        else:
            raise ValueError(f"unknown display kind {self.kind!r}")

    def _start_xvfb(self) -> None:
        for display_num in range(90, 130):
            if pathlib.Path(f"/tmp/.X{display_num}-lock").exists():
                continue
            log = open(self.workdir / f"xvfb-{display_num}.log", "wb")
            self.proc = subprocess.Popen(
                ["Xvfb", f":{display_num}", "-screen", "0", "1920x1080x24",
                 "-nolisten", "tcp"],
                stdout=log, stderr=subprocess.STDOUT,
            )
            for _ in range(100):
                time.sleep(0.1)
                if self.proc.poll() is not None:
                    break
                if subprocess.run(["xdpyinfo", "-display", f":{display_num}"],
                                  capture_output=True).returncode == 0:
                    self.env = {"DISPLAY": f":{display_num}"}
                    return
            if self.proc.poll() is None:
                self.proc.terminate()
        raise RuntimeError("could not start Xvfb")

    def _start_weston(self) -> None:
        runtime = os.environ.get("XDG_RUNTIME_DIR")
        if not runtime or not os.access(runtime, os.W_OK):
            runtime = tempfile.mkdtemp(prefix="tcmp-runtime-")
            os.chmod(runtime, 0o700)

        self._start_xvfb()
        self._xvfb, xvfb_env = self.proc, self.env

        socket = f"wayland-tcmp-{os.getpid()}"
        ini = self.workdir / "weston.ini"
        ini.write_text("[core]\nrequire-input=false\nidle-time=0\n")
        log = open(self.workdir / "weston.log", "wb")
        self.proc = subprocess.Popen(
            ["weston", "--backend=x11", f"--socket={socket}",
             "--width=1600", "--height=900", f"--config={ini}"],
            stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, XDG_RUNTIME_DIR=runtime, **xvfb_env),
        )
        sock_path = pathlib.Path(runtime) / socket
        for _ in range(150):
            time.sleep(0.1)
            if sock_path.exists():
                self.env = {"WAYLAND_DISPLAY": socket,
                            "XDG_RUNTIME_DIR": runtime,
                            "GDK_BACKEND": "wayland"}
                return
            if self.proc.poll() is not None:
                break
        raise RuntimeError("could not start weston")

    def stop(self) -> None:
        for proc in (self.proc, self._xvfb):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()


def make_display(kind: str, workdir: pathlib.Path):
    """Return the display server appropriate for *kind* on this platform."""
    if kind in ("x11", "wayland"):
        return Display(kind, workdir)
    return NullDisplay(workdir)
