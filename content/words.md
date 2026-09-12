# Words & interpolation

> `word` is the string type. Its methods are compiler builtins, and `{path}` interpolation has precise rules.

## Literals and escapes

A `word` literal is double-quoted.

| Escape | Meaning |
|---|---|
| `\n` | newline |
| `\r` | carriage return |
| `\t` | tab |
| `\"` | double quote |
| `\\` | backslash |
| `\xNN` | byte with hex value `NN` |

`\x1b` is the ESC byte, which is how you produce coloured console output — see
[Coloured output](console.html).

> [!warn]
> `\x00` is rejected at lex time: *"embedded NUL escape is not supported"*. V3
> words use a NUL-terminated runtime representation, so a word can never
> contain a zero byte. A malformed hex escape (fewer than two hex digits) is
> also a lex error.

An unterminated literal reports *"unterminated string literal"* pointing at the
opening quote.

## Methods

All of these are compiler builtins — no import, and they work under
`freak check` as well as `freak build`.

{{example:strings}}

| Method | Signature | Notes |
|---|---|---|
| `.length()` | `-> int` | Character count |
| `.trim()` | `-> word` | Strips leading and trailing whitespace |
| `.to_upper()` | `-> word` | |
| `.to_lower()` | `-> word` | |
| `.contains(needle)` | `word -> bool` | |
| `.starts_with(prefix)` | `word -> bool` | |
| `.ends_with(suffix)` | `word -> bool` | |
| `.replace(old, new)` | `word, word -> word` | Replaces every occurrence |
| `.substring(start, len)` | `int, int -> word` | Start index and **length**, not an end index |
| `.char_at(i)` | `int -> word` | A one-character `word`, not a `char` type |
| `.to_int()` | `-> int` | |
| `.to_num()` | `-> num` | |
| `.checksum()` | `-> int` | Runtime hash |
| `.parse_int()` | `-> int` | Checked; sets the parse status on failure |
| `.parse_num()` | `-> num` | Checked; sets the parse status on failure |
| `.repeated(n)` | `int -> word` | The word repeated `n` times |

> [!note]
> `.substring(start, len)` takes a **length** as its second argument. The bible
> describes `slice(from, to)`; V3's builtin is not that function.
> `"abcdef".substring(1, 3)` yields `"bcd"`.

### Snapshot helpers

Seven further `word` methods exist for the compiler's own line-and-field
serialisation format. They are part of the builtin table and will type-check in
your code, but they are internal plumbing rather than a general-purpose API:

`.snapshot_escape()`, `.snapshot_unescape()`, `.snapshot_line_count()`,
`.snapshot_line(i)`, `.snapshot_lines()`, `.snapshot_field_count()`,
`.snapshot_field_raw(i)`.

## Checked parsing

`.to_int()` and `.to_num()` convert silently — a word that is not a number
yields `0`, indistinguishable from parsing `"0"`. As of v0.14.2 there is a
checked pair that reports failure out of band:

```fk
say word_from_int("42".parse_int())      -- 42
say word_from_int(parse_status())        -- 0, clean

say word_from_int("nope".parse_int())    -- 0
say word_from_int(parse_status())        -- 1, failed
parse_clear_status()
```

| Call | Signature | Meaning |
|---|---|---|
| `w.parse_int()` | `-> int` | Parse, `0` on failure |
| `w.parse_num()` | `-> num` | Parse, `0.0` on failure |
| `parse_status()` | `-> int` | `0` clean, non-zero if a parse failed |
| `parse_clear_status()` | `-> void` | Reset it |

The status is global and **sticky** — it stays set until you clear it — so
check it immediately after the parse you care about, exactly as with
`ByteBuffer.status()`. This is V3's substitute for `maybe<int>`, which does not
exist.

`std/convert.fk` also offers `word_to_int_safe(s)`, which returns `0` on
failure without touching any status.

## Concatenation and conversion

```fk
say "Muv" + "-" + "Luv"      -- operator
say word_concat("XM", "3")   -- builtin, identical
```

`+` on two words concatenates, and `+=` appends in place as of v0.14.2.
`+` on a word and a number is a type error — convert first:

```fk
pilot n: int = 42
say "answer: " + word_from_int(n)
say "answer: {n}"              -- or interpolate
```

| Builtin | Signature |
|---|---|
| `word_from_int(i)` | `int -> word` |
| `word_from_bool(b)` | `bool -> word` |
| `word_to_int(w)` | `word -> int` |
| `word_concat(a, b)` | `word, word -> word` |
| `word_join(handle)` | `int -> word` |
| `char_to_word(code)` | `int -> word` |
| `format_num(f)` | `num -> word` |
| `parse_num(w)` | `word -> num` |

