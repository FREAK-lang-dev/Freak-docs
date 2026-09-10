# FREAK V3

> The complete, verified reference for the language the shipping FREAK V3 compiler actually accepts.

FREAK is a programming language written entirely by AI. Its compiler is
self-hosted: the compiler that builds FREAK programs is itself written in FREAK.
This site documents **V3 "Maverick"** — the shipping, self-hosted generation
that lives in `src/compiler/v3/`.

{{verified-summary}}

## Why this site exists

The project ships a specification, `freak-full-bible.md`, that describes the
*complete* language: variants, doctrines, closures, generics, lifetimes,
squadron concurrency, probability types, and more. That document is explicit
that it describes the destination, not the present.

The V3 compiler implements a **much smaller** language than the bible. Not a
slightly smaller one — a fundamentally smaller one. Roughly a fifth of the
bible's surface compiles today.

Every page here documents only what V3 accepts, and proves it: each FREAK
snippet on this site is a real file under `examples/`, compiled by a real V3
binary, and — where it produces output — executed, with the output captured
verbatim. Nothing here is aspirational.

For the feature-by-feature comparison against the specification, see
[Bible vs V3](conformance.html). For what to write instead of the features that
are missing, see [Not in V3](not-in-v3.html).

## Hello, FREAK

{{example:hello}}

```sh
freak run hello.fk
```

## The language in one screen

This is close to the whole language. If a construct is not on this list, check
[Not in V3](not-in-v3.html) before reaching for it.

```fk
-- comments start with a double dash

pilot x = 42                    -- binding, type inferred
pilot y: word = "text"          -- explicit type annotation
fixed pilot LIMIT: int = 100    -- immutable binding
pilot mut counter: int = 0      -- reassignable binding

task add(a: int, b: int) -> int {
    give back a + b             -- explicit return, always
}

shape Point { x: int  y: int }  -- record type

impl Point {
    task make(v: int) -> Point { give back Point { x: v, y: v } }
    task sum(self) -> int { give back self.x + self.y }
}

task main() -> void {
    pilot p: Point = Point::make(3)
    say "sum={p.sum()}"          -- (interpolates paths, not calls)

    if p.x > 2 { say "big" } else { say "small" }

    when p.x {
        3 -> say "three"
        _ -> say "other"
    }

    repeat 3 times { say "again" }
    repeat until counter == 3 { counter += 1 }
    training arc until counter > 99 max 10 sessions { counter += 1 }

    pilot names: List<word> = ["alpha", "bravo"]
    say names[0]
    say word_from_int(names.length())

    say "\x1b[1;32mok\x1b[0m"        -- ANSI colour, no library needed
}
```

## What makes V3 unusual

**One flat namespace.** There are no modules at runtime. `use` lines are
stripped before parsing and act only as a hint that tells the build to link an
optional standard-library file. Every task and every top-level binding in your
file and in the standard library shares one global scope.

**Keywords are case-insensitive.** `pilot`, `Pilot` and `PILOT` are the same
token. This makes a surprising number of natural names illegal — `Pilot`,
`Result`, `Max`, `Route` and `Check` cannot name your shapes or bindings. See
[reserved words](language-basics.html#reserved-words-are-case-insensitive).

**Type annotations are one identifier, plus `List<T>`.** `pilot x: int` and
`pilot x: List<int>` both work; `List` is the only generic form, and it does
not nest.

**Four scalars, shapes, and two builtin types.** `int`, `num`, `word`, `bool`,
`void`, the `shape` records you declare, plus `List<T>` and `ByteBuffer`. No
`maybe<T>`, no `result<T,E>`, no `Map<K,V>`, no tuples. Alongside `List<T>` an
older untyped array handle survives, addressed by an `int`.

**No implicit returns.** Every value-returning path needs `give back`.

## Two backends

V3 emits either LLVM IR or portable C.

| Backend | Flag | Status |
|---|---|---|
| LLVM IR | `--llvm` (default) | Full surface, including shapes, methods and `std::ui` |
| C | `--c` | Scalars, control flow, words, arrays and native calls. Shape storage is *not* a claimed executable path |

If your program uses shapes, use the default LLVM backend. Every example on
this site was verified through it.

## Where to go next

- [Getting started](getting-started.html) — build the compiler and run a program
- [Bindings & types](language-basics.html) — the value model
- [Shapes & impl](shapes.html) — the only user-defined type
- [Lists & arrays](arrays.html) — the two collection surfaces
- [Coloured output](console.html) — ANSI escapes and terminal handling
- [Standard library](stdlib.html) — the complete callable surface
- [Bible vs V3](conformance.html) — the specification comparison
