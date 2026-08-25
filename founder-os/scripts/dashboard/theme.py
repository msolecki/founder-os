"""The page's stylesheet, generated from one token table.

Generated rather than written out three times because the failure this prevents
is invisible: a colour defined only under `prefers-color-scheme` leaves the
default "system" viewer reading one theme's ink on the other theme's paper, and
nothing raises. One table, three emissions, and a test that counts them.

The palette is the package's, from `docs/index.html`. The additions are the ones
a data page needs: two categorical hues that stay distinguishable under the
common colour-vision deficiencies, and a status scale kept separate from the
accent so "attention" never doubles as "series two".
"""
from __future__ import annotations

TOKENS = {
    "light": {
        "--paper": "#f2eee4",
        "--surface": "#fffaf0",
        "--sunk": "#e9e3d6",
        "--ink": "#122127",
        "--ink-soft": "#4a575b",
        "--ink-faint": "#79868a",
        "--line": "rgba(18, 33, 39, 0.14)",
        "--line-strong": "rgba(18, 33, 39, 0.32)",
        "--accent": "#f15a35",
        "--accent-deep": "#ba351c",
        "--good": "#17795e",
        "--warn": "#8f6011",
        "--crit": "#ba351c",
        "--good-wash": "rgba(23, 121, 94, 0.12)",
        "--warn-wash": "rgba(143, 96, 17, 0.13)",
        "--crit-wash": "rgba(186, 53, 28, 0.11)",
        "--bet-1": "#0a6e9a",
        "--bet-2": "#6d7c15",
        "--bet-1-wash": "rgba(10, 110, 154, 0.14)",
        "--bet-2-wash": "rgba(109, 124, 21, 0.16)",
        "--stage-late": "#c2401f",
        "--stage-early": "#e79878",
        "--grid": "rgba(18, 33, 39, 0.10)",
        "--band": "rgba(18, 33, 39, 0.07)",
        "--neutral-mark": "#8d9a9d",
        "--shadow": "0 1px 2px rgba(18,33,39,.05), 0 12px 32px rgba(18,33,39,.06)",
    },
    "dark": {
        "--paper": "#0c181d",
        "--surface": "#142a31",
        "--sunk": "#0f2229",
        "--ink": "#ebe5d7",
        "--ink-soft": "#a3b3b7",
        "--ink-faint": "#74868b",
        "--line": "rgba(235, 229, 215, 0.14)",
        "--line-strong": "rgba(235, 229, 215, 0.34)",
        "--accent": "#ff7a56",
        "--accent-deep": "#ff9877",
        "--good": "#4fb894",
        "--warn": "#d7a03c",
        "--crit": "#ff7a56",
        "--good-wash": "rgba(79, 184, 148, 0.15)",
        "--warn-wash": "rgba(215, 160, 60, 0.15)",
        "--crit-wash": "rgba(255, 122, 86, 0.14)",
        "--bet-1": "#2f9dcc",
        "--bet-2": "#82992a",
        "--bet-1-wash": "rgba(47, 157, 204, 0.18)",
        "--bet-2-wash": "rgba(130, 153, 42, 0.20)",
        "--stage-late": "#ff8055",
        "--stage-early": "#a8532f",
        "--grid": "rgba(235, 229, 215, 0.10)",
        "--band": "rgba(235, 229, 215, 0.08)",
        "--neutral-mark": "#7c8d91",
        "--shadow": "0 1px 2px rgba(0,0,0,.3), 0 12px 32px rgba(0,0,0,.28)",
    },
}

CSP = ('<meta http-equiv="Content-Security-Policy" content="default-src '
       "'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
       "img-src 'self' data:; connect-src 'none'; base-uri 'none'; "
       "form-action 'none'\">")

_FONTS = (
    '  --sans: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", '
    "Roboto, sans-serif;\n"
    '  --serif: Georgia, "Iowan Old Style", "Times New Roman", serif;\n'
    "  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;\n")


def _emit(mapping) -> str:
    return "".join("  %s: %s;\n" % (name, value)
                   for name, value in sorted(mapping.items()))


