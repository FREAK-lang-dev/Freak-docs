# Control flow

> Two branch forms, three loop forms, and a bounded loop you will not find in other languages.

## if / else if / else

Conditions take no parentheses. Braces are mandatory even for one statement.

{{example:control_if}}

`else if` chains to any depth. Internally V3 flattens these rather than nesting
them, which is one of the architectural fixes that made the self-hosted
compiler possible.

## when

`when` matches a subject against literal arms. `_` is the catch-all.

{{example:control_when}}

Rules:

- Each arm is `pattern -> statement`. One statement — wrap several in a block.
- Arms are separated by nothing at all; newlines are enough.
- The subject may be `int`, `word`, `bool` or `num`.
- Arm patterns are **expressions compared for equality**, not patterns. There is
  no destructuring, no binding, no guards, no ranges.
- Exhaustiveness is not checked. Without a `_` arm and with no match, nothing runs.
- `when` is a **statement**, not an expression. It cannot appear on the right of
  `=` or inside `give back`.

To produce a value from a match, assign inside the arms:

```fk
task main() -> void {
    pilot code: int = 2
    pilot mut label: word = ""
    when code {
        1 -> label = "launch"
        2 -> label = "hold"
        _ -> label = "unknown"
    }
    say label
}
```

> [!v4]
> Destructuring arms — `BETA::Soldier { position } -> engage_at(position)` —
> need variants, which V3 does not have. So does `check` over `maybe` /
> `result`, and `check route`. See [Not in V3](not-in-v3.html).

## Loops

V3 has exactly three loop forms.

{{example:control_loops}}

### repeat N times

```fk
repeat COUNT times { body }
```

`COUNT` is any `int` expression, evaluated **once** before the loop. There is no
loop variable — keep your own counter if you need the index.

```fk
pilot mut i: int = 0
repeat array_len(items) times {
    say array_get(items, i)
    i += 1
}
```

### repeat until

```fk
repeat until CONDITION { body }
```

The condition is tested **before** each pass, so the body may run zero times.
Note the sense: the loop continues while the condition is *false*.

### training arc

```fk
training arc until CONDITION max N sessions { body }
```

A loop with a compulsory iteration cap. It stops when the condition becomes
true **or** when the cap is reached — whichever comes first — so it cannot spin
forever.

{{example:training_arc}}

It lowers to roughly:

```text
int64_t sessions = 0;
while (!(CONDITION) && sessions < N) {
    body;
    sessions++;
}
```

This makes it genuinely useful for bounded numeric search, where you want a
hard guarantee of termination:

{{example:bounded_search}}

> [!v4]
> The `with growth` variant — which makes the compiler verify that the body
> actually mutates the condition's subject — is V4. Plain `training arc` is
> fully supported.

## break and continue

Both work in all three loop forms.

```fk
repeat 10 times {
    if should_skip { continue }
    if should_stop { break }
    process()
}
```

## Bare blocks

A `{ ... }` on its own is a statement. It groups code but does **not** create a
new scope for bindings — a `pilot` declared inside remains visible afterwards.

```fk
task main() -> void {
    pilot x: int = 1
    {
        say word_from_int(x)
    }
}
```

## eventually

`eventually { ... }` is the cleanup block. Its V3 behaviour differs sharply
from the specification.

{{example:eventually}}

> [!warn]
> V3 emits the block **inline, where you wrote it**. It is not deferred to the
> end of scope, it does not run in LIFO order with other `eventually` blocks,
> and it does not run on `give back`, `break` or `panic`. Treat it as a labelled
> section, not as `defer`. True deferred semantics are V4.

## No `for each`

`for each` lexes as a keyword but has no grammar in V3:

```text
error: unexpected 'for each' — this token cannot start an expression
```

Iterate with an index instead:

```fk
pilot mut i: int = 0
repeat array_len(items) times {
    say array_get(items, i)
    i += 1
}
```

## Summary of what is missing

| Construct | Status |
|---|---|
| `for each x in list` | V4 |
| `for each (i, x) in list.enumerate()` | V4 |
| `check` over `maybe` / `result` | V4 |
| `check route` | V4 |
| `when` with destructuring or guards | V4 |
| `when` in expression position | V4 |
| `training arc ... with growth` | V4 |
| `xm3 { a \|\| b }` and all squadron concurrency | V4 |
| `prob[0.3] chance { }`, `prob_when` | V4 |
| `isekai { } bringing back { }` | V4 |
| `eventually if cond { }` | V4 |
| True deferred `eventually` | V4 |
