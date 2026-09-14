#!/usr/bin/env python3
"""Draw the download record as a page you can open.

The CSV is a running total per asset per day, which is not what anybody wants
to look at: the question is how many were downloaded *on* a day, and that is
the difference between one day's total and the day before's. The first day has
no day before it, so it has no bar — only the totals it starts from.

Writes a self-contained page beside the data. Nothing is fetched at view time:
a file:// page cannot read its sibling CSV, so the numbers are baked in and the
page is rewritten whenever this runs.
"""

import csv
import html
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Overridable so the page can be drawn from a scratch copy without touching the
# record itself.
CSV = Path(
    os.environ.get(
        "LEDGE_DOWNLOADS_CSV",
        Path.home() / "Developer/ledge-website/data/downloads.csv",
    )
)
OUT = CSV.parent / "downloads.html"

# Validated against the reference palette: ΔE 33.6 normal, 24.7 protan (light)
# and 31.8 / 26.8 (dark) — both well clear of the floor.
SERIES = [
    ("Downloads", "dmg", "#2a78d6", "#3987e5"),
    ("Update checks", "feed", "#eb6834", "#d95926"),
]


def load(path):
    """Totals per day, split into disk images and appcast fetches."""
    days = defaultdict(lambda: {"dmg": 0, "feed": 0, "delta": 0})
    with open(path, newline="") as handle:
        for row in csv.DictReader(handle):
            count = int(row["count"])
            asset = row["asset"]
            if asset.endswith(".dmg"):
                days[row["date"]]["dmg"] += count
            elif asset == "appcast.xml":
                days[row["date"]]["feed"] += count
            elif asset.endswith(".delta"):
                days[row["date"]]["delta"] += count
    return dict(sorted(days.items()))


def deltas(days):
    """Per-day movement. The first day has nothing to subtract from."""
    out = []
    previous = None
    for date, totals in days.items():
        if previous is not None:
            out.append((date, {k: max(0, totals[k] - previous[k]) for k in totals}))
        previous = totals
    return out


def bars(rows, key, colour):
    if not rows:
        return ""
    top = max(max(r[1][key] for r in rows), 1)
    cells = []
    for date, totals in rows:
        value = totals[key]
        height = round(value / top * 100, 1)
        cells.append(
            f'<div class="bar" title="{html.escape(date)}: {value}">'
            f'<div class="fill" style="height:{height}%;background:{colour}"></div>'
            f'<span class="tick">{html.escape(date[5:])}</span></div>'
        )
    return "".join(cells)


def main():
    if not CSV.exists():
        sys.exit(f"no record yet: {CSV}")
    days = load(CSV)
    if not days:
        sys.exit("the record is empty")
    latest_date, latest = list(days.items())[-1]
    moved = deltas(days)

    if moved:
        chart = f"""
        <div class="chart">
          <div class="plot">{bars(moved, "dmg", "var(--series-1)")}</div>
          <p class="caption">Downloads per day</p>
        </div>
        <div class="chart">
          <div class="plot">{bars(moved, "feed", "var(--series-2)")}</div>
          <p class="caption">Update checks per day</p>
        </div>"""
        note = f"{len(moved)} day{'s' if len(moved) != 1 else ''} of movement so far."
    else:
        chart = ""
        note = (
            "One day recorded. A day's downloads are the difference from the day "
            "before, so the first bars appear once a second day lands."
        )

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Ledge downloads</title>
<style>
  :root {{
    color-scheme: light dark;
    --surface-1: #fcfcfb;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --series-1: #2a78d6;
    --series-2: #eb6834;
    --rule: #e4e3df;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --surface-1: #1a1a19;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --series-1: #3987e5;
      --series-2: #d95926;
      --rule: #34332f;
    }}
  }}
  body {{
    margin: 0; padding: 48px 40px 56px;
    background: var(--surface-1); color: var(--text-primary);
    font: 14px/1.5 -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  }}
  h1 {{ font-size: 19px; font-weight: 600; margin: 0 0 2px; }}
  .sub {{ color: var(--text-secondary); margin: 0 0 32px; }}
  .tiles {{ display: flex; gap: 44px; margin-bottom: 40px; }}
  .tile .n {{ font-size: 40px; font-weight: 600; letter-spacing: -0.02em;
              font-variant-numeric: tabular-nums; }}
  .tile .l {{ color: var(--text-secondary); }}
  .tile .swatch {{ display: inline-block; width: 9px; height: 9px; border-radius: 2px;
                   margin-right: 7px; vertical-align: 1px; }}
  .chart {{ margin-bottom: 34px; max-width: 760px; }}
  .plot {{ display: flex; align-items: flex-end; gap: 2px; height: 132px;
           border-bottom: 1px solid var(--rule); padding-bottom: 0; }}
  .bar {{ flex: 1; height: 100%; display: flex; flex-direction: column;
          justify-content: flex-end; align-items: stretch; position: relative;
          min-width: 14px; }}
  .fill {{ border-radius: 4px 4px 0 0; min-height: 2px; }}
  .tick {{ position: absolute; bottom: -22px; left: 0; right: 0; text-align: center;
           color: var(--text-secondary); font-size: 11px;
           font-variant-numeric: tabular-nums; }}
  .caption {{ margin: 30px 0 0; color: var(--text-secondary); }}
  .note {{ color: var(--text-secondary); max-width: 52ch; }}
  table {{ border-collapse: collapse; margin-top: 36px; font-variant-numeric: tabular-nums; }}
  th, td {{ text-align: right; padding: 5px 18px 5px 0; }}
  th:first-child, td:first-child {{ text-align: left; }}
  th {{ color: var(--text-secondary); font-weight: 500; border-bottom: 1px solid var(--rule); }}
</style></head><body>
  <h1>Ledge downloads</h1>
  <p class="sub">Running totals as of {html.escape(latest_date)}</p>

  <div class="tiles">
    <div class="tile">
      <div class="n">{latest['dmg']}</div>
      <div class="l"><span class="swatch" style="background:var(--series-1)"></span>Downloads</div>
    </div>
    <div class="tile">
      <div class="n">{latest['feed']}</div>
      <div class="l"><span class="swatch" style="background:var(--series-2)"></span>Update checks</div>
    </div>
    <div class="tile">
      <div class="n">{latest['delta']}</div>
      <div class="l">Patch updates</div>
    </div>
  </div>

  {chart}
  <p class="note">{html.escape(note)}</p>

  <table>
    <tr><th>Date</th><th>Downloads</th><th>Checks</th><th>Patches</th></tr>
    {''.join(
        f"<tr><td>{html.escape(d)}</td><td>{t['dmg']}</td>"
        f"<td>{t['feed']}</td><td>{t['delta']}</td></tr>"
        for d, t in days.items()
    )}
  </table>
</body></html>"""

    OUT.write_text(page)
    print(OUT)
    if "--open" in sys.argv:
        subprocess.run(["open", str(OUT)], check=False)


if __name__ == "__main__":
    main()
