#!/usr/bin/env python3
"""Turn measured results and curated data into the report and the Pages site.

Two renderers over one model: `render_markdown` writes REPORT.md, `render_html` writes
docs/index.html.  Neither invents anything -- every cell traces to either a ucs-detect
YAML in results/ or a row in data/.

Run:  python3 harness/make_report.py
"""
from __future__ import annotations

import collections
import dataclasses
import html
import json
import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / "results"
DATA = ROOT / "data"
DOCS = ROOT / "docs"

sys.path.insert(0, str(HERE))
from curated import load_matrix                       # noqa: E402
from terminals import BY_KEY, REPORT_ORDER, TERMINALS  # noqa: E402

SUPPORT_MARK = {
    "yes": ("&#10003;", "yes", "yes"),
    "partial": ("~", "partial", "partial"),
    "no": ("&#8212;", "no", "no"),
    "unknown": ("?", "unknown", "?"),
}


@dataclasses.dataclass
class PlatformRun:
    """One platform's worth of measurements."""

    platform: str
    provenance: dict
    runs: list[dict]
    yamls: dict[str, dict]          # terminal key -> parsed ucs-detect YAML


def load_platforms() -> list[PlatformRun]:
    """Load every results/<platform>/ directory that has a run summary."""
    out = []
    for summary_path in sorted(RESULTS.glob("*/run-summary.json")):
        directory = summary_path.parent
        summary = json.loads(summary_path.read_text())
        yamls = {}
        for record in summary["runs"]:
            if not record.get("yaml"):
                continue
            path = directory / record["yaml"]
            if path.exists():
                yamls[record["terminal"]] = yaml.safe_load(path.read_text())
        out.append(PlatformRun(directory.name, summary["provenance"],
                               summary["runs"], yamls))
    return out


def load_yaml(name: str):
    """Load a curated data file, tolerating its absence."""
    return load_matrix(DATA / name)


def category_score(doc: dict, key: str) -> tuple[int, int]:
    """Return (total, errors) for one ucs-detect category."""
    section = (doc.get("test_results") or {}).get(key) or {}
    total = sum((v or {}).get("n_total", 0) for v in section.values())
    errors = sum((v or {}).get("n_errors", 0) for v in section.values())
    return total, errors


def pct(total: int, errors: int) -> float | None:
    """Percentage of measurements that matched the expectation."""
    return None if not total else 100.0 * (total - errors) / total


def probe_value(doc: dict, probe: dict) -> str:
    """Resolve one capability probe to yes/no/unknown."""
    value = (doc.get("terminal_results") or {}).get(probe["field"])
    if value is None:
        return "unknown"
    if isinstance(value, dict):
        if probe.get("truthy_when_dict"):
            return "yes" if value else "no"
        return "yes" if value else "no"
    return "yes" if value else "no"


def mode_value(doc: dict, number: int) -> str:
    """Resolve one DEC private mode to yes/no/unknown."""
    modes = (doc.get("terminal_results") or {}).get("modes") or {}
    entry = modes.get(str(number), modes.get(number))
    if entry is None:
        return "unknown"
    return "yes" if entry.get("supported") else "no"


# --------------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------------

