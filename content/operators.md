# Operators

> Full precedence table, exact type rules, and the four anime operators V3 really implements.

## Precedence

Loosest binding first. Everything on one row is left-associative.

| Level | Operators |
|---|---|
| 1 | `or` |
| 2 | `and` |
| 3 | `==` `!=` `<` `>` `<=` `>=` |
| 4 | `+` `-` `NAKAMA` |
| 5 | `*` `/` `%` |
| 6 (prefix) | `not` `-` `PLUS ULTRA` `FINAL FORM` `TSUNDERE` |
| 7 (postfix) | `.field` `.method()` `[index]` `\|>` |

Parentheses group as expected.

{{example:operators}}

## Type rules

The checker is strict — these are the exact rules, not approximations.

| Operator | Accepts | Produces |
|---|---|---|
| `+` | both numeric (`int`/`num`), **or** both `word` | `num` if either side is `num`, else `int`; `word` for word+word |
| `-` `*` `/` | both numeric | `num` if either side is `num`, else `int` |
| `%` | **both `int`** | `int` |
| `NAKAMA` | **both `int`** | `int` |
| `and` `or` | **both `bool`** | `bool` |
| `==` `!=` | equality-compatible types | `bool` |
| `<` `>` `<=` `>=` | both numeric | `bool` |
| `not` | `bool` | `bool` |
| `-` (prefix) | numeric | same as operand |
| `PLUS ULTRA` `FINAL FORM` `TSUNDERE` | **`int` only** | `int` |

Two consequences worth internalising:

- **`%` is integer-only.** `7.5 % 2.0` is a type error, not a float remainder.
- **`and` / `or` do not coerce.** There is no truthiness. `if count and flag` is
  an error unless `count` is already `bool`.

`+` is the only overloaded operator: numeric addition and word concatenation.

```fk
say "Muv" + "-" + "Luv"
say word_from_int(2 + 3)
```

> [!v4]
> `**` (exponent) does not exist — you get `expected ',', found '**'`. Use
> `math::pow(base, exp)` for `num`, or `std_pow(base, exp)` for `int`.

## Negative numbers

There is no negative literal. `-5` is unary minus applied to `5`. In an
initialiser position, write the subtraction the compiler's own source uses:

```fk
pilot below: int = 0 - 5
say word_from_int(-below)
```

## The anime operators

Four of the bible's anime operators are implemented. Their V3 semantics are
**not** what the specification describes — the specification defines emotional
scaling formulas; V3 implements simple integer arithmetic.

{{example:anime_operators}}

| Operator | Form | V3 lowering | Bible says |
|---|---|---|---|
| `FINAL FORM` | prefix, `int` | `x * x` | postfix `base FINAL FORM`, plus a 5-second build pause |
| `PLUS ULTRA` | prefix, `int` | `x * 2` | infix `base PLUS ULTRA emotion` → `base * (1 + e²)` |
| `TSUNDERE` | prefix, `int` | `0 - x` | postfix; `!x` for bool, `-x` for num |
| `NAKAMA` | infix, `int` | `a + b` | `a + b + (a * b * 0.1)` |

> [!warn]
> Position and type both differ from the specification. In V3 all three unary
> operators are **prefix** and accept **`int` only**. `base FINAL FORM` fails
> with `expected ',', found 'FINAL FORM'`, and `TSUNDERE true` fails with
> `operator 'TSUNDERE' does not accept bool`.

Keyword matching is case-insensitive, so `plus ultra`, `Plus Ultra` and
`PLUS ULTRA` all lex to the same token. Both words must be present — `PLUS`
alone is an ordinary identifier.

## The pipe operator

`|>` binds at postfix precedence and rewrites a call so the left value becomes
its **first** argument.

{{example:pipe}}

```text
x |> f()        is  f(x)
x |> f(y)       is  f(x, y)
x |> f() |> g() is  g(f(x))
```

The right-hand side must be a bare task name followed by an optional argument
list. You cannot pipe into a method call, a shape constructor, or a namespaced
builtin like `math::sqrt`.

## Postfix forms

| Form | Meaning |
|---|---|
| `value.field` | Shape field access |
| `value.method(args)` | Instance method or builtin method call |
| `Shape::method(args)` | Associated method call |
| `namespace::call(args)` | Builtin namespace call (`math::sqrt`, `fs::read`, …) |
| `word[i]` | Indexing — **only on `word`**, yielding a one-character `word` |
| `value \|> task()` | Pipe |

Indexing an array handle with `[i]` does not work. Arrays use
`array_get(handle, i)` — see [Arrays](arrays.html).

## Operator overloading

Writing `impl Add for YourShape` registers an implementation, and the method is
callable by name. V3 does **not** rewrite the `+` token to dispatch to it — see
[Shapes & impl](shapes.html#operator-doctrines).

{{example:operator_overload}}

## Not implemented

| Operator | Status |
|---|---|
| `**` exponent | V4 — use `math::pow` / `std_pow` |
| `?` error propagation | V4 |
| `or else` fallback | V4 |
| `\|\|` as an xm3 branch separator | V4 — lexes as one token but has no grammar |
| `as?` downcast | V4 |
| `*ptr`, `.read()`, `.write()`, `.offset()`, `.cast<U>()` | V4 |
| `..` ranges | V4 |
