# Coloured output

> There is no colour library. You write ANSI escape sequences into `word` values yourself — so this page is the full code reference.

FREAK has no `std::term`, no `Color` type and no formatting helpers. Colour
works because two things are true:

1. The lexer supports `\xNN` byte escapes and passes them through to the backend
   untouched.
2. Every compiled FREAK program enables ANSI processing at startup.

That is enough. Colour constants are ordinary `word` bindings, concatenated with
`+`. The compiler's own CLI is written this way, so it doubles as the reference
implementation.

{{example:colour}}

## Anatomy of a sequence

Everything below is a **CSI** sequence — `ESC [` followed by parameters and a
single final letter that selects the operation:

```text
\x1b [ params <final>
 │     │       └── the operation: `m` = set graphics, `H` = move cursor, …
 │     └────────── numeric parameters, `;` separated
 └──────────────── ESC, decimal 27, written \x1b in a FREAK word
```

`\x1b` is the only part that needs escaping; `[`, the digits, the semicolons and
the final letter are ordinary characters.

Sequences ending in `m` are **SGR** (Select Graphic Rendition) — colour and
text style. Everything else moves the cursor or edits the screen.

Multiple parameters combine in one sequence, which is cheaper and more reliable
than emitting several:

```fk
say "\x1b[1;4;31m" + "bold underlined red" + "\x1b[0m"
```

{{example:ansi_codes}}

> [!note]
> That output block is the program's real bytes, re-rendered as HTML. Two
> swatches look odd on purpose: **blink** appears unstyled, because this page
> does not animate it and many terminals ignore it too; and **hidden** appears
> blank, because that is what `8` does. Non-SGR sequences are dropped from the
> rendering rather than shown as garbage.

## SGR: attributes

Each attribute has a matching off-switch, so you can turn one thing off without
resetting everything.

| On | Off | Effect |
|---|---|---|
| `0` | — | Reset all attributes and colours |
| `1` | `22` | Bold / increased intensity |
| `2` | `22` | Dim / faint |
| `3` | `23` | Italic |
| `4` | `24` | Underline |
| `5` | `25` | Slow blink |
| `6` | `25` | Rapid blink — rarely implemented |
| `7` | `27` | Reverse video (swap foreground and background) |
| `8` | `28` | Conceal / hidden |
| `9` | `29` | Crossed out / strikethrough |
| `21` | `24` | Double underline — sometimes "bold off" instead |
| `51` | `54` | Framed |
| `52` | `54` | Encircled |
| `53` | `55` | Overlined |

Note that `22` clears **both** bold and dim, since they share an intensity
channel.

## SGR: foreground colour

| Code | Colour | Code | Bright variant |
|---|---|---|---|
| `30` | Black | `90` | Bright black (grey) |
| `31` | Red | `91` | Bright red |
| `32` | Green | `92` | Bright green |
| `33` | Yellow | `93` | Bright yellow |
| `34` | Blue | `94` | Bright blue |
| `35` | Magenta | `95` | Bright magenta |
| `36` | Cyan | `96` | Bright cyan |
| `37` | White | `97` | Bright white |
| `39` | **Default foreground** | | |

## SGR: background colour

| Code | Colour | Code | Bright variant |
|---|---|---|---|
| `40` | Black | `100` | Bright black (grey) |
| `41` | Red | `101` | Bright red |
| `42` | Green | `102` | Bright green |
| `43` | Yellow | `103` | Bright yellow |
| `44` | Blue | `104` | Bright blue |
| `45` | Magenta | `105` | Bright magenta |
| `46` | Cyan | `106` | Bright cyan |
| `47` | White | `107` | Bright white |
| `49` | **Default background** | | |

## SGR: extended colour

`38` sets the foreground and `48` the background, each with two sub-forms
selected by the next parameter.

| Sequence | Meaning |
|---|---|
| `\x1b[38;5;Nm` | Foreground from the 256-colour palette, `N` = 0–255 |
| `\x1b[48;5;Nm` | Background from the 256-colour palette |
| `\x1b[38;2;R;G;Bm` | Foreground, 24-bit truecolour, each channel 0–255 |
| `\x1b[48;2;R;G;Bm` | Background, 24-bit truecolour |
| `\x1b[58;5;Nm` | Underline colour — an extension, patchy support |
| `\x1b[59m` | Default underline colour |