def md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a GitHub-flavoured markdown table."""
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def measured_terminals(platforms: list[PlatformRun]) -> list[str]:
    """Terminal keys that produced results anywhere, in report order."""
    seen = {k for p in platforms for k in p.yamls}
    return [k for k in REPORT_ORDER if k in seen]


def render_markdown(platforms, caps, vt_features, gui_features) -> str:
    keys = measured_terminals(platforms)
    lines: list[str] = []
    add = lines.append

    add("# Terminal emulator comparison")
    add("")
    add("Unicode, VT sequence and GUI feature comparison across terminal emulators.")
    add("Measurements are reproducible: see [README.md](README.md).")
    add("")

    # ---- provenance
    add("## How this was produced")
    add("")
    for run in platforms:
        prov = run.provenance
        patches = ", ".join(f"`{p['file']}` ({p['sha256']})"
                            for p in prov.get("ucs_detect_patches", [])) or "none"
        add(f"- **{run.platform}** — {prov.get('generated')}, "
            f"`{prov.get('platform_detail','')}`")
        add(f"  - ucs-detect pinned at "
            f"`{prov.get('ucs_detect_pinned_commit','unknown')[:12]}`, "
            f"patches: {patches}")
        add(f"  - arguments: `{' '.join(prov.get('ucs_detect_args', []))}`")
    add("")

    add("### Terminals measured")
    add("")
    rows = []
    for run in platforms:
        for record in run.runs:
            rows.append([
                BY_KEY[record["terminal"]].name,
                f"`{record['version']}`",
                run.platform,
                record["display"],
                record["status"],
                f"{record['elapsed_sec']}s",
            ])
    add(md_table(["Terminal", "Version", "Platform", "Display", "Status", "Run time"],
                 rows))
    add("")

    missing = [t for t in TERMINALS if t.key not in keys]
    if missing:
        add("### Not measured here")
        add("")
        add(md_table(
            ["Terminal", "Why"],
            [[t.name, t.notes or "no launch definition for this platform"]
             for t in missing]))
        add("")
        add("These rows are filled by running the same harness on macOS or Windows and "
            "committing the results; see README.md.")
        add("")

    # ---- Unicode
    add("## Unicode support (measured)")
    add("")
    add("Each cell is the share of measurements whose cursor advance matched the "
        "expected column width. Higher is better.")
    add("")
    cats = caps["unicode_categories"]
    headers = ["Terminal"] + [c["name"] for c in cats] + ["**Overall**"]
    rows = []
    for run in platforms:
        for key in keys:
            doc = run.yamls.get(key)
            if not doc:
                continue
            cells, gt, ge = [], 0, 0
            for cat in cats:
                total, errors = category_score(doc, cat["key"])
                gt += total
                ge += errors
                value = pct(total, errors)
                cells.append("—" if value is None else f"{value:.1f}%")
            overall = pct(gt, ge)
            rows.append(([BY_KEY[key].name] + cells +
                         [f"**{overall:.1f}%**" if overall is not None else "—"],
                         overall or 0))
    rows.sort(key=lambda r: -r[1])
    add(md_table(headers, [r[0] for r in rows]))
    add("")
    for cat in cats:
        add(f"- **{cat['name']}** — {cat['blurb'].strip()}")
    add("")

    # ---- measured capabilities
    add("## Capabilities (measured by probe)")
    add("")
    add("Answered by the terminal during the run. A dash can mean *not supported*, "
        "*not enabled by default*, or *the probe asked the wrong question* — caveats "
        "are noted beneath the table.")
    add("")
    headers = ["Capability"] + [BY_KEY[k].name for k in keys]
    rows, notes = [], []
    for probe in caps["probes"]:
        row = [probe["name"]]
        for key in keys:
            doc = next((p.yamls[key] for p in platforms if key in p.yamls), None)
            row.append(SUPPORT_MARK[probe_value(doc, probe)][2] if doc else "?")
        rows.append(row)
        if probe.get("caveat"):
            notes.append(f"- **{probe['name']}** — {probe['caveat'].strip()}")
    add(md_table(headers, rows))
    add("")
    if notes:
        add("**Caveats**")
        add("")
        lines.extend(notes)
        add("")

    add("### DEC private modes (DECRQM)")
    add("")
    rows = []
    for mode in caps["modes"]:
        row = [f"{mode['number']} — {mode['name']}"]
        for key in keys:
            doc = next((p.yamls[key] for p in platforms if key in p.yamls), None)
            row.append(SUPPORT_MARK[mode_value(doc, mode["number"])][2] if doc else "?")
        rows.append(row)
    add(md_table(["Mode"] + [BY_KEY[k].name for k in keys], rows))
    add("")

    # ---- curated matrices
    for title, features, blurb in (
        ("VT sequences and extensions (documented)", vt_features,
         "Compiled from each terminal's source tree and documentation rather than "
         "measured, so it covers terminals this machine cannot run."),
        ("GUI and user-facing features (documented)", gui_features,
         "Compiled from official documentation and source."),
    ):
        if not features:
            continue
        add(f"## {title}")
        add("")
        add(blurb)
        add("")
        by_cat = collections.defaultdict(list)
        for row in features:
            by_cat[row.get("category", "other")].append(row)
        all_keys = [t.key for t in TERMINALS]
        for category, rows_in_cat in sorted(by_cat.items()):
            add(f"### {category.replace('_', ' ').title()}")
            add("")
            table_rows = []
            for row in rows_in_cat:
                cells = [row["name"]]
                values = row.get("values")
                support = row.get("support") or {}
                for key in all_keys:
                    if values is not None:
                        cells.append(str(values.get(key, "?")))
                    else:
                        verdict = support.get(key, "unknown")
                        cells.append(SUPPORT_MARK.get(verdict,
                                                      SUPPORT_MARK["unknown"])[2])
                table_rows.append(cells)
            add(md_table(["Feature"] + [BY_KEY[k].name for k in all_keys], table_rows))
            add("")

    add("## Licence")
    add("")
    add("Apache-2.0. Results and report generated by the harness in this repository.")
    add("")
    return "\n".join(lines)


# --------------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------------

CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#e2e2e2;--head:#f6f7f9;
--yes:#177245;--yesbg:#e6f4ea;--no:#8a8a8a;--nobg:#f2f2f2;
--part:#8a5a00;--partbg:#fdf3e0;--unk:#7a7a8a;--unkbg:#f0f0f4;--accent:#0b5fff}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e7e9ee;--muted:#9aa0ab;
--line:#262a33;--head:#171b22;--yes:#5fd08a;--yesbg:#12301f;--no:#7c828d;--nobg:#1a1d24;
--part:#e0b062;--partbg:#2e2413;--unk:#8b90a0;--unkbg:#1c1f27;--accent:#6ea8fe}}
:root[data-theme=dark]{--bg:#0f1115;--fg:#e7e9ee;--muted:#9aa0ab;--line:#262a33;
--head:#171b22;--yes:#5fd08a;--yesbg:#12301f;--no:#7c828d;--nobg:#1a1d24;
--part:#e0b062;--partbg:#2e2413;--unk:#8b90a0;--unkbg:#1c1f27;--accent:#6ea8fe}
:root[data-theme=light]{--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#e2e2e2;--head:#f6f7f9;
--yes:#177245;--yesbg:#e6f4ea;--no:#8a8a8a;--nobg:#f2f2f2;--part:#8a5a00;--partbg:#fdf3e0;
--unk:#7a7a8a;--unkbg:#f0f0f4;--accent:#0b5fff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:2rem 1.25rem 5rem}
h1{font-size:2rem;margin:0 0 .35rem;letter-spacing:-.02em}
h2{font-size:1.4rem;margin:2.75rem 0 .5rem;padding-top:1rem;border-top:1px solid var(--line)}
h3{font-size:1.05rem;margin:1.75rem 0 .5rem;color:var(--muted);
text-transform:uppercase;letter-spacing:.06em}
p,li{color:var(--fg)} .lede{color:var(--muted);font-size:1.05rem;margin:0 0 1.5rem}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:.75rem 0 1rem;
border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:.5rem .65rem;text-align:center;border-bottom:1px solid var(--line);
white-space:nowrap}
th{background:var(--head);font-weight:600;position:sticky;top:0;z-index:2}
td:first-child,th:first-child{text-align:left;position:sticky;left:0;background:var(--bg);
z-index:1;white-space:normal;min-width:210px}
th:first-child{background:var(--head);z-index:3}
tbody tr:hover td{background:var(--head)}
.pill{display:inline-block;min-width:2.1rem;padding:.1rem .45rem;border-radius:999px;
font-size:12px;font-weight:600}
.yes{color:var(--yes);background:var(--yesbg)}
.no{color:var(--no);background:var(--nobg)}
.partial{color:var(--part);background:var(--partbg)}
.unknown{color:var(--unk);background:var(--unkbg)}
.num{font-variant-numeric:tabular-nums}
.bar{position:relative;display:block;min-width:64px}
.bar em{position:absolute;inset:0;background:var(--yesbg);border-radius:4px;
transform-origin:left;z-index:0}
.bar span{position:relative;z-index:1;font-variant-numeric:tabular-nums}
.note{color:var(--muted);font-size:14px}
.callout{border:1px solid var(--line);border-left:3px solid var(--accent);
background:var(--head);border-radius:8px;padding:1rem 1.15rem;margin:1.25rem 0}
.callout h3{margin-top:0;color:var(--fg);text-transform:none;letter-spacing:0;
font-size:1.05rem}
code{background:var(--head);border:1px solid var(--line);border-radius:5px;
padding:.08em .35em;font-size:.9em}
a{color:var(--accent)}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);
color:var(--muted);font-size:14px}
"""


