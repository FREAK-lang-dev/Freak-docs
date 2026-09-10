# Lists & arrays

> V3 has two collection surfaces: a typed `List<T>`, and an older untyped handle. Know which one you are holding.

This is the one part of V3 with genuine overlap, because `List<T>` was added on
top of a pre-existing untyped array. Both still work, and they are not
interchangeable everywhere.

| | `List<T>` | Legacy handle |
|---|---|---|
| Type | `List<int>`, `List<word>`, `List<Shape>`, … | `int` |
| Created by | `[a, b, c]`, `List::filled(v, n)` | `array_new()` |
| Element type | Checked | Always `word` |
| Length | `list.length()` | `array_len(h)` |
| Read | `list[i]` | `array_get(h, i)` |
| Write | `list[i] = v` (needs `pilot mut`) | `array_set(h, i, v)` |
| Append | — | `array_push(h, v)` |
| Accepted by `array_*` builtins | yes, when `List<word>` | yes |
| Accepted by `std/algorithm.fk` tasks | **no** | yes |

## The List type

The element type must be a scalar — `int`, `num`, `word`, `bool` — or the name
of a shape. There is no nesting: `List<List<int>>` does not parse.

{{example:lists}}

Rules worth pinning down:

- **`[a, b, c]` infers `List<T>`** from its elements, all of which must share
  one type. Numbers stay numbers; no conversion to `word` is needed.
- **`.length()` is a method**, not a field. `list.length` reports
  *"non-shape value has no fields"*.
- **Indexed assignment needs `pilot mut`.** Otherwise you get
  *"indexed assignment requires a mutable list binding; declare it with pilot mut"*.
- **`List::filled(value, count)`** builds a pre-populated list and takes its
  element type from `value`.
- Indexing a shape element chains: `contacts[0].tag`.

There is still no `push`, `pop`, `insert`, `remove`, `sort` or iterator on
`List<T>`. It is a fixed-shape, indexable sequence. To build one incrementally,
use the legacy handle, or size it with `List::filled` and assign by index.

### Where a List may appear

| Position | Allowed |
|---|---|
| `pilot` / `fixed pilot` binding | yes |
| Task parameter | yes |
| Task return type | yes |
| **Shape field** | **no** |

> [!warn]
> A shape field cannot hold a list:
>
> ```text
> type error: V3 owned shape fields do not yet support List values
> ```
>
> Store a legacy `int` array handle in the field instead, or keep the list in a
> separate binding beside the shape.

> [!note]
> `List<T>` is newer than most of V3 and the surface is thin. Treat it as the
> right choice for *holding* typed data, and the legacy handle as the right
> choice for *building* and for reaching the `std/algorithm.fk` helpers.

## The legacy handle

`array_new()` returns an `int` handle to a runtime array whose elements are
always `word`. Store other types by converting them in and out.

{{example:arrays}}

| Call | Signature |
|---|---|
| `array_new()` | `-> int` |
| `array_push(h, value)` | `word-array, word -> void` |
| `array_get(h, i)` | `word-array, int -> word` |
| `array_set(h, i, value)` | `word-array, int, word -> void` |
| `array_len(h)` | `word-array -> int` |
| `array_release(h)` | `word-array -> void` |
| `word_join(h)` | `int -> word` |

`word-array` is a checker-internal marker meaning "either an `int` handle or a
`List<word>`" — it is not a type you can write in source. That is why the
`array_*` builtins accept both, while a user-declared task with `handle: int`
accepts only the handle.

## Mixing the two

{{example:array_literal}}

The rule that follows from the table above: **builtins bridge, library tasks do
not.**

```fk
pilot names: List<word> = ["b", "a"]

say word_from_int(array_len(names))   -- fine: builtin, accepts word-array
say array_get(names, 0)               -- fine

-- array_join is a task in std/algorithm.fk declared `handle: int`:
-- say array_join(names, ",")
--   type error: call to 'array_join' argument 1 expects int, got List<word>
```

If you need the library helpers, build a legacy handle with `array_new()`.

## Iterating

There is no `for each` in either surface. Keep an index and use a counted loop:

```fk
pilot mut i: int = 0
repeat items.length() times {
    say items[i]
    i += 1
}
```

`repeat N times` evaluates its count once, so growing the collection inside the
loop will not extend the iteration.

## std/algorithm.fk helpers

Plain FREAK source, linked by `freak build` and `freak run` (not `freak check`).
Every helper takes a **legacy `int` handle**.

| Task | Signature | Notes |
|---|---|---|
| `array_sort_int(h)` | `int -> void` | In-place insertion sort, numeric order |
| `array_binary_search_int(h, target)` | `int, int -> int` | Index or `-1`; needs a sorted array |
| `array_reverse(h)` | `int -> void` | In place |
| `array_find(h, target)` | `int, word -> int` | Index or `-1` |
| `array_contains(h, target)` | `int, word -> bool` | |
| `array_count(h, target)` | `int, word -> int` | |
| `array_copy(h)` | `int -> int` | New handle, shallow copy |
| `array_join(h, sep)` | `int, word -> word` | |
| `array_sum_int(h)` | `int -> int` | |
| `array_max_int(h)` / `array_min_int(h)` | `int -> int` | |

> [!warn]
> **Two of these are broken**, re-confirmed against the compiler that verified
> this site:
>
> - `array_sort_word(h)` **segfaults**. It routes through
>   `extern task freak_word_compare(a: word, b: word) -> int`, and that
>   declaration does not bridge the LLVM backend's `word` handle
>   representation. See [extern & FFI](ffi.html#type-mapping).
> - `array_unique(h)` **returns an empty array**.
>
> To sort words, keep a parallel `int` key array and sort that, or write an
> insertion sort in your own code comparing with `.char_at()`.

## Memory

`array_release(h)` frees a legacy array. V3 has no garbage collector and no
automatic drop, so a long-running program that allocates in a loop must
release. Do not use a handle after releasing it, and do not release twice.

`List<T>` values have no explicit release call.

## Passing collections to tasks

A legacy handle is just an `int`, so it passes freely and the callee mutates
the caller's array — the standard way to return a collection:

```fk
task fill(out: int) -> void {
    array_push(out, "alpha")
    array_push(out, "bravo")
}

task main() -> void {
    pilot items: int = array_new()
    fill(items)
    say word_from_int(array_len(items))
    array_release(items)
}
```

A `List<T>` can also be a parameter or return type, since `parser_take_type`
accepts the annotation in both positions.

## Maps and sets

Still none. `Map<K,V>`, `Set<T>` and `Lineup<T>` do not exist, and the
`{ "k": v }` map literal does not parse. For small lookups, use two parallel
collections and `array_find`.
