# Not in V3

> Every major bible feature the shipping compiler rejects, with the diagnostic you will see and what to write instead.

Use this page when something from `freak-full-bible.md` will not compile.
Each entry gives the exact error and a working V3 substitute.

> [!note]
> Some things on the bible's missing list have quietly arrived. V3 now has a
> typed [`List<T>`](arrays.html), a builtin
> [`ByteBuffer`](stdlib.html#bytebuffer), a
> [`word_builder::*`](words.html#building-words-incrementally) accumulator, and
> a `tcp::socket_*` family that can listen and accept. Check
> [Bible vs V3](conformance.html) before assuming something is absent.

## Optional and fallible values

```text
error: expected '{', found '<'          -- maybe<T>, result<T,E>
error: unexpected 'check'
error: unexpected '?'
error: unexpected 'or else'
```

There is no `maybe<T>`, `result<T,E>`, `some`, `nobody`, `ok`, `err`, `?` or
`or else`. Signal absence and failure with sentinel values, the way the
compiler's own source does.

For parsing specifically, v0.14.2 added a checked pair —
`w.parse_int()` / `w.parse_num()` plus a global `parse_status()` — which
distinguishes "parsed zero" from "failed". `ByteBuffer.status()` follows the
same out-of-band pattern. See
[checked parsing](words.html#checked-parsing).

```fk
-- A word task returns "" for "no value".
task find_name(id: int) -> word {
    if id == 1 { give back "Takeru" }
    give back ""
}

-- An int task returns -1 for "not found".
task index_of_flag(flags: int, needle: word) -> int {
    pilot mut i: int = 0
    repeat array_len(flags) times {
        if array_get(flags, i) == needle { give back i }
        i += 1
    }
    give back 0 - 1
}

task main() -> void {
    pilot name: word = find_name(2)
    if name.length() == 0 {
        say "not found"
    } else {
        say name
    }
}
```

For richer errors, return a shape with a status field:

```fk
shape Outcome {
    ok: bool
    value: int
    message: word
}
```

## Collections

`List<T>` **does** exist now — typed, indexable, and growable as of v0.14.2
(`push`, `pop`, `reserve`, `capacity`, `clear`). What it still lacks is
`insert`, `remove`, `sort` and any iterator, and it does not nest. See
[Lists & arrays](arrays.html).

Still absent: `Map<K,V>`, `Set<T>`, `Lineup<T>`, and the `{ "k": v }` map
literal.

For a map, keep two parallel collections:

```fk
task map_get(keys: int, values: int, key: word) -> word {
    pilot at: int = array_find(keys, key)
    if at < 0 { give back "" }
    give back array_get(values, at)
}
```

## Iteration

```text
error: unexpected 'for each' — this token cannot start an expression
```

Use an index and a counted loop:

```fk
pilot mut i: int = 0
repeat array_len(items) times {
    say array_get(items, i)
    i += 1
}
```

There is no `std::iter` either — no `.map`, `.filter`, `.fold`, `.any`,
`.collect`. Write the loop.

## Closures

```text
error: unexpected '|' — this token cannot start an expression
```

No lambdas, no capture modes, no `Callable` / `MutCallable` / `OneShot`. Since
tasks cannot be passed as values, the substitute is a named task plus a
dispatch `when`:

```fk
task apply(op: word, value: int) -> int {
    when op {
        "double" -> give back value * 2
        "square" -> give back value * value
        _        -> give back value
    }
    give back value
}
```

## Generics

```text
error: expected '(', found '<'          -- task first<T>(...)
```

No type parameters, no doctrine bounds, no monomorphisation. Write one task per
concrete type.

`List<T>` is the sole exception, and it is not a general mechanism — the
annotation is a hard-coded special case in `parser_take_type`, so `List<T>`
works while `List<List<int>>` and every other composed type do not.

## Doctrines and dynamic dispatch

```text
error: unexpected 'doctrine' — this token cannot start an expression
type error: operator '+' does not accept Vec2 and Vec2
```

`doctrine` declarations do not parse. `impl D for S { }` **does** parse, but
`D` is never validated and the operator token is not rewritten — call the
method by name.

```fk
impl Add for Vec2 {
    task add(self, other: Vec2) -> Vec2 { ... }
}

pilot c: Vec2 = a.add(b)     -- not a + b
```

No `dyn Doctrine`, no vtables, no heterogeneous collections.

## Variants and aliases

```text
type error: unknown binding 'variant'
type error: unknown binding 'alias'
```

Neither `variant` nor `alias` is even a keyword in V3's lexer, so they parse as
identifiers and fail in the checker. Model a sum type as a shape with a tag:

```fk
shape Contact {
    kind: word        -- "soldier" | "laser" | "fort"
    id: int
    armor: int
    hive: word
}

task engage(c: Contact) -> void {
    when c.kind {
        "soldier" -> say "engaging soldier {c.id}"
        "laser"   -> say "smoke now"
        "fort"    -> say "requesting strike on {c.hive}"
        _         -> say "unknown contact"
    }
}
```

For an alias, just repeat the underlying type — a type annotation is one
identifier (or `List<T>`) anyway, so there is little to abbreviate.

## Borrowing, lifetimes and shared ownership

```text
error: expected an identifier for parameter name, found 'lend'
```

No `lend` / `lend mut` parameters, no `'a` lifetimes, no outlives bounds, no
`Shared<T>` / `Weak<T>`, no `.clone()`, no `trust me`.

Every parameter is by value, and shapes are handles into runtime storage — so a
task that mutates a shape parameter's field affects the caller. Return a fresh
shape when you want isolation.

`--strict-borrow` enables a Phase-1 checker for immutability and single-owner
moves; that is the whole of V3's ownership story.

## Concurrency

Nothing at all. No `xm3`, `sortie`, `debrief`, `formation`, `BriefingRoom`,
`wingman`, `Comms`, `std::thread`, atomics or channels. None of those words are
keywords. `||` lexes as one token and has no grammar rule.

Shell out if you must:

```fk
pilot code: int = process::exec("some-command --flag")
```

## Modules and visibility

```text
error: unexpected 'launch' — this token cannot start an expression
```

`use` lines are replaced with comments before parsing. There is no import
system and no visibility system — one flat global namespace holds your file and
every linked standard-library file.

Consequences worth planning around:

- Name collisions with `std/` tasks are real. Prefix your tasks.
- `use std::math3d`, `use std::zip`, `use std::ui` and `use cockpit` still
  matter as **build triggers** — the text switches on linking that module.
- **Hangar packages cannot be consumed.** `hangar install` downloads into
  `hangar_modules/`, but the build never reads it. Concatenate the source
  instead: `cat lib/thing.fk src/app.fk > combined.fk && freak build
  combined.fk`. See [Hangar & packages](hangar.html).

## Advanced types

`power<N>`, `prob[lo..hi]`, `causality<T>` and `mood` do not lex. Model the same
intent with ordinary values and runtime checks:

```fk
task engage_fort(power_level: int) -> word {
    if power_level < 7000 { give back "insufficient power" }
    give back "engaging"
}
```

## Anime layer

Rejected: `foreshadow`, `payoff`, `route`, `check route`, `only on`,
`deus_ex_machina`, `isekai`, `bringing back`, `trust me`, `direct_order`,
`sadly`, `for science,`, `knowing this will hurt,`, `training arc ... with
growth`, `eventually if`, `prob[...] chance`, `prob_when`, `declare was`.

Accepted: `training arc`, plain `eventually`, single bare `@annotation`, and
the four anime operators. See [Anime layer](anime-layer.html).

## FFI

Only `extern task name(p: T) -> R`, one per line. No `extern [C] { }` blocks,
calling conventions, `link=`, `@link_name`, variadics, `std::ffi` aliases, raw
pointers, `@layout(C)`, `@repr(...)`, `@extern_callback` or `trust me`.

Stick to `int`, `num`, `bool` and `void` across the boundary — `word` is an
`i64` runtime handle, not a `char*`. See [extern & FFI](ffi.html).

## Syntax shorthands

| Bible form | V3 |
|---|---|
| `task f(x) => expr` | Use a braced body with `give back` |
| `done` closing a block | Use `}` |
| `**` exponent | `math::pow(a, b)` or `std_pow(a, b)` |
| `-5` as a literal | `0 - 5` |
| `42u`, `3.14f`, `42t`, `999b` | No suffixes |
| `[0; 100]` repeat-fill | `List::filled(0, 100)` |
| `[T; N]` fixed arrays | `List<T>`, or a legacy array handle |
| `(a, b)` tuples | A shape |
| Named call arguments | Positional only |
| Stacked `@a @b` annotations | One per statement |
| `@rival(meiya)` annotation arguments | Bare `@name` only |

## Build modes, voices, output paths

`slice_of_life`, `mecha`, `shonen_jump`, `final_form` and `alternative` build
modes do not exist; nor do `--voice=`, `--clearance=`, `--build-mode=` or
`-o output_path`. The knobs are `--opt=0..3`, `--c` / `--llvm`, `--target=` and
`--strict-borrow`.

## Tooling

No language server, no incremental parsing, no tolerant AST, no autocomplete,
no `test "name" { expect ... }` framework, no JIT. Parse errors abort the
build. `freak test` is a shim around a Python regression runner in the source
checkout.