The 256-colour index is laid out in three blocks:

| Range | Contents |
|---|---|
| `0`–`7` | The standard colours, same as `30`–`37` |
| `8`–`15` | The bright colours, same as `90`–`97` |
| `16`–`231` | A 6×6×6 RGB cube |
| `232`–`255` | 24 greys, dark to light |

The cube index is `16 + 36*r + 6*g + b`, where each of `r`, `g`, `b` is 0–5:

```fk
task cube(r: int, g: int, b: int) -> word {
    give back "\x1b[38;5;" + word_from_int(16 + 36 * r + 6 * g + b) + "m"
}
```

Truecolour is the simplest option when you know the exact shade you want:

```fk
task rgb(r: int, g: int, b: int) -> word {
    give back "\x1b[38;2;" + word_from_int(r) + ";" + word_from_int(g) + ";" + word_from_int(b) + "m"
}
```

## Cursor and screen control

These are CSI sequences with a final letter other than `m`. They pass through
V3 exactly the same way — they are just bytes — but they act on the terminal
rather than on the text, so they cannot be shown in a captured output block.

| Sequence | Effect |
|---|---|
| `\x1b[nA` | Cursor up `n` rows |
| `\x1b[nB` | Cursor down `n` rows |
| `\x1b[nC` | Cursor forward `n` columns |
| `\x1b[nD` | Cursor back `n` columns |
| `\x1b[nE` | Cursor to start of line, `n` rows down |
| `\x1b[nF` | Cursor to start of line, `n` rows up |
| `\x1b[nG` | Cursor to column `n` |
| `\x1b[row;colH` | Cursor to an absolute position, 1-based |
| `\x1b[nJ` | Erase display — `0` to end, `1` to start, `2` all, `3` all plus scrollback |
| `\x1b[nK` | Erase line — `0` to end, `1` to start, `2` whole line |
| `\x1b[nS` | Scroll up `n` lines |
| `\x1b[nT` | Scroll down `n` lines |
| `\x1b[s` | Save cursor position |
| `\x1b[u` | Restore saved cursor position |
| `\x1b[?25l` | Hide the cursor |
| `\x1b[?25h` | Show the cursor |
| `\x1b[?1049h` | Switch to the alternate screen buffer |
| `\x1b[?1049l` | Return to the main screen buffer |

A progress line, using carriage return plus erase-to-end:

```fk
task main() -> void {
    pilot mut i: int = 0
    repeat 5 times {
        i += 1
        say "\r\x1b[K" + "working " + word_from_int(i) + "/5"
    }
    say ""
}
```

> [!note]
> `say` always appends a newline, so a true in-place progress indicator is not
> possible with it — each call moves to the next line regardless. The snippet
> above redraws on successive lines. V3 has no unbuffered write, so if you need
> real single-line progress you must go through the C runtime.

## ANSI is enabled for you

On Windows, escapes only work when the console has
`ENABLE_VIRTUAL_TERMINAL_PROCESSING` set. The runtime does this for **every**
FREAK program, not just the CLI:

- `freak_enable_ansi()` in `freakc/runtime/freak_runtime.c` sets the flag on
  both stdout and stderr.
- The C backend emits a direct `freak_enable_ansi();` call into `main`.
- The LLVM backend calls it via `freak_llvm_setup_args`, which the emitted
  `main` invokes with `argc`/`argv`.

So nothing platform-specific is needed on your side. On POSIX the call is a
no-op.

## The escape itself

`\x1b` is one of a small set of byte escapes the lexer understands:

| Escape | Byte |
|---|---|
| `\n` | newline |
| `\r` | carriage return |
| `\t` | tab |
| `\"` | double quote |
| `\\` | backslash |
| `\xNN` | any byte, two hex digits |

The lexer's hex branch re-emits `\xNN` as that literal two-character sequence
specifically so the C and LLVM emitters pass it straight into the generated
string constant. Nothing in the pipeline interprets it.

> [!warn]
> `\x00` is rejected at lex time — *"embedded NUL escape is not supported"* —
> because V3 words are NUL-terminated at runtime. A malformed hex escape (fewer
> than two hex digits) is also a lex error.

## The CLI's palette

`src/cli/version.fk` declares its whole palette as top-level `pilot` bindings.
That file is plain FREAK compiled by V3, so it is a worked example you can copy.