`format_num` prints a `num` without a trailing `.0` when it is integral —
`format_num(12.0)` gives `12`.

## Indexing

`word[i]` yields a one-character `word`. It is the only indexable type in V3.

```fk
pilot s: word = "abc"
say s[1]           -- b
say s.char_at(1)   -- b, identical
```

## Interpolation

`{path}` inside a double-quoted word substitutes a binding's value.

{{example:interpolation}}

The rules are exact:

- A **path** is an identifier followed by zero or more `.field` hops:
  `name`, `p.score`, `self.engine.thrust`.
- The path must resolve to `word`, `int`, `num` or `bool`. Any other type is a
  type error.
- Every segment must be a valid identifier — so it cannot be a keyword, in any
  casing.
- A matched `{...}` whose body is **not** a valid path is left as literal text,
  braces included. `"literal {1 + 2} braces"` prints exactly that.
- An unmatched `{` is literal text.
- Unknown bindings are a compile error: *"unknown interpolation binding 'x'"*.

> [!warn]
> Interpolation substitutes **paths only** — never calls, never expressions.
> `"{p.sum()}"` is not a call; it is literal text, because `sum()` is not a
> valid path segment. Compute into a binding first:
>
> ```fk
> pilot total: int = p.sum()
> say "sum={total}"
> ```

Dotted shape interpolation, including `{self.field}` inside a method, is
verified working on the LLVM backend. It is **not** a claimed executable path
on the C backend.

## Printing without a newline

`say` always appends a newline. To put several pieces on one line, build the
word first and say it once — or use carriage-return and cursor-movement
escapes to redraw. All three techniques are in
[Printing on the same line](console.html#printing-on-the-same-line).

## Building words incrementally

Repeated `+` concatenation copies the whole accumulated word each time.
`word_builder::*` avoids that. The builder is an `int` handle, not a shape.

{{example:word_builder}}

| Call | Signature | Notes |
|---|---|---|
| `word_builder::new()` | `-> int` | |
| `word_builder::with_capacity(n)` | `int -> int` | Pre-allocate |
| `word_builder::reserve(b, n)` | `int, int -> void` | Grow the capacity |
| `word_builder::append(b, w)` | `int, word -> void` | |
| `word_builder::append_char(b, code)` | `int, int -> void` | By codepoint |
| `word_builder::append_int(b, n)` | `int, int -> void` | |
| `word_builder::length(b)` | `int -> int` | |
| `word_builder::capacity(b)` | `int -> int` | |
| `word_builder::clear(b)` | `int -> void` | Keep the buffer, drop the content |
| `word_builder::finish(b)` | `int -> word` | Consumes the builder |
| `word_builder::discard(b)` | `int -> void` | Free without producing a word |

> [!note]
> `finish` consumes the builder — do not reuse the handle afterwards. Use
> `clear` to keep building with the same allocation, and `discard` when you are
> abandoning it without producing a word.

This is V3's answer to the bible's `WordBuilder` from §7.2. The API is
namespaced calls over a handle rather than methods on an object.

## Standard-library word tasks

`std/string.fk` is ordinary FREAK source linked in by `freak build` and
`freak run`. Its tasks are global and take the word as a normal argument.

{{example:stdlib_string}}

| Task | Signature |
|---|---|
| `string_repeat(s, count)` | `word, int -> word` |
| `string_reverse(s)` | `word -> word` |
| `string_count(haystack, needle)` | `word, word -> int` |
| `string_index_of(s, needle)` | `word, word -> int`, `-1` when absent |
| `string_pad_left(s, width, pad)` | `word, int, word -> word` |
| `string_pad_right(s, width, pad)` | `word, int, word -> word` |
| `string_split(s, delim)` | `word, word -> word` (an encoded word, not an array) |
| `string_join(parts, sep)` | `word, word -> word` |
| `string_trim(s)` | `word -> word` |
| `string_substring(s, start, end)` | `word, int, int -> word` — an **end index**, unlike the builtin |
| `string_replace(s, old, new)` | `word, word, word -> word` |
| `string_contains` / `string_starts_with` / `string_ends_with` | `-> bool` |
| `is_digit(c)` / `is_alpha(c)` / `is_whitespace(c)` | `word -> bool` |

> [!note]
> These duplicate several builtin methods. The builtins are cheaper and work
> under `freak check`; the `std/` tasks exist because the standard library is
> itself written in FREAK. Where the two disagree — `substring` — prefer the
> builtin and mind the length-vs-end-index difference.

## Splitting into an array

`string_split` returns an encoded word, not an array handle. To get a real
array, walk the characters yourself:

{{example:wordcount}}
