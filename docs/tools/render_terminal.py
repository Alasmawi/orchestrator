#!/usr/bin/env python3
"""Render captured terminal output (text files from Scripts/audit-check.sh)
as terminal-window SVGs for the README.

    python3 docs/tools/render_terminal.py <out.svg> <title> <file.txt> [<file.txt> ...]

The text is drawn as-is: this only changes how real output looks, never what
it says. Lines starting with "$ " are commands; everything else is output.
"""
import html
import re
import sys

# Classic terminal window, matching the light cloud diagrams in docs/.
BODY, BAR_BG, EDGE = "#1F2430", "#ECEEF1", "#C9CED6"
CMD, OUT, GOOD_C, WARN_C, PROMPT = "#FFFFFF", "#C9D1D9", "#7EE787", "#E3B341", "#28C840"
TITLE_C = "#545B64"
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
    spans = sorted([(m.start(), m.end(), GOOD_C, 700) for m in GOOD.finditer(line)] +
                   [(m.start(), m.end(), WARN_C, 400) for m in WARN.finditer(line)])
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
            body.append(f'<text x="{PAD}" y="{y}"><tspan fill="{PROMPT}" font-weight="700">❯</tspan>'
                        f'<tspan fill="{CMD}" font-weight="700" dx="{CW}">{html.escape(line[2:])}</tspan></text>')
        else:
            body.append(f'<text x="{PAD}" y="{y}" fill="{OUT}" xml:space="preserve">{colour_output(line)}</text>')
        y += LH

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{MONO}" font-size="{FS}">
<clipPath id="win"><rect width="{width}" height="{height}" rx="10"/></clipPath>
<g clip-path="url(#win)">
<rect width="{width}" height="{height}" fill="{BODY}"/>
<rect width="{width}" height="{BAR}" fill="{BAR_BG}"/>
<line x1="0" y1="{BAR}" x2="{width}" y2="{BAR}" stroke="{EDGE}"/>
</g>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="none" stroke="{EDGE}"/>
<circle cx="20" cy="17" r="6" fill="#FF5F57"/><circle cx="40" cy="17" r="6" fill="#FEBC2E"/><circle cx="60" cy="17" r="6" fill="#28C840"/>
<text x="{width / 2}" y="21.5" fill="{TITLE_C}" font-size="12" font-weight="600" text-anchor="middle" font-family="'Inter','Segoe UI','Helvetica Neue',Arial,sans-serif">{html.escape(title)}</text>
{chr(10).join(body)}
</svg>
"""
    open(out_path, "w").write(svg)


if __name__ == "__main__":
    main()