| Group | Constants |
|---|---|
| Styles | `C_RESET` `C_BOLD` `C_DIM` `C_ITALIC` `C_ULINE` `C_BLINK` `C_STRIKE` |
| Standard | `C_RED` `C_GREEN` `C_YELLOW` `C_BLUE` `C_MAGENTA` `C_CYAN` `C_WHITE` |
| Bold | `C_BRED` `C_BGREEN` `C_BYELLOW` `C_BBLUE` `C_BMAGENTA` `C_BCYAN` `C_BWHITE` |
| Truecolour gradient | `C_G1`…`C_G6` — pink → purple → blue → cyan |
| Background | `C_BG_DARK` = `\x1b[48;2;20;20;30m` |

The gradient is what produces the banner from `freak help`:

```fk
pilot C_G1 = "\x1b[38;2;255;100;200m"
pilot C_G2 = "\x1b[38;2;220;80;220m"
pilot C_G3 = "\x1b[38;2;180;70;240m"
```

## Box drawing and symbols

The same file declares Unicode decorations as raw UTF-8 **byte** escapes,
because V3 has no `char` type and no `\u` escape — you spell out the encoding:

```fk
pilot BOX_TL = "\xe2\x95\xad"      -- U+256D  round corner
pilot BOX_H  = "\xe2\x94\x80"      -- U+2500  horizontal
pilot BOX_V  = "\xe2\x94\x82"      -- U+2502  vertical
pilot SYM_CHECK = "\xe2\x9c\x93"   -- U+2713  check mark
```

> [!note]
> `.length()` counts characters, not bytes, so a box-drawing character is one
> character even though it is three bytes. Padding maths built on `.length()`
> stays correct.

## Respecting the user's terminal

The CLI honours the `NO_COLOR` convention in `cli_configure_output()`. Nothing
does this for you automatically — the runtime enables ANSI, it does not decide
whether you *should* use it. Copy the pattern:

```fk
pilot mut C_RESET = "\x1b[0m"
pilot mut C_BRED  = "\x1b[1;31m"

task configure_output() -> void {
    if process::env("NO_COLOR") != "" {
        C_RESET = ""
        C_BRED = ""
    }
}

task main() -> void {
    configure_output()
    say C_BRED + "error" + C_RESET + ": no colour when NO_COLOR is set"
}
```

Setting the constants to the empty word is exactly what `cli_disable_colors()`
does — every call site keeps working and concatenates nothing.

The CLI checks four variables:

| Variable | Effect in the CLI |
|---|---|
| `NO_COLOR` | Any non-empty value disables colour |
| `FREAK_NO_COLOR` | Truthy value disables colour |
| `FREAK_ASCII` | Force ASCII box drawing and symbols |
| `FREAK_UNICODE` | Force Unicode even when it would otherwise degrade |

On Windows without an explicit override it degrades decorations to ASCII unless
it detects a modern terminal via `WT_SESSION`, `TERM_PROGRAM`, `ANSICON` or
`ConEmuANSI`.

> [!note]
> There is no TTY detection anywhere. Neither the CLI nor your program can tell
> whether stdout is a pipe, so escapes are emitted even when output is
> redirected. That is why tooling around FREAK — including this site's
> verification harness — has to strip ANSI from captured compiler output.

## The compiler's own diagnostics

V3 hardcodes red for errors rather than using the palette, because the compiler
files are concatenated *ahead* of the CLI's constants:

```fk
say "\x1b[1;31merror\x1b[0m: " + msg
```

That line is in `src/compiler/v3/helpers.fk`, with variants in `parser.fk` (the
>100-error bail-out) and `main.fk` (the abort summary). The caret line under a
diagnostic is coloured the same way.

## Support and practical notes

- **Always reset.** An unclosed sequence leaks into the shell prompt after your
  program exits.
- **Safe floor:** the 8 standard colours and `1`/`4`/`0`. Universally supported.
- **Widely safe:** bright colours, backgrounds, 256-colour, truecolour, `2`,
  `3`, `7`, `9`.
- **Patchy:** `5`/`6` blink (often ignored), `8` conceal, `21` double
  underline, `51`–`55` framed/encircled/overlined, `58` underline colour.
- **Combine parameters** in one sequence rather than emitting several.
- Colour goes through `say`, which writes to stdout. There is no stderr writer
  in V3, so diagnostics and normal output share one stream.
