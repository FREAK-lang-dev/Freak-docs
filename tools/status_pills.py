#!/usr/bin/env python3
"""Inline SVG status pills for conformance markers.

The documentation mirrors the bible's implementation-status legend, which the
specification writes with emoji. Emoji render inconsistently across platforms,
carry no accessible name, and cannot inherit the surrounding colour, so the
docs use inline SVG pills instead.

Markdown shorthand, usable anywhere inline markdown is processed:

    :shipped:   works end to end            (green,  check)
    :partial:   parsed, guarantee incomplete (amber, warning triangle)
    :v4:        specified, not in V3         (violet, forward arrow)
    :planned:   not started                  (slate,  dashed circle)

Icons are lucide-style: 24-unit viewBox, currentColor stroke, no fill, so a
pill's single colour rule drives both glyph and text.

Self-test:  python tools/status_pills.py
"""

from __future__ import annotations

import re

_SVG_OPEN = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
)

# Glyph geometry, keyed by pill name.
_PATHS = {
    "shipped": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "partial": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16'
        'a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>'
    ),
    "v4": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "planned": '<circle cx="12" cy="12" r="10" stroke-dasharray="3 3"/>',
}

_LABELS = {
    "shipped": "Ships",
    "partial": "Partial",
    "v4": "V4",
    "planned": "Planned",
}

_CLASSES = {
    "shipped": "status-shipped",
    "partial": "status-partial",
    "v4": "status-v4",
    "planned": "status-planned",
}

TOKEN_RE = re.compile(r":(shipped|partial|v4|planned):")


def pill(kind: str) -> str:
    """Render one status pill as inline SVG plus its label."""
    label = _LABELS[kind]
    return (
        f'<span class="status-pill {_CLASSES[kind]}" role="img" '
        f'aria-label="{label}">'
        f'{_SVG_OPEN}{_PATHS[kind]}</svg>{label}</span>'
    )


def expand(text: str) -> str:
    """Replace every :kind: token in already-escaped HTML."""
    return TOKEN_RE.sub(lambda m: pill(m.group(1)), text)


def _selftest() -> int:
    failures = 0
    for kind in _PATHS:
        out = pill(kind)
        for needle in ("<svg", "</svg>", _CLASSES[kind], _LABELS[kind], "aria-label"):
            if needle not in out:
                print(f"FAIL  {kind}: missing {needle}")
                failures += 1
        if out.count("<span") != 1 or out.count("</span>") != 1:
            print(f"FAIL  {kind}: unbalanced span")
            failures += 1

    sample = "Row :shipped: and :v4: and :partial: and :planned:."
    got = expand(sample)
    if got.count("<span") != 4:
        print("FAIL  expand did not replace every token")
        failures += 1
    if ":shipped:" in got or ":v4:" in got:
        print("FAIL  expand left a token behind")
        failures += 1
    if expand("no tokens here") != "no tokens here":
        print("FAIL  expand altered plain text")
        failures += 1

    print("all status_pills checks passed" if not failures else f"{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
