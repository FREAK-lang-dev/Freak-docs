# Shapes & impl

> `shape` is the only user-defined type in V3. `impl` attaches methods to it.

## Declaring a shape

```fk
shape Name {
    field: type
    field: type
}
```

Fields are `name: type`, where the type is `int`, `num`, `word`, `bool`, or
another shape's name. Separators are optional: newlines, commas, or a trailing
comma before `}` all work.

> [!warn]
> A shape field may **not** hold a `List<T>`, even though the annotation parses
> everywhere else:
>
> ```text
> type error: V3 owned shape fields do not yet support List values
> ```
>
> Keep the list in a separate binding, or store a legacy `int` array handle in
> the field instead. `List<T>` *is* allowed as a task parameter and return type.

{{example:shapes}}

## Construction

```fk
pilot v: Vector2 = Vector2 { x: 3, y: 4 }
```

Every field must be supplied, by name, in any order. Field labels are checked
against the declaration; an unknown or missing field is a compile error.

> [!note]
> The parser only treats `Name { ... }` as a constructor when `Name` is already
> a **registered shape**. A shape must therefore be declared before it is
> constructed in the token stream. Declaring shapes at the top of the file, as
> every example here does, keeps this from ever mattering.

## Field access and assignment

```fk
say word_from_int(v.x)
v.x = 10
```

Compound assignment works on fields too: `v.x += 1`.

Access chains through nested shapes, including inside string interpolation.

{{example:nested_shapes}}

## Methods

`impl Shape { ... }` may contain only `task` declarations.

{{example:impl_methods}}

The receiver decides the call form:

| Declaration | Kind | Call |
|---|---|---|
| `task area(self) -> int` | instance method | `value.area()` |
| `task scaled(self, f: int) -> Rect` | instance method with args | `value.scaled(3)` |
| `task square(side: int) -> Rect` | associated method | `Rect::square(4)` |

`self` is written bare — never `self: Rect`. The compiler substitutes the
owning shape's type once the `impl` target is known, so `self.field` resolves
properly and duplicate field/method names across shapes do not collide.

Methods are compiled to a flat global task named `Shape_method`. This is why
two shapes may both define `area` without conflict, and why the checker tracks
`impl` provenance separately: a free task literally named `Rect_area` is **not**
accepted as proof that `Rect.area` exists.

## Operator doctrines

V3 accepts `impl Doctrine for Shape` and records the doctrine name as
provenance. The methods become callable exactly like any other method.

{{example:operator_overload}}

> [!warn]
> **The operator token is not rewritten.** Implementing `Add` does not make `+`
> work on your shape:
>
> ```text
> type error: operator '+' does not accept Vec2 and Vec2
> ```
>
> Call the method by name — `a.add(b)`. The bible's `pilot v = v1 + v2`
> dispatch is V4.

> [!note]
> The doctrine name is **not validated**. `impl Whatever for Vec2 { ... }`
> compiles cleanly — the name is recorded and otherwise ignored. There is no
> check that the doctrine exists, that its methods are all implemented, or that
> signatures match. Use `Add`, `Sub`, `Mul`, `Div`, `Neg`, `Eq` by convention,
> and expect V4 to start enforcing them.

`doctrine` **declarations** do not parse at all:

```text
error: unexpected 'doctrine' — this token cannot start an expression
```

So a doctrine is never a real contract in V3, and there is no generic bound
(`task f<T: Displayable>(...)`), no `dyn Doctrine`, and no dynamic dispatch.

## Shapes as values

Shapes live in runtime storage and are handled by reference. Two consequences:

- Passing a shape to a task and mutating a field inside is **visible to the
  caller**. There is no implicit copy.
- Assigning one shape binding to another aliases the same storage.

To get an independent value, construct a new one — a small `copy` associated
method is the usual idiom:

```fk
impl Rect {
    task copy_of(self) -> Rect {
        give back Rect { w: self.w, h: self.h }
    }
}
```

Under `--strict-borrow` the Phase-1 checker additionally treats user shapes as
single-owner move types, so a use after move is reported.

## Backend support

Shape construction, field access, method execution and dotted `{shape.field}`
interpolation are verified executable evidence on the **LLVM backend only**.

> [!warn]
> The C backend (`--c`) may transpile shape declarations, but packaged shape
> runtime storage is explicitly not a claimed executable path. If your program
> declares a shape, build it with the default LLVM backend.

## What shapes cannot do

| Feature | Status |
|---|---|
| Generic fields `shape Pair<A, B>` | V4 |
| Field default values | V4 |
| `variant` sum types | V4 |
| `alias` type aliases | V4 |
| `doctrine` declarations | V4 |
| Doctrine bounds on generics | V4 |
| `dyn Doctrine` and vtables | V4 |
| Real operator dispatch through `Add` etc. | V4 |
| Field visibility / `launch` on fields | V4 |
| `@layout(C)`, `@repr(u32)` | V4 |
| `Shared<T>` / `Weak<T>` | V4 |
| A destructor or `drop` hook | V4 |
