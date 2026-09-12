# Bindings & types

> The value model: five types, one binding keyword, and a case-insensitive keyword table that will bite you.

## Bindings

`pilot` introduces a binding. The type annotation is optional; when present it
follows the name after a colon.

{{example:variables}}

Three forms exist:

| Form | Meaning |
|---|---|
| `pilot x = expr` | Ordinary binding |
| `pilot mut x = expr` | Explicitly reassignable |
| `fixed pilot x = expr` | Immutable binding |

> [!note]
> `mut` and `fixed` only change behaviour under `--strict-borrow`. Without that
> flag V3 does no ownership or mutability checking, and all three forms behave
> identically. Write `mut` anyway — it documents intent and it is what the
> checker will demand when you turn it on.

Assignment operators: `=`, `+=`, `-=`, `*=`, `/=`, `%=`.

## Type inference

The annotation can always be omitted. V3 infers from the initialiser.

{{example:inference}}

## The type table

| Type | Notes |
|---|---|
| `int` | 64-bit signed integer. The default for whole-number literals |
| `num` | 64-bit float. Any literal containing `.` |
| `word` | UTF-8 string |
| `bool` | `true` / `false`, and the aliases `yes` / `no` / `hai` / `iie` |
| `void` | Absence of a value. Only a return type |
| `List<T>` | Typed growable sequence. `T` is a scalar or a shape name; no nesting |
| `ByteBuffer` | Builtin binary read/write cursor, with real methods |
| *a shape name* | Any type you declared with `shape` |

There is no `uint`, `tiny`, `char`, `big`, `float`, `float32` or `never`; and no
`maybe<T>`, `result<T,E>`, `Map<K,V>`, `Set<T>`, tuple, fixed array or raw
pointer.

### The type-annotation grammar

The parser takes one identifier, plus a single special case for `List`:

```fk
pilot a: int = 1                       -- fine
pilot b: word = "x"                    -- fine
pilot c: Rect = Rect { w: 1, h: 2 }    -- fine, Rect is a shape
pilot d: List<int> = [1, 2, 3]         -- fine
pilot e: ByteBuffer = ByteBuffer::new()

-- none of these parse:
--   pilot f: maybe<int> = some(1)
--   pilot g: [int; 4] = [1, 2, 3, 4]
--   pilot h: List<List<int>> = []
--   task i<T>(x: T) -> T { give back x }
```

`List<T>` is the only generic form in the language, and it is hard-coded in
`parser_take_type` rather than being a general mechanism — the element must be
a plain identifier, so `List<List<int>>` is rejected with *"expected '>' after
list element type"*.

The same grammar applies to shape fields, task parameters, task return types
and `extern` signatures.

> [!note]
> `List<T>` and `ByteBuffer` are recent additions to V3. Much of the rest of
> the language still assumes the older untyped `int` handle, so the two
> surfaces coexist — see [Lists & arrays](arrays.html) for which calls accept
> which.

### Numeric literals

A literal with a `.` is `num`; otherwise `int`.

```fk
pilot i = 42        -- int
pilot f = 42.0      -- num
```

There is **no negative literal**. `-5` parses as unary minus applied to `5`,
which is fine inside an expression but not as an initialiser in every position.
The idiom used throughout the compiler's own source is a subtraction:

```fk
pilot below_zero: int = 0 - 5
say word_from_int(-below_zero)
```

There are also no numeric suffixes: `42u`, `3.14f`, `42t` and `999b` are all V4.

### Mixing int and num

Arithmetic that involves a `num` on either side produces `num`. Convert
explicitly at the boundary:

```fk
pilot n: int = 7
pilot f: num = n.to_num()
pilot back: int = f.to_int()
```

| Conversion | Result |
|---|---|
| `intValue.to_num()` | `num` |
| `intValue.to_word()` | `word` |
| `numValue.to_int()` | `int` |
| `numValue.to_word()` | `word` |
| `boolValue.to_word()` | `word` |
| `wordValue.to_int()` | `int` |
| `wordValue.to_num()` | `num` |
| `word_from_int(i)` | `word` |
| `word_from_bool(b)` | `word` |
| `format_num(f)` | `word` |
| `parse_num(w)` | `num` |
| `word_to_int(w)` | `int` |
| `char_to_word(code)` | `word` |

## Reserved words are case-insensitive

This is the single most surprising rule in V3, and the one that produces the
most confusing errors.

The lexer lowercases every identifier before comparing it against the keyword
table. `pilot`, `Pilot`, `PILOT` and `PiLoT` are all the same keyword token.
A keyword can never be an identifier, so none of those can name a shape, task,
field or binding.

{{example:reserved_words}}

Naming a shape `Pilot` produces:

```text
error: expected an identifier for shape name, found 'Pilot'
```

### The full reserved list

Every word below is reserved **in any casing**:

```text
pilot   fixed    task     say      shape    impl     doctrine
launch  use      as       in       lend     mut      move
copy    break    continue if       else     when     repeat
times   until    done     for      each     check    result
got     nobody   some     ok       err      sessions max
foreshadow  payoff  route  sadly   deus_ex_machina   isekai
eventually  and    or      not     nakama   tsundere extern

true  false  yes  no  hai  iie
```

Multi-word keywords, lexed greedily:

```text
give back   or else    trust me    for each    for science
training arc   bringing back   only on   PLUS ULTRA   FINAL FORM
```

The names that catch people most often are `Pilot`, `Result`, `Max`, `Route`,
`Check`, `Move`, `Copy`, `Some`, `Ok`, `Err`, `Got`, `Use`, `In`, `As`, `Each`,
`Done` and `Times`. Pick a synonym: `Aviator`, `Outcome`, `upper_bound`,
`verdict`.

> [!warn]
> Several of these words are reserved but have **no grammar at all** in V3 —
> `doctrine`, `use`, `launch`, `check`, `lend`, `route`, `foreshadow`,
> `isekai`, `trust me`, `for each`. They lex as keywords and then fail in the
> parser with *"this token cannot start an expression"*. They still cannot be
> used as identifiers.

## Top-level code

A file does not need a `main`. Statements written at the top level run in
order, and top-level bindings are visible to every task in the file.

{{example:toplevel}}

> [!note]
> This is a real difference from the bible, which forbids arbitrary executable
> statements at root scope and requires root bindings to be `fixed pilot`
> constants. V3 allows both.

## Comments

`--` starts a comment that runs to the end of the line. There is no block
comment form.

```fk
-- a whole-line comment
pilot x = 1    -- a trailing comment
```
