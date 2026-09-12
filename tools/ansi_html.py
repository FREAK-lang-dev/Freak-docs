#!/usr/bin/env python3
"""Render captured terminal output as HTML.

A small terminal model rather than a plain escape-stripper, because FREAK
examples legitimately use carriage returns and cursor movement to redraw a
line. Replaying those onto a grid means the documentation shows what a
terminal shows, instead of a soup of escapes or a misleading pile of
half-finished lines.

Handles:
  - SGR (ESC[...m): attributes, 16 colours, 256-colour, truecolour, and the
    selective resets (22/23/24/27/28/29/39/49)
  - CR, LF
  - CUU (ESC[nA) cursor up, CUD (ESC[nB) cursor down
  - EL  (ESC[nK) erase in line
  - ED  (ESC[2J) erase display

Anything else is consumed and ignored, which is what a terminal does with a
sequence it does not implement.

Self-test:  python tools/ansi_html.py
"""

from __future__ import annotations

import html
import re

CSI_SEQ = re.compile(r"\x1b\[([0-9;?]*)([A-Za-z])")

# xterm's 16 base colours, tuned to stay legible on the dark ground the
# documentation paints behind terminal output.
ANSI_BASE = [
    "#3b3b46", "#c8322a", "#1f8f4e", "#a06f00",
    "#2f5fc0", "#a03fb0", "#0f8a9e", "#c9c9d4",
    "#7b7b8a", "#e8564c", "#3fbe72", "#c99400",
    "#5a86e0", "#c163d0", "#37abbd", "#ffffff",
]

DEFAULT_FG = "#d7d7e0"
DEFAULT_BG = "#16161d"