_BASE = """
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 15px;
  line-height: 1.55;
}
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.wrap { max-width: 1320px; margin: 0 auto; padding: 0 24px 72px; }
.masthead { border-bottom: 1px solid var(--line); background: var(--surface); }
.masthead .wrap { display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
                  padding-top: 14px; padding-bottom: 0; }
.masthead b { letter-spacing: -.01em; }
.tabs { display: flex; gap: 4px; max-width: 1320px; margin: 0 auto;
        padding: 10px 24px 0; }
.tab { appearance: none; border: 1px solid var(--line); border-bottom: none;
       background: transparent; color: var(--ink-soft); font: inherit;
       font-size: 13px; padding: 7px 14px; border-radius: 7px 7px 0 0;
       cursor: pointer; }
.tab[aria-selected="true"] { background: var(--paper); color: var(--ink);
                             font-weight: 600; }
.tab[disabled] { color: var(--ink-faint); cursor: default; }
.layout { display: grid; grid-template-columns: 330px minmax(0, 1fr);
          gap: 22px; align-items: start; padding-top: 24px; }
.panels { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.span-2 { grid-column: 1 / -1; }
.panel, .brief { background: var(--surface); border: 1px solid var(--line);
                 border-radius: 10px; box-shadow: var(--shadow);
                 padding: 16px 17px 13px; display: flex; flex-direction: column;
                 gap: 13px; min-width: 0; }
.brief { border-left: 3px solid var(--accent); }
.panel-head { display: flex; align-items: baseline; justify-content: space-between;
              gap: 10px; flex-wrap: wrap; }
.panel-note { font-size: 11px; color: var(--ink-faint); }
.panel-title { margin: 0; font-size: 11px; font-weight: 700; text-transform: uppercase;
               letter-spacing: .11em; color: var(--ink-soft); }
.brief p { margin: 0; }
.one-thing { margin: 0; font-family: var(--serif); font-size: 24px; line-height: 1.28;
             text-wrap: balance; }
.stat-value { font-family: var(--mono); font-size: 27px; font-weight: 700;
              letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
.panel p { margin: 0; }
.bet { display: flex; flex-direction: column; gap: 8px; padding: 12px 0;
       border-top: 1px solid var(--line); }
.bet:first-of-type { border-top: none; padding-top: 0; }
.signal { display: flex; flex-direction: column; gap: 6px; }
.numbers { font-size: 12px; }
.numbers summary { cursor: pointer; color: var(--ink-faint); font-size: 11px; }
.cite { margin-top: auto; padding-top: 10px; border-top: 1px dashed var(--line);
        font-family: var(--mono); font-size: 10.5px; color: var(--ink-faint);
        display: flex; flex-wrap: wrap; gap: 4px 10px; }
.track { position: relative; height: 9px; border-radius: 4px; background: var(--sunk);
         overflow: hidden; display: flex; gap: 2px; }
.track.tall { height: 22px; border-radius: 5px; }
.fill { height: 100%; border-radius: 4px; }
.fill.hatch { background-image: repeating-linear-gradient(135deg, currentColor 0 2px,
              transparent 2px 6px);
              background-color: color-mix(in srgb, currentColor 13%, transparent); }
.marker-wrap { position: relative; }
.marker { position: absolute; top: -3px; bottom: -3px; width: 2px;
          background: var(--ink); border-radius: 1px; }
svg.spark { width: 100%; height: auto; display: block; overflow: visible; }
.chip { font-family: var(--mono); font-size: 11px; padding: 2px 7px; border-radius: 4px;
        background: var(--sunk); color: var(--ink-soft); }
.chip-crit { background: var(--crit-wash); color: var(--crit); }
.chip-warn { background: var(--warn-wash); color: var(--warn); }
.chip-good { background: var(--good-wash); color: var(--good); }
.chip-bet-1 { background: var(--bet-1-wash); color: var(--bet-1); }
.chip-bet-2 { background: var(--bet-2-wash); color: var(--bet-2); }
.unknown { color: var(--ink-faint); font-style: italic; }
.contested { border-left: 3px solid var(--warn); padding-left: 10px; }
.contested ul { margin: 6px 0; padding-left: 18px; }
.table-scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-family: var(--mono);
        font-size: 11.5px; font-variant-numeric: tabular-nums; }
th, td { text-align: right; padding: 4px 10px 4px 0; vertical-align: top; }
th { white-space: nowrap; }
th:first-child, td:first-child { text-align: left; white-space: nowrap; }
th { color: var(--ink-faint); font-weight: 500; border-bottom: 1px solid var(--line); }
.view { display: block; }
body.js .view[hidden] { display: none; }
@media (max-width: 1080px) { .layout { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 760px) { .panels { grid-template-columns: minmax(0, 1fr); } }
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
"""


STYLESHEET = (
    ":root {\n" + _emit(TOKENS["light"]) + _FONTS + "}\n"
    "@media (prefers-color-scheme: dark) {\n"
    '  :root:not([data-theme="light"]) {\n' + _emit(TOKENS["dark"]) + "  }\n}\n"
    ':root[data-theme="dark"] {\n' + _emit(TOKENS["dark"]) + "}\n"
    + _BASE
)
