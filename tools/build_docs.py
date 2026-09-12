#!/usr/bin/env python3
"""Generate the FREAK V3 documentation site.

Reads content/*.md (a small, fixed Markdown subset), injects verified examples
from examples/verified.json, and writes a dependency-free static site into
site/. The output works straight from the filesystem -- no server, no CDN.

Usage:
    python tools/build_docs.py
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SITE = ROOT / "site"
ASSETS = SITE / "assets"
VERIFIED = ROOT / "examples" / "verified.json"

# Sidebar order and grouping. Every entry is a content/<slug>.md file.
NAV = [
    ("Start here", [
        ("index", "Overview"),
        ("getting-started", "Getting started"),
        ("cli", "Compiler CLI"),
        ("hangar", "Hangar & packages"),
    ]),
    ("Tutorials", [
        ("tutorial-first-program", "1 · Your first program"),
        ("tutorial-cli-tool", "2 · A command-line tool"),
        ("tutorial-data", "3 · Modelling data"),
    ]),
    ("Language", [
        ("language-basics", "Bindings & types"),
        ("tasks", "Tasks"),
        ("control-flow", "Control flow"),
        ("operators", "Operators"),
        ("words", "Words & interpolation"),
        ("shapes", "Shapes & impl"),
        ("arrays", "Lists & arrays"),
        ("console", "Coloured output"),
        ("anime-layer", "Anime layer"),
        ("ffi", "extern & FFI"),
    ]),
    ("Reference", [
        ("stdlib", "Standard library"),
        ("grammar", "Grammar"),
        ("conformance", "Bible vs V3"),
        ("not-in-v3", "Not in V3"),
        ("examples", "Verified examples"),
    ]),
]

KEYWORDS = {
    "pilot", "fixed", "task", "say", "shape", "impl", "doctrine", "launch",
    "use", "as", "in", "lend", "mut", "move", "copy", "break", "continue",
    "if", "else", "when", "repeat", "times", "until", "done", "for", "each",
    "check", "result", "got", "nobody", "some", "ok", "err", "sessions",
    "max", "foreshadow", "payoff", "route", "sadly", "deus_ex_machina",
    "isekai", "eventually", "and", "or", "not", "nakama", "tsundere",
    "extern", "give back", "or else", "trust me", "for each", "for science",
    "training arc", "bringing back", "only on",
}
LITERALS = {"true", "false", "yes", "no", "hai", "iie"}
MULTIWORD = ["give back", "or else", "trust me", "for each", "for science",
             "training arc", "bringing back", "only on", "PLUS ULTRA",
             "FINAL FORM"]


# --------------------------------------------------------------------------
# FREAK syntax highlighting
# --------------------------------------------------------------------------

def highlight_fk(code: str) -> str:
    """Tokenise FREAK source into <span> runs. Operates on raw text."""
    out = []
    i = 0
    n = len(code)
    while i < n:
        ch = code[i]

        # line comment
        if ch == "-" and i + 1 < n and code[i + 1] == "-":
            j = code.find("\n", i)
            j = n if j == -1 else j
            out.append(f'<span class="c-com">{html.escape(code[i:j])}</span>')
            i = j
            continue

        # string literal, with {interpolation} highlighted inside
        if ch == '"':
            j = i + 1
            while j < n:
                if code[j] == "\\":
                    j += 2
                    continue
                if code[j] == '"':
                    j += 1
                    break
                j += 1
            raw = code[i:j]
            esc = html.escape(raw)
            esc = re.sub(r"\{([A-Za-z_][A-Za-z0-9_.]*)\}",
                         r'<span class="c-interp">{\1}</span>', esc)
            out.append(f'<span class="c-str">{esc}</span>')
            i = j
            continue

        # number
        if ch.isdigit():
            j = i
            while j < n and (code[j].isdigit() or code[j] == "."):
                j += 1
            out.append(f'<span class="c-num">{html.escape(code[i:j])}</span>')
            i = j
            continue

        # identifier / keyword (including multi-word keywords)
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (code[j].isalnum() or code[j] == "_"):
                j += 1
            word = code[i:j]

            matched = None
            for phrase in MULTIWORD:
                head = phrase.split()[0]
                if word.lower() == head.lower():
                    look = code[i:i + len(phrase) + 4]
                    m = re.match(r"(\w+)(\s+)(\w+)", look)
                    if m and f"{m.group(1)} {m.group(3)}".lower() == phrase.lower():
                        matched = i + len(m.group(0))
                        break
            if matched:
                out.append(f'<span class="c-kw">{html.escape(code[i:matched])}</span>')
                i = matched
                continue

            low = word.lower()
            if low in LITERALS:
                cls = "c-lit"
            elif low in KEYWORDS:
                cls = "c-kw"
            elif word in ("int", "num", "word", "bool", "void", "self"):
                cls = "c-type"
            elif j < n and code[j] == "(":
                cls = "c-fn"
            elif word[:1].isupper():
                cls = "c-type"
            else:
                cls = ""
            token = html.escape(word)
            out.append(f'<span class="{cls}">{token}</span>' if cls else token)
            i = j
            continue

        # annotation
        if ch == "@":
            j = i + 1
            while j < n and (code[j].isalnum() or code[j] == "_"):
                j += 1
            out.append(f'<span class="c-attr">{html.escape(code[i:j])}</span>')
            i = j
            continue

        if ch in "+-*/%<>=!|?:&":
            j = i
            while j < n and code[j] in "+-*/%<>=!|?:&":
                j += 1
            out.append(f'<span class="c-op">{html.escape(code[i:j])}</span>')
            i = j
            continue

        out.append(html.escape(ch))
        i += 1

    return "".join(out)


# --------------------------------------------------------------------------
# Terminal output rendering lives in ansi_html.py
# --------------------------------------------------------------------------

from ansi_html import render as ansi_to_html, has_ansi   # noqa: E402


# --------------------------------------------------------------------------
# Inline markdown
# --------------------------------------------------------------------------

def split_row(row: str) -> list[str]:
    """Split a table row on cell boundaries only.

    A '|' is a boundary unless it is backslash-escaped or sits inside a
    `code span`, so rows may talk about the pipe operator without contortions.
    """
    guard = "\x00PIPE\x00"
    protected = re.sub(r"`[^`]*`",
                       lambda m: m.group(0).replace("|", guard), row)
    cells = re.split(r"(?<!\\)\|", protected.strip().strip("|"))
    return [c.replace(guard, "|").strip() for c in cells]


def inline(text: str) -> str:
    """`code`, **bold**, *italic*, [label](href) -- escaping everything else."""
    text = text.replace("\\|", "|")
    parts = re.split(r"(`[^`]+`)", text)
    rendered = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            rendered.append(f"<code>{html.escape(part[1:-1])}</code>")
            continue
        seg = html.escape(part)
        seg = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', seg)
        seg = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", seg)
        seg = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", seg)
        rendered.append(seg)
    return "".join(rendered)


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_]+", "-", s) or "section"


# --------------------------------------------------------------------------
# Example cards
# --------------------------------------------------------------------------

def example_card(name: str, data: dict, mode: str = "full") -> str:
    ex = data["examples"].get(name)
    if ex is None:
        return f'<div class="callout warn"><p>Missing example: {html.escape(name)}</p></div>'

    ok = ex["compiled"]
    badge = ('<span class="badge ok">compiles</span>' if ok
             else '<span class="badge bad">does not compile</span>')
    ran = ex.get("ran")
    if ok and ran:
        badge += '<span class="badge ok">runs</span>'

    body = [
        '<figure class="example">',
        '  <figcaption>',
        f'    <span class="ex-name">examples/{html.escape(ex["file"])}</span>',
        f'    <span class="ex-badges">{badge}</span>',
        '  </figcaption>',
        f'  <pre class="code"><code>{highlight_fk(ex["source"].rstrip())}</code></pre>',
    ]

    if mode == "full" and ex.get("stdout"):
        raw = ex["stdout"]
        coloured = has_ansi(raw)
        label = "Program output (ANSI rendered)" if coloured else "Program output"
        rendered = ansi_to_html(raw) if coloured else html.escape(raw)
        cls = "stdout term" if coloured else "stdout"
        body.append('  <div class="ex-out">')
        body.append(f'    <div class="ex-out-head">{label}</div>')
        body.append(f'    <pre class="{cls}"><code>{rendered}</code></pre>')
        body.append('  </div>')

    if not ok and ex.get("errors"):
        errs = "\n".join(ex["errors"])
        body.append(f'  <pre class="stdout err"><code>{html.escape(errs)}</code></pre>')

    body.append("</figure>")
    return "\n".join(body)


# --------------------------------------------------------------------------
# Block markdown
# --------------------------------------------------------------------------

CALLOUT_KINDS = {"note": "note", "warn": "warn", "v4": "v4", "tip": "tip"}


def render_blocks(lines: list[str], data: dict, headings: list, search_rows: list,
                  page_slug: str, page_title: str) -> str:
    out = []
    i = 0
    n = len(lines)

    def push_search(anchor, heading, text):
        """Index a section as one or more ~700-character chunks.

        Chunking rather than truncating means a term late in a long section is
        still findable, while each snippet stays tight enough to be readable.
        """
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return
        limit = 700
        words = text.split(" ")
        chunk: list[str] = []
        size = 0
        chunks: list[str] = []
        for w in words:
            if size + len(w) + 1 > limit and chunk:
                chunks.append(" ".join(chunk))
                chunk, size = [], 0
            chunk.append(w)
            size += len(w) + 1
        if chunk:
            chunks.append(" ".join(chunk))
        for part in chunks:
            search_rows.append({
                "p": page_slug, "t": page_title,
                "a": anchor, "h": heading, "x": part,
            })

    current_anchor = ""
    current_heading = page_title
    buffer_text = []

    def flush_search():
        nonlocal buffer_text
        if buffer_text:
            push_search(current_anchor, current_heading, " ".join(buffer_text))
            buffer_text = []

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # directives
        m = re.fullmatch(r"\{\{example:([\w-]+)(\|source)?\}\}", stripped)
        if m:
            out.append(example_card(m.group(1), data,
                                    "source" if m.group(2) else "full"))
            ex = data["examples"].get(m.group(1))
            if ex:
                buffer_text.append(ex["source"])
            i += 1
            continue

        if stripped == "{{verified-summary}}":
            out.append(
                '<div class="summary-card">'
                f'<div class="sc-num">{data["compiled"]}/{data["total"]}</div>'
                '<div class="sc-body"><strong>documentation examples compile</strong>'
                f'<span>Verified with {html.escape(data["compiler"])} on '
                f'{html.escape(data["generated_utc"])}. Every code block on this '
                'site marked <em>compiles</em> was built by that compiler and, '
                'where it produces output, executed.</span></div></div>'
            )
            i += 1
            continue

        # headings
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            anchor = slugify(text)
            flush_search()
            current_anchor = anchor
            current_heading = text
            if level <= 3:
                headings.append({"level": level, "text": text, "anchor": anchor})
            out.append(
                f'<h{level} id="{anchor}">{inline(text)}'
                f'<a class="anchor" href="#{anchor}" aria-label="Link to this section">#</a>'
                f"</h{level}>"
            )
            i += 1
            continue

        # fenced code
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "text"
            i += 1
            block = []
            while i < n and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            code = "\n".join(block)
            buffer_text.append(code)
            rendered = highlight_fk(code) if lang == "fk" else html.escape(code)
            label = {"fk": "FREAK", "sh": "shell", "text": "", "toml": "TOML"}.get(lang, lang)
            tag = f'<span class="code-lang">{label}</span>' if label else ""
            out.append(f'<div class="codeblock">{tag}'
                       f'<pre class="code"><code>{rendered}</code></pre></div>')
            continue

        # callout
        m = re.match(r">\s*\[!(\w+)\]\s*(.*)", stripped)
        if m and m.group(1).lower() in CALLOUT_KINDS:
            kind = CALLOUT_KINDS[m.group(1).lower()]
            body = [m.group(2)]
            i += 1
            while i < n and lines[i].strip().startswith(">"):
                body.append(lines[i].strip().lstrip(">").strip())
                i += 1
            text = " ".join(x for x in body if x)
            buffer_text.append(text)
            titles = {"note": "Note", "warn": "Careful", "v4": "Not in V3", "tip": "Tip"}
            out.append(f'<div class="callout {kind}">'
                       f'<div class="callout-title">{titles[kind]}</div>'
                       f"<p>{inline(text)}</p></div>")
            continue

        # table
        if stripped.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            if len(rows) >= 2 and set(rows[1].replace("|", "").strip()) <= set("-: "):
                head = split_row(rows[0])
                body_rows = [split_row(r) for r in rows[2:]]
                buffer_text.append(" ".join(head))
                for r in body_rows:
                    buffer_text.append(" ".join(r))
                thead = "".join(f"<th>{inline(c)}</th>" for c in head)
                tbody = "".join(
                    "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                    for r in body_rows
                )
                out.append('<div class="tablewrap"><table>'
                           f"<thead><tr>{thead}</tr></thead>"
                           f"<tbody>{tbody}</tbody></table></div>")
                continue
            for r in rows:
                out.append(f"<p>{inline(r)}</p>")
            continue

        # lists
        if re.match(r"[-*]\s+", stripped) or re.match(r"\d+\.\s+", stripped):
            ordered = bool(re.match(r"\d+\.\s+", stripped))
            items = []
            while i < n:
                s = lines[i].strip()
                if not s:
                    break
                m2 = re.match(r"(?:[-*]|\d+\.)\s+(.*)", s)
                if not m2:
                    if items:
                        items[-1] += " " + s
                        i += 1
                        continue
                    break
                items.append(m2.group(1))
                i += 1
            buffer_text.extend(items)
            tag = "ol" if ordered else "ul"
            body = "".join(f"<li>{inline(x)}</li>" for x in items)
            out.append(f"<{tag}>{body}</{tag}>")
            continue

        # paragraph
        para = [stripped]
        i += 1
        while i < n and lines[i].strip() and not re.match(
                r"^(#|```|\||[-*]\s|\d+\.\s|>|\{\{)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        text = " ".join(para)
        buffer_text.append(text)
        out.append(f"<p>{inline(text)}</p>")

    flush_search()
    return "\n".join(out)


# --------------------------------------------------------------------------
# Page shell
# --------------------------------------------------------------------------

def sidebar_html(active: str) -> str:
    parts = ['<nav class="sidebar-nav">']
    for group, items in NAV:
        parts.append(f'<div class="nav-group"><div class="nav-group-title">{group}</div><ul>')
        for slug, label in items:
            cls = ' class="active"' if slug == active else ""
            parts.append(f'<li><a href="{slug}.html"{cls}>{label}</a></li>')
        parts.append("</ul></div>")
    parts.append("</nav>")
    return "\n".join(parts)


def toc_html(headings: list) -> str:
    items = [h for h in headings if h["level"] == 2]
    if len(items) < 2:
        return ""
    links = "".join(
        f'<li><a href="#{h["anchor"]}">{html.escape(h["text"])}</a></li>'
        for h in items
    )
    return f'<aside class="toc"><div class="toc-title">On this page</div><ul>{links}</ul></aside>'


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; FREAK V3</title>
<meta name="description" content="{desc}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#128165;</text></svg>">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <button class="menu-toggle" aria-label="Toggle navigation">&#9776;</button>
  <a class="brand" href="index.html"><span class="brand-mark">FREAK</span><span class="brand-sub">V3 docs</span></a>
  <div class="searchbox">
    <input type="search" id="q" placeholder="Search the docs&hellip;  (press /)" autocomplete="off" spellcheck="false" aria-label="Search documentation">
    <div id="results" class="results" hidden></div>
  </div>
  <span class="compiler-tag">{compiler}</span>
</header>
<div class="layout">
  <aside class="sidebar">{sidebar}</aside>
  <main id="main">
    <article class="prose">
{body}
    </article>
    <footer class="pagefoot">
      <p>Every FREAK snippet on this site was compiled by <strong>{compiler}</strong>,
      built from source with a verified self-host fixed point.
      {compiled}/{total} examples compile; regenerate with
      <code>python tools/verify.py</code> then <code>python tools/build_docs.py</code>.</p>
    </footer>
  </main>
  {toc}
</div>
<script src="assets/search-index.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
"""


