#!/usr/bin/env python3
"""Drive ucs-detect inside each terminal emulator and record the results.

Isolation, and why each piece is needed:

* off-screen display -- Xvfb for X11 terminals, weston-in-Xvfb for Wayland-only ones
  (Linux only).  Nothing appears on the user's desktop and the run does not depend on
  their session.
* private D-Bus session -- GNOME Terminal, Konsole and Ghostty are single-instance
  apps that rendezvous over the session bus.  Without a private bus, launching one
  hands the command to the user's already-running instance, which lives on the real
  display, and the run silently measures nothing.
* private XDG_CONFIG_HOME -- every terminal starts from its own defaults rather than
  the operator's personal settings, so the numbers describe the shipped configuration.
* software rendering -- there is no GPU behind Xvfb.  GPU-accelerated terminals
  otherwise fail to bring up a window and exit before running the command.
* sentinel file -- completion is detected by the inner shell writing an exit-status
  file, not by the terminal process exiting.  Terminals that fork or hand off to a
  server exit immediately, which would otherwise look like a finished run.  The
  sentinel path is absolute: it is interpreted by a shell running *inside* the
  terminal, whose working directory is its own business.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform as platform_mod
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from display import make_display                                    # noqa: E402
from terminals import BY_KEY, TERMINALS, Terminal, current_platform  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
DEFAULT_UCS = REPO_ROOT / ".ucs-detect" / ".venv" / "bin" / "ucs-detect"
UCS_DETECT = os.environ.get("UCS_DETECT_BIN", str(DEFAULT_UCS))
UCS_REPO = os.environ.get("UCS_DETECT_REPO", str(REPO_ROOT / ".ucs-detect"))


def shell_quote(value: str) -> str:
    """Quote *value* for a POSIX shell."""
    if value and all(c.isalnum() or c in "-_./:=" for c in value):
        return value
    return "'" + value.replace("'", "'\\''") + "'"


def run_one(term: Terminal, display, outdir: pathlib.Path,
            ucs_args: list[str], timeout: int, vt_probe: bool = True) -> dict:
    """Run ucs-detect inside *term* and return a result record."""
    yaml_path = outdir / f"{term.key}.yaml"
    rc_path = outdir / f"{term.key}.rc"
    term_log = outdir / f"{term.key}.term.log"
    probe_path = outdir / f"{term.key}.vtprobe.json" if vt_probe else None
    for stale in (yaml_path, rc_path, probe_path):
        if stale is not None:
            stale.unlink(missing_ok=True)

    launch = term.launch_for()
    if launch is not None and launch.applescript_app:
        # iTerm2 and Terminal.app take a command through AppleScript, not argv.
        # Refusing loudly beats building a nonsensical `osascript sh -c ...` argv that
        # would fail somewhere less obvious.
        return {
            "terminal": term.key, "name": term.name, "version": "unknown",
            "display": launch.display, "verified_launch": False,
            "status": "not-implemented", "exit_code": None, "elapsed_sec": 0.0,
            "yaml": None,
            "detail": (f"{term.name} must be driven through AppleScript "
                       f"(application {launch.applescript_app!r}); that path is "
                       f"scaffolded but not implemented. See README.md."),
        }

    config_home = outdir / "config" / term.key
    config_home.mkdir(parents=True, exist_ok=True)

    version = term.probe_version()
    inner = " ".join([
        shell_quote(UCS_DETECT), *(shell_quote(a) for a in ucs_args),
        "--save-yaml", shell_quote(str(yaml_path)),
        "--set-software-name", shell_quote(term.name),
        "--set-software-version", shell_quote(version),
    ])
    # The VT probe runs in the same launch, after ucs-detect, on the same tty. It costs
    # under a second and covers what DECRQM cannot answer: page memory and the DEC
    # locator. Its exit status is deliberately ignored -- a probe that fails must not
    # invalidate the Unicode measurements.
    parts = [inner, "rc=$?"]
    if probe_path is not None:
        parts.append(f"{shell_quote(sys.executable)} "
                     f"{shell_quote(str(HERE / 'vt_probe.py'))} "
                     f"--out {shell_quote(str(probe_path))} || true")
    parts.append(f"echo $rc > {shell_quote(str(rc_path))}")
    script = "; ".join(parts)

    argv = term.argv(["sh", "-c", script])
    if current_platform() == "linux":
        argv = ["dbus-run-session", "--", *argv]

    env = dict(os.environ)
    for stale_var in ("DISPLAY", "WAYLAND_DISPLAY"):
        env.pop(stale_var, None)
    env.update(display.env)
    if launch is not None:
        env.update(launch.env)
    env["XDG_CONFIG_HOME"] = str(config_home)
    env["LANG"] = env["LC_ALL"] = "C.UTF-8"
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    env["GALLIUM_DRIVER"] = "llvmpipe"

    started = time.monotonic()
    status = "ok"
    with open(term_log, "wb") as log:
        proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
                                env=env, start_new_session=True)
        while True:
            if rc_path.exists():
                time.sleep(1.0)          # let the YAML writer flush
                break
            if time.monotonic() - started > timeout:
                status = "timeout"
                break
            if proc.poll() is not None and not rc_path.exists():
                time.sleep(2.0)
                if not rc_path.exists():
                    status = "terminal-exited"
                    break
            time.sleep(0.5)

        if proc.poll() is None:
            _terminate(proc)

    rc = rc_path.read_text().strip() if rc_path.exists() else None
    if status == "ok" and rc not in ("0", None):
        status = f"exit-{rc}"
    if status == "ok" and not yaml_path.exists():
        status = "no-yaml"

    return {
        "terminal": term.key, "name": term.name, "version": version,
        "display": (term.launch_for().display if term.launch_for() else "?"),
        "verified_launch": bool(term.launch_for() and term.launch_for().verified),
        "status": status, "exit_code": rc,
        "elapsed_sec": round(time.monotonic() - started, 1),
        "yaml": yaml_path.name if yaml_path.exists() else None,
        "vtprobe": (probe_path.name
                    if probe_path is not None and probe_path.exists() else None),
    }


def _terminate(proc: subprocess.Popen) -> None:
    """Stop the terminal and everything it spawned."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, AttributeError):
        proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, AttributeError):
            proc.kill()


