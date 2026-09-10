# Tutorial 3: Modelling data

> Shapes, nested shapes, methods, and both of V3's collection surfaces — including the restriction that catches everyone. About 25 minutes.

V3 gives you one user-defined type (`shape`) and two ways to hold a sequence.
This tutorial builds a squadron roster and shows where each tool fits.

## Step 1 — A shape with behaviour

```fk
shape Member {
    callsign: word
    sorties: int
}

impl Member {
    task enlist(callsign: word) -> Member {
        give back Member { callsign: callsign, sorties: 0 }
    }

    task veteran(self) -> bool {
        give back self.sorties >= 20
    }
}
```

`enlist` has no `self`, so it is an associated method: `Member::enlist("V-1")`.
`veteran` takes `self`, so it is an instance method: `m.veteran()`.

Constructor-style associated methods are the idiomatic way to build a shape
with defaults, since fields have no default values.

## Step 2 — Nesting

Shapes hold shapes, and access chains:

```fk
shape Airframe {
    model: word
    thrust: int
}

shape Member {
    callsign: word
    sorties: int
    frame: Airframe
}
```

Construct inline:

```fk
pilot m: Member = Member {
    callsign: "Valkyrie-1",
    sorties: 0,
    frame: Airframe { model: "Takemikazuchi", thrust: 880 }
}

say word_from_int(m.frame.thrust)
say "{m.callsign} flies a {m.frame.model}"
```

Dotted paths work inside interpolation, including `{self.frame.thrust}` from
within a method.

> [!note]
> Shapes are handles into runtime storage, not values. Passing one to a task
> and mutating a field is visible to the caller, and assigning one binding to
> another aliases the same storage. To get an independent copy, construct a new
> shape.

## Step 3 — Lists

`List<T>` is the typed sequence. The element is a scalar or a shape name:

```fk
pilot names: List<word> = ["Valkyrie-1", "Valkyrie-2", "Valkyrie-3"]
say word_from_int(names.length())
say names[1]
```

Three rules to internalise:

- **`.length()` is a method**, not a field. `names.length` reports
  *"non-shape value has no fields"*.
- **Indexed assignment needs `pilot mut`**, otherwise
  *"indexed assignment requires a mutable list binding"*.
- **The literal infers the type.** `[1, 2, 3]` is a `List<int>`; all elements
  must share one type.

`List::filled(value, count)` builds a pre-populated list, which is the way to
size one up front:

```fk
pilot mut tally: List<int> = List::filled(0, 3)
tally[0] = 24
```

There is no `push`, `pop`, `sort` or iterator. It is an indexable sequence,
nothing more.

## Step 4 — The restriction

This is the one that catches people:

```fk
shape Roster {
    members: List<Member>     -- does not compile
}
```

```text
type error: V3 owned shape fields do not yet support List values
```

A `List<T>` may be a binding, a task parameter and a return type — but **not a
shape field**. So the "container shape holding a list of children" pattern is
unavailable.

Work around it one of three ways:

1. Keep the list beside the shape rather than inside it.
2. Store a legacy `int` array handle in the field.
3. Pass lists through tasks, which is allowed:

```fk
task total_sorties(counts: List<int>) -> int {
    pilot mut sum: int = 0
    pilot mut i: int = 0
    repeat counts.length() times {
        sum += counts[i]
        i += 1
    }
    give back sum
}
```

## Step 5 — The legacy handle

Alongside `List<T>` there is an older untyped array: `array_new()` returns an
`int` handle, and every element is a `word`.

```fk
pilot h: int = array_new()
array_push(h, "alpha")
array_push(h, "bravo")
say word_from_int(array_len(h))
say array_get(h, 0)
array_release(h)
```

It is worth keeping around for two reasons: it can **grow** (`array_push`), and
it is the only thing the `std/algorithm.fk` helpers accept.

```fk
array_sort_int(h)
say array_join(h, ", ")
say word_from_int(array_max_int(h))
```

Those helpers are declared `handle: int`, so passing a `List<word>` fails:

```text
type error: call to 'array_join' argument 1 expects int, got List<word>
```

The `array_*` **builtins** are more forgiving — `array_len`, `array_get`,
`array_set`, `array_push` accept either. Builtins bridge; library tasks do not.

> [!warn]
> Two helpers are broken in the shipping compiler: `array_sort_word()`
> segfaults, and `array_unique()` returns an empty array. Use `array_sort_int`,
> and deduplicate by hand.

## Step 6 — Choosing between them

| Need | Use |
|---|---|
| Typed elements, fixed size | `List<T>` |
| Numbers without converting to `word` | `List<int>` / `List<num>` |
| Growing a collection | Legacy handle + `array_push` |
| Sorting, joining, searching | Legacy handle + `std/algorithm.fk` |
| A field inside a shape | Legacy handle — `List` is rejected |
| Returning a collection from a task | Either; or mutate a handle passed in |

`array_release(h)` frees a legacy array. V3 has no garbage collector, so a
long-running program that allocates in a loop must release.

## The finished program

{{example:tut_roster}}

## Where to go next

- [Lists & arrays](arrays.html) — the full reference for both surfaces
- [Shapes & impl](shapes.html) — operator doctrines and backend caveats
- [Standard library](stdlib.html) — `ByteBuffer`, `word_builder`, JSON, semver
- [Bible vs V3](conformance.html) — how far this is from the specification