def cell(verdict: str) -> str:
    """Render a support verdict as an HTML pill."""
    mark, css, _ = SUPPORT_MARK.get(verdict, SUPPORT_MARK["unknown"])
    return f'<span class="pill {css}">{mark}</span>'


def score_cell(value: float | None) -> str:
    """Render a percentage with a proportional background bar."""
    if value is None:
        return '<span class="note">—</span>'
    return (f'<span class="bar"><em style="transform:scaleX({value/100:.4f})"></em>'
            f'<span>{value:.1f}%</span></span>')


def html_table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
                   for row in rows)
    return (f'<div class="scroll"><table><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def render_html(platforms, caps, vt_features, gui_features) -> str:
    keys = measured_terminals(platforms)
    parts: list[str] = []
    add = parts.append

    generated = platforms[0].provenance.get("generated", "") if platforms else ""
    add(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Terminal emulator comparison</title>
<meta name="description" content="Unicode, VT sequence and GUI feature comparison across terminal emulators.">
<style>{CSS}</style></head><body><div class="wrap">""")

    add("<h1>Terminal emulator comparison</h1>")
    add('<p class="lede">Unicode, VT sequence and GUI feature support across terminal '
        "emulators &mdash; measured, not asserted. Every number below is reproduced by "
        'the harness in <a href="https://github.com/contour-terminal/terminal-comparison">'
        "this repository</a>.</p>")
    prov = platforms[0].provenance if platforms else {}
    patches = ", ".join(f"<code>{html.escape(p['file'])}</code>"
                        for p in prov.get("ucs_detect_patches", [])) or "none"
    add(f'<p class="note">Generated {html.escape(generated)} &middot; '
        f"ucs-detect pinned at "
        f"<code>{html.escape(prov.get('ucs_detect_pinned_commit','unknown')[:12])}</code> "
        f"+ {patches}.</p>")

    # ---- VS15 callout: the finding that motivated the tooling fix
    add("""<div class="callout"><h3>A note on VS15</h3>
<p>Variation Selector-15 (<code>U+FE0E</code>) selects <em>text</em> presentation. Per
<a href="https://github.com/contour-terminal/terminal-unicode-core">terminal-unicode-core</a>
it must <strong>not</strong> change a grapheme cluster's width: VS16 may promote a cluster to two
columns, but VS15 may not shrink one back. The asymmetry is mechanical &mdash; a terminal reaches
the selector only after the base character has been placed and the cursor advanced, so giving a
column back means un-wrapping a line that has already wrapped, or un-scrolling content that has
already left the screen.</p>
<p>The upstream <code>ucs-detect</code> VS15 test expected the opposite, scoring a conforming
terminal at 0%. This repository pins a
<a href="https://github.com/contour-terminal/terminal-comparison/blob/main/patches/0001-vs15-must-not-narrow.patch">patched</a>
oracle that expects the base character's own width. Measured against xterm, which has no
grapheme-clustering mode and can only report the unchanged width, the correction moves the score
from 0/158 to 158/158.</p></div>""")

    # ---- provenance
    add("<h2>How this was produced</h2>")
    rows = []
    for run in platforms:
        for record in run.runs:
            rows.append([
                html.escape(BY_KEY[record["terminal"]].name),
                f"<code>{html.escape(str(record['version']))}</code>",
                html.escape(run.platform),
                html.escape(record["display"]),
                cell("yes") if record["status"] == "ok" else html.escape(record["status"]),
                f'<span class="num">{record["elapsed_sec"]}s</span>',
            ])
    add(html_table(["Terminal", "Version", "Platform", "Display", "Ran", "Run time"], rows))

    missing = [t for t in TERMINALS if t.key not in keys]
    if missing:
        add("<h3>Not measured here</h3>")
        add(html_table(
            ["Terminal", "Why"],
            [[html.escape(t.name),
              f'<span class="note">{html.escape(t.notes or "no launch definition for this platform")}</span>']
             for t in missing]))
        add('<p class="note">These rows are filled by running the same harness on macOS '
            "or Windows and committing the results.</p>")

    # ---- Unicode scores
    add("<h2>Unicode support (measured)</h2>")
    add('<p class="note">Share of measurements whose cursor advance matched the expected '
        "column width. Higher is better.</p>")
    cats = caps["unicode_categories"]
    rows = []
    for run in platforms:
        for key in keys:
            doc = run.yamls.get(key)
            if not doc:
                continue
            cells, gt, ge = [], 0, 0
            for cat in cats:
                total, errors = category_score(doc, cat["key"])
                gt += total
                ge += errors
                cells.append(score_cell(pct(total, errors)))
            overall = pct(gt, ge)
            rows.append(([html.escape(BY_KEY[key].name)] + cells +
                         [f"<strong>{overall:.1f}%</strong>" if overall is not None else "—"],
                         overall or 0))
    rows.sort(key=lambda r: -r[1])
    add(html_table(["Terminal"] + [c["name"] for c in cats] + ["Overall"],
                   [r[0] for r in rows]))
    add("<ul>" + "".join(
        f"<li><strong>{html.escape(c['name'])}</strong> — "
        f"{html.escape(c['blurb'].strip())}</li>" for c in cats) + "</ul>")

    # ---- probes
    add("<h2>Capabilities (measured by probe)</h2>")
    add('<p class="note">Answered by the terminal during the run. A dash can mean '
        "<em>not supported</em>, <em>not enabled by default</em>, or <em>the probe asked "
        "the wrong question</em>; caveats follow the table.</p>")
    rows, notes = [], []
    for probe in caps["probes"]:
        row = [html.escape(probe["name"])]
        for key in keys:
            doc = next((p.yamls[key] for p in platforms if key in p.yamls), None)
            row.append(cell(probe_value(doc, probe)) if doc else cell("unknown"))
        rows.append(row)
        if probe.get("caveat"):
            notes.append(f"<li><strong>{html.escape(probe['name'])}</strong> — "
                         f"{html.escape(probe['caveat'].strip())}</li>")
    add(html_table(["Capability"] + [BY_KEY[k].name for k in keys], rows))
    if notes:
        add("<h3>Caveats</h3><ul>" + "".join(notes) + "</ul>")

    add("<h3>DEC private modes (DECRQM)</h3>")
    rows = []
    for mode in caps["modes"]:
        row = [f"<code>{mode['number']}</code> {html.escape(mode['name'])}"]
        for key in keys:
            doc = next((p.yamls[key] for p in platforms if key in p.yamls), None)
            row.append(cell(mode_value(doc, mode["number"])) if doc else cell("unknown"))
        rows.append(row)
    add(html_table(["Mode"] + [BY_KEY[k].name for k in keys], rows))

    # ---- curated
    all_keys = [t.key for t in TERMINALS]
    for title, features, blurb in (
        ("VT sequences and extensions", vt_features,
         "Compiled from each terminal's source tree and documentation rather than "
         "measured, so it also covers terminals this machine cannot run."),
        ("GUI and user-facing features", gui_features,
         "Compiled from official documentation and source."),
    ):
        if not features:
            continue
        add(f"<h2>{html.escape(title)} <span class='note'>(documented)</span></h2>")
        add(f'<p class="note">{html.escape(blurb)}</p>')
        by_cat = collections.defaultdict(list)
        for row in features:
            by_cat[row.get("category", "other")].append(row)
        for category, rows_in_cat in sorted(by_cat.items()):
            add(f"<h3>{html.escape(category.replace('_', ' '))}</h3>")
            table_rows = []
            for row in rows_in_cat:
                label = f"<strong>{html.escape(row['name'])}</strong>"
                if row.get("sequence"):
                    label += f"<br><code>{html.escape(str(row['sequence']))}</code>"
                if row.get("notes"):
                    label += f'<br><span class="note">{html.escape(str(row["notes"]))}</span>'
                cells = [label]
                values, support = row.get("values"), row.get("support") or {}
                for key in all_keys:
                    if values is not None:
                        cells.append(f'<span class="note">'
                                     f'{html.escape(str(values.get(key, "?")))}</span>')
                    else:
                        cells.append(cell(support.get(key, "unknown")))
                table_rows.append(cells)
            add(html_table(["Feature"] + [BY_KEY[k].name for k in all_keys], table_rows))

    add("<footer>Apache-2.0. Generated by <code>harness/make_report.py</code> from the "
        "YAML files in <code>results/</code> and <code>data/</code>. "
        '<a href="https://github.com/contour-terminal/terminal-comparison">Source</a>.'
        "</footer>")
    add("</div></body></html>")
    return "\n".join(parts)


def main() -> int:
    platforms = load_platforms()
    if not platforms:
        print("error: no results found under results/*/run-summary.json", file=sys.stderr)
        return 2
    caps = yaml.safe_load((DATA / "measured-capabilities.yaml").read_text())
    vt_features = load_yaml("vt-features.yaml")
    gui_features = load_yaml("gui-features.yaml")

    DOCS.mkdir(parents=True, exist_ok=True)
    (ROOT / "REPORT.md").write_text(
        render_markdown(platforms, caps, vt_features, gui_features))
    (DOCS / "index.html").write_text(
        render_html(platforms, caps, vt_features, gui_features))

    measured = measured_terminals(platforms)
    print(f"wrote REPORT.md and docs/index.html "
          f"({len(measured)} terminals measured, "
          f"{len(vt_features)} VT rows, {len(gui_features)} GUI rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
