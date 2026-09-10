# Tasks

> Functions are called tasks. One declaration form, one return keyword, no shorthands.

## Declaring a task

```fk
task name(param: type, param: type) -> returntype {
    body
}
```

`-> returntype` may be omitted, in which case the return type is `void`.
Parameter and return types follow the same grammar as everywhere else — one
identifier, or `List<T>`. See
[the type-annotation grammar](language-basics.html#the-type-annotation-grammar).

{{example:tasks}}

## `give back`

`give back expr` returns a value. `give back` on its own returns from a `void`
task.

There is **no implicit tail return**. A bare expression at the end of a block
is evaluated and discarded. Every path that must produce a value needs its own
`give back`:

```fk
task area(r: num) -> num {
    math::pow(r, 2.0) * 3.14159    -- computed, then thrown away
}

task area_ok(r: num) -> num {
    give back math::pow(r, 2.0) * 3.14159
}
```

The checker reports a missing return on a value-returning task, pointing at the
`task` keyword of the offending declaration.

> [!v4]
> The arrow shorthand `task square(x: num) => x * x` is in the bible but does
> **not** parse in V3 — you get `expected '{', found '=>'`. Neither does the
> `done` block terminator: `task f() -> int` … `done` fails with
> `expected '{', found 'give back'`. Braces are the only block delimiter.

## Calling

```fk
task main() -> void {
    say word_from_int(add(1, 2))
}
```

Arguments are positional. Named call arguments — `connect(host: "localhost",
port: 8080)` — are V4 and do not parse.

Argument count and argument types are both checked against the declaration.

## Order does not matter

Every task in the file is indexed before any body is checked, so a task may
call one declared later, and may call itself.

{{example:recursion}}

## `main`

If a task called `main` exists it becomes the program entry point. If it does
not, top-level statements are the program. You can have both — top-level
statements run first, then `main`.

## Parameters are by value

There is no `lend` / `lend mut` in V3: the borrow syntax from the bible does
not parse in a parameter list. Every parameter is passed by value.

```fk
-- does not parse in V3:
--   task show(lend p: Point) -> void { say word_from_int(p.x) }

-- write this instead:
task show(p: Point) -> void { say word_from_int(p.x) }
```

For shapes this matters: a shape parameter is a handle into runtime storage, so
mutating a field inside a task is visible to the caller. Treat shape arguments
as shared, and return a new value when you want isolation.

## Instance and associated methods

A task declared inside `impl Shape { ... }` whose first parameter is `self` is
an instance method; without `self` it is an associated method. Both are covered
in [Shapes & impl](shapes.html#methods).

## The pipe operator

`|>` rewrites a call so the piped value becomes its first argument.

{{example:pipe}}

`x |> f()` is exactly `f(x)`, and `x |> f(y)` is exactly `f(x, y)`. The right
side must be a plain task name — you cannot pipe into a method or a shape
constructor.

## `extern` tasks

A task implemented in C is declared with `extern`, on one line, with no body.
See [extern & FFI](ffi.html).

```fk
extern task abs(v: int) -> int
```

## What tasks cannot do

| Feature | Status |
|---|---|
| Generic parameters `task f<T>(...)` | V4 — `expected '(', found '<'` |
| Named call arguments | V4 |
| Default parameter values | V4 |
| Variadic parameters | V4 |
| Closures / lambdas `\|x\| => x * 2` | V4 — `|` cannot start an expression |
| Arrow bodies `=> expr` | V4 |
| `done` as a block terminator | V4 |
| Returning `maybe<T>` or `result<T,E>` | V4 — no such types |
| `?` error propagation, `or else` | V4 |
| Visibility modifiers `launch` / `launch(package)` | V4 |