def main() -> int:
    data = json.loads(VERIFIED.read_text(encoding="utf-8"))
    ASSETS.mkdir(parents=True, exist_ok=True)

    search_rows: list[dict] = []
    pages = [(slug, label) for _, items in NAV for slug, label in items]

    for slug, label in pages:
        src = CONTENT / f"{slug}.md"
        if not src.exists():
            print(f"  ! missing content/{slug}.md")
            continue
        lines = src.read_text(encoding="utf-8").split("\n")

        title = label
        desc = ""
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
        for ln in lines[:6]:
            if ln.startswith("> ") and not ln.startswith("> [!"):
                desc = ln[2:].strip()
                break

        headings: list = []
        body = render_blocks(lines, data, headings, search_rows, slug, title)

        page = PAGE.format(
            title=html.escape(title),
            desc=html.escape(desc or f"FREAK V3 documentation: {title}"),
            sidebar=sidebar_html(slug),
            body=body,
            toc=toc_html(headings),
            compiler=html.escape(data["compiler"]),
            compiled=data["compiled"],
            total=data["total"],
        )
        (SITE / f"{slug}.html").write_text(page, encoding="utf-8")
        print(f"  wrote site/{slug}.html")

    index_js = "window.SEARCH_INDEX = " + json.dumps(search_rows, separators=(",", ":")) + ";"
    (ASSETS / "search-index.js").write_text(index_js, encoding="utf-8")
    print(f"  wrote site/assets/search-index.js ({len(search_rows)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