def git_rev(repo: str, args: list[str]) -> str:
    """Return git output for *repo*, or 'unknown'."""
    try:
        out = subprocess.run(["git", "-C", repo, *args],
                             capture_output=True, text=True, timeout=15)
        return out.stdout.strip() or "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--only", action="append", default=[],
                        help="terminal key; repeatable (default: all installed)")
    parser.add_argument("--timeout", type=int, default=2400)
    parser.add_argument("--test-only", default=None,
                        help="ucs-detect category (wide, vs15, vs16, zwj, ...)")
    parser.add_argument("--all", action="store_true",
                        help="pass --all to ucs-detect (full tables, not contested)")
    parser.add_argument("--no-languages", action="store_true")
    parser.add_argument("--limit-category-time", type=int, default=240)
    parser.add_argument("--no-vt-probe", action="store_true",
                        help="skip the extra VT probe (page memory, DEC locator)")
    parser.add_argument("--all-dec-modes", action="store_true",
                        help="probe every known DEC private mode, not just the "
                             "notable subset (slower, but fills the mode table)")
    args = parser.parse_args()

    if not os.access(UCS_DETECT, os.X_OK):
        print(f"error: ucs-detect not found at {UCS_DETECT}\n"
              f"Run harness/setup-ucs-detect.sh first.", file=sys.stderr)
        return 2

    outdir = pathlib.Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    keys = args.only or [t.key for t in TERMINALS if t.resolve()]
    chosen = [BY_KEY[k] for k in keys if BY_KEY[k].resolve()]
    if not chosen:
        print("error: none of the requested terminals are installed", file=sys.stderr)
        return 2

    ucs_args = ["--probe-silently", "--no-final-summary"]
    if args.test_only:
        ucs_args += ["--test-only", args.test_only]
    if args.all:
        ucs_args += ["--all"]
    if args.no_languages:
        ucs_args += ["--no-languages-test"]
    if args.limit_category_time:
        ucs_args += ["--limit-category-time", str(args.limit_category_time)]
    if args.all_dec_modes:
        ucs_args += ["--detect-all-dec-modes"]

    # The measurement tool is a pinned upstream commit plus this repository's patches,
    # applied to the working tree rather than committed.  Recording only the commit
    # would describe an oracle that was not the one used, so the patches are hashed
    # into the provenance too.
    patches = []
    for patch in sorted((REPO_ROOT / "patches").glob("*.patch")):
        digest = hashlib.sha256(patch.read_bytes()).hexdigest()
        patches.append({"file": patch.name, "sha256": digest[:16]})

    provenance = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "platform": current_platform(),
        "platform_detail": platform_mod.platform(),
        "ucs_detect_pinned_commit": git_rev(UCS_REPO, ["rev-parse", "HEAD"]),
        "ucs_detect_patches": patches,
        "ucs_detect_tree_dirty": bool(
            git_rev(UCS_REPO, ["status", "--porcelain"]) not in ("", "unknown")),
        "ucs_detect_args": ucs_args,
    }

    results = []
    for kind in ("x11", "wayland", "native"):
        group = [t for t in chosen if (t.launch_for() or None)
                 and t.launch_for().display == kind]
        if not group:
            continue
        display = make_display(kind, outdir)
        print(f">>> starting {kind} display for {len(group)} terminal(s)", flush=True)
        display.start()
        try:
            for term in group:
                print(f">>> {term.key} ...", end="", flush=True)
                record = run_one(term, display, outdir, ucs_args, args.timeout,
                                 vt_probe=not args.no_vt_probe)
                results.append(record)
                print(f" {record['status']} ({record['elapsed_sec']}s)", flush=True)
        finally:
            display.stop()

    summary = {"provenance": provenance, "runs": results}
    (outdir / "run-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if all(r["status"] == "ok" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
