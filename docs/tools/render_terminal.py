#!/usr/bin/env python3
"""Render captured terminal output (text files from Scripts/audit-check.sh)
as flat terminal-window SVGs for the README.

    python3 docs/tools/render_terminal.py <out.svg> <title> <file.txt> [<file.txt> ...]

The text is drawn as-is: this only changes how real output looks, never what
it says. Lines starting with "$ " are commands; everything else is output.
"""
import html
import re
import sys

INK, PANEL2, BONE = "#0E0F12", "#1B1D23", "#EFE9DD"
ROSE, SOFT, MUTED, DIM = "#EA5F70", "#A3A4AB", "#8D8F98", "#5C5E66"
AMBER, CARMINE = "#F2A93B", "#B0122B"
HAIR = "rgba(239,233,221,.14)"
MONO = "'JetBrains Mono', 'SFMono-Regular', Menlo, Consolas, monospace"

FS, LH, CW = 12.5, 18, 7.55          # font size, line height, char width
PAD, BAR = 20, 34

GOOD = re.compile(r"\b(Ready|Running|Bound|Available|HTTP 20[01]|Message posted|condition met|"
                  r"scaled|1/1|3/3|PASS|[0-9]+ passed|0 failed)\b")
WARN = re.compile(r"(<unknown>|Pending|ContainerCreating|Terminating|0/1|<none>)")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def colour_output(line):
    """Escape a line and tint status words; the text itself is unchanged."""
    out, pos = [], 0
    spans = sorted([(m.start(), m.end(), BONE, 700) for m in GOOD.finditer(line)] +
                   [(m.start(), m.end(), AMBER, 400) for m in WARN.finditer(line)])
    for start, end, fill, weight in spans:
        if start < pos:
            continue
        out.append(html.escape(line[pos:start]))
        out.append(f'<tspan fill="{fill}" font-weight="{weight}">{html.escape(line[start:end])}</tspan>')
        pos = end
    out.append(html.escape(line[pos:]))
    return "".join(out)


def main():
    out_path, title, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    lines = []
    for i, path in enumerate(files):
        text = ANSI.sub("", open(path).read()).rstrip("\n").expandtabs(8)
        if i:
            lines.append("")
        lines.extend(text.split("\n"))

    width = int(PAD * 2 + max(len(l) for l in lines) * CW)
    width = max(width, 520)
    height = BAR + PAD + len(lines) * LH + PAD - 6

    body = []
    y = BAR + PAD + FS
    for line in lines:
        if line.startswith("$ "):
            body.append(f'<text x="{PAD}" y="{y}"><tspan fill="{ROSE}" font-weight="700">❯</tspan>'
                        f'<tspan fill="{BONE}" dx="{CW}">{html.escape(line[2:])}</tspan></text>')
        else:
            body.append(f'<text x="{PAD}" y="{y}" fill="{SOFT}" xml:space="preserve">{colour_output(line)}</text>')
        y += LH

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{MONO}" font-size="{FS}">
<rect width="{width}" height="{height}" fill="{INK}"/>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" fill="none" stroke="{HAIR}"/>
<rect x="1" y="1" width="{width - 2}" height="{BAR - 1}" fill="{PANEL2}"/>
<line x1="0" y1="{BAR}" x2="{width}" y2="{BAR}" stroke="{HAIR}"/>
<rect x="14" y="13" width="9" height="9" fill="{CARMINE}"/>
<rect x="29" y="13" width="9" height="9" fill="{DIM}"/>
<rect x="44" y="13" width="9" height="9" fill="{DIM}"/>
<text x="66" y="21.5" fill="{MUTED}" font-size="11" letter-spacing="1.4">{html.escape(title.upper())}</text>
<text x="{width - 14}" y="21.5" fill="{DIM}" font-size="11" text-anchor="end">abdulla@alasmawi</text>
{chr(10).join(body)}
</svg>
"""
    open(out_path, "w").write(svg)


if __name__ == "__main__":
    main()