def xterm256(n: int) -> str:
    """Resolve an xterm 256-colour index to a hex string."""
    if n < 16:
        return ANSI_BASE[n]
    if n < 232:
        n -= 16
        levels = (0, 95, 135, 175, 215, 255)
        r, g, b = levels[n // 36], levels[(n // 6) % 6], levels[n % 6]
        return f"#{r:02x}{g:02x}{b:02x}"
    v = 8 + (n - 232) * 10
    return f"#{v:02x}{v:02x}{v:02x}"


def blank_style() -> dict:
    return {"bold": False, "dim": False, "italic": False, "underline": False,
            "strike": False, "reverse": False, "hidden": False,
            "fg": None, "bg": None}


def apply_sgr(style: dict, params: str) -> None:
    """Fold one SGR parameter list into the running style."""
    codes = [int(c) for c in params.split(";") if c.isdigit()] or [0]
    i = 0
    while i < len(codes):
        c = codes[i]
        if c == 0:
            style.update(blank_style())
        elif c == 1:
            style["bold"] = True
        elif c == 2:
            style["dim"] = True
        elif c == 3:
            style["italic"] = True
        elif c == 4:
            style["underline"] = True
        elif c == 7:
            style["reverse"] = True
        elif c == 8:
            style["hidden"] = True
        elif c == 9:
            style["strike"] = True
        elif c == 22:
            style["bold"] = style["dim"] = False
        elif c == 23:
            style["italic"] = False
        elif c == 24:
            style["underline"] = False
        elif c == 27:
            style["reverse"] = False
        elif c == 28:
            style["hidden"] = False
        elif c == 29:
            style["strike"] = False
        elif 30 <= c <= 37:
            style["fg"] = ANSI_BASE[c - 30]
        elif 90 <= c <= 97:
            style["fg"] = ANSI_BASE[c - 90 + 8]
        elif 40 <= c <= 47:
            style["bg"] = ANSI_BASE[c - 40]
        elif 100 <= c <= 107:
            style["bg"] = ANSI_BASE[c - 100 + 8]
        elif c == 39:
            style["fg"] = None
        elif c == 49:
            style["bg"] = None
        elif c in (38, 48) and i + 1 < len(codes):
            key = "fg" if c == 38 else "bg"
            mode = codes[i + 1]
            if mode == 5 and i + 2 < len(codes):
                style[key] = xterm256(codes[i + 2])
                i += 2
            elif mode == 2 and i + 4 < len(codes):
                style[key] = f"rgb({codes[i+2]},{codes[i+3]},{codes[i+4]})"
                i += 4
        i += 1


def css_for(style: dict) -> str:
    fg, bg = style["fg"], style["bg"]
    if style["reverse"]:
        fg, bg = bg or DEFAULT_BG, fg or DEFAULT_FG
    out = []
    if style["bold"]:
        out.append("font-weight:700")
    if style["dim"]:
        out.append("opacity:.65")
    if style["italic"]:
        out.append("font-style:italic")
    deco = []
    if style["underline"]:
        deco.append("underline")
    if style["strike"]:
        deco.append("line-through")
    if deco:
        out.append("text-decoration:" + " ".join(deco))
    if style["hidden"]:
        out.append("visibility:hidden")
    if fg:
        out.append(f"color:{fg}")
    if bg:
        out.append(f"background:{bg}")
    return ";".join(out)


def _param(params: str, default: int = 1) -> int:
    digits = "".join(ch for ch in params if ch.isdigit())
    if not digits:
        return default
    return int(digits)


def render(text: str) -> str:
    """Replay `text` onto a grid and return the resulting HTML."""
    rows: list[list[tuple[str, str]]] = [[]]   # each cell is (char, css)
    row = col = 0
    style = blank_style()

    def ensure_row(r: int) -> None:
        while len(rows) <= r:
            rows.append([])

    def put(ch: str) -> None:
        nonlocal col
        ensure_row(row)
        line = rows[row]
        while len(line) < col:
            line.append((" ", ""))
        cell = (ch, css_for(style))
        if col < len(line):
            line[col] = cell
        else:
            line.append(cell)
        col += 1

    def feed(chunk: str) -> None:
        nonlocal row, col
        for ch in chunk:
            if ch == "\n":
                row += 1
                col = 0
                ensure_row(row)
            elif ch == "\r":
                col = 0
            elif ch == "\t":
                for _ in range(4 - (col % 4)):
                    put(" ")
            else:
                put(ch)

    pos = 0
    for m in CSI_SEQ.finditer(text):
        feed(text[pos:m.start()])
        pos = m.end()

        params, final = m.group(1), m.group(2)
        if final == "m":
            apply_sgr(style, params)
        elif final == "A":
            row = max(0, row - _param(params))
        elif final == "B":
            row += _param(params)
            ensure_row(row)
        elif final == "C":
            col += _param(params)
        elif final == "D":
            col = max(0, col - _param(params))
        elif final == "G":
            col = max(0, _param(params) - 1)
        elif final == "K":
            ensure_row(row)
            mode = _param(params, 0)
            line = rows[row]
            if mode == 0:
                del line[col:]
            elif mode == 1:
                for k in range(min(col + 1, len(line))):
                    line[k] = (" ", "")
            else:
                line.clear()
        elif final == "J" and _param(params, 0) == 2:
            rows = [[]]
            row = col = 0
        # every other final byte is a sequence we do not model

    feed(text[pos:])

    out_lines = []
    for line in rows:
        while line and line[-1][0] == " " and not line[-1][1]:
            line.pop()
        parts, run, run_css = [], [], None
        for ch, css in line:
            if css != run_css:
                if run:
                    parts.append((run_css, "".join(run)))
                run, run_css = [], css
            run.append(ch)
        if run:
            parts.append((run_css, "".join(run)))
        out_lines.append("".join(
            f'<span style="{css}">{html.escape(seg)}</span>' if css else html.escape(seg)
            for css, seg in parts))

    while out_lines and out_lines[-1] == "":
        out_lines.pop()
    return "\n".join(out_lines)


def has_ansi(text: str) -> bool:
    return bool(CSI_SEQ.search(text)) or "\r" in text


# --------------------------------------------------------------------------

def _selftest() -> int:
    E = chr(27)
    cases = [
        ("plain", "a\nb", "a\nb"),
        ("cr overwrite", "calculating..." + chr(13) + E + "[Kdone", "done"),
        ("cr partial", "abcdef" + chr(13) + "XY", "XYcdef"),
        ("cursor up redraw",
         "p 0%\n" + E + "[1A" + chr(13) + E + "[Kp 100%\ndone", "p 100%\ndone"),
        ("erase display", "junk" + E + "[2Jclean", "clean"),
        ("tab", "a\tb", "a   b"),
    ]
    failures = 0
    for name, raw, expect in cases:
        got = render(raw)
        flat = re.sub(r"<[^>]+>", "", got)
        ok = flat == expect
        print(f"{'ok  ' if ok else 'FAIL'}  {name:20} {flat!r}")
        if not ok:
            print(f"      expected {expect!r}")
            failures += 1

    styled = render(E + "[1;31merror" + E + "[0m: bad")
    if "font-weight:700" not in styled or "#c8322a" not in styled:
        print("FAIL  sgr styling"); failures += 1
    else:
        print("ok    sgr styling")

    if xterm256(208) != "#ff8700" or xterm256(196) != "#ff0000":
        print("FAIL  xterm256"); failures += 1
    else:
        print("ok    xterm256")

    print("\nall ansi_html checks passed" if not failures else f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
