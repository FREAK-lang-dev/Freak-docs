# extern & FFI

> V3's foreign-function interface is one line long, and that is the whole of it.

## The declaration form

```fk
extern task name(param: type, param: type) -> returntype
```

One line, no body, no block, no attributes. Parameter and return types use the
usual [type grammar](language-basics.html#the-type-annotation-grammar), but only
a small set makes sense at a C boundary: `int`, `num`, `bool`, `void`. See
[type mapping](#type-mapping) below before reaching for `word` — and never for
`List<T>` or `ByteBuffer`, which have no C representation.

{{example:extern}}

The declared symbol must be resolvable by the linker when Clang links the
program. Because V3 already links the C runtime and the platform C library,
ordinary libc symbols are available with no extra flags — `abs` above is
`abs(3)` from the C library.

## The reserved symbol namespace

V3 mangles source task symbols into a reserved `__freak_` namespace so
generated code can never be shadowed by user names. Two rules follow:

- An `extern task` whose native name begins with `__freak_` is a **hard type
  error**. This stops a raw ABI symbol from being captured by generated locals,
  parameters, globals or task symbols.
- A source task cannot redeclare a compiler builtin call name. Declaring
  `task say(...)` or `extern task fs::read(...)` is rejected before either
  backend emits code.

## Type mapping

There are no `std::ffi` aliases in V3 — no `c_int`, `c_size`, `usize`,
`wchar`. You declare the FREAK type and the backend picks the representation.

| FREAK type | LLVM representation |
|---|---|
| `int` | `i64` |
| `num` | `double` |
| `bool` | `i64` (0 / 1) |
| `word` | `i64` handle into the runtime's word table |
| `void` | `void` |

> [!warn]
> **`word` is not `char*`.** On the LLVM backend a `word` is an `i64` handle
> managed by the FREAK runtime, not a pointer to bytes. Declaring
> `extern task puts(s: word) -> int` will compile and then pass a handle where
> C expects a pointer.
>
> This is not hypothetical: `std/algorithm.fk` declares
> `extern task freak_word_compare(a: word, b: word) -> int` and the resulting
> `array_sort_word` **segfaults**. Treat `word` across `extern` as unsafe until
> you have checked the specific runtime function's real C signature.

The safe subset is `int`, `num`, `bool` and `void`. For string work, prefer the
builtin `word` methods and the runtime functions FREAK already exposes.

## Calling

An extern task is called exactly like a FREAK task, and its arguments are
type-checked against the declaration:

```fk
extern task abs(v: int) -> int

task main() -> void {
    say word_from_int(abs(0 - 41))
}
```

## Backend differences

The C backend emits a plain C call and relies on the symbol being declared by
an included header or implicitly. The LLVM backend emits a `declare` for the
symbol with the mapped signature. A signature that disagrees with the real C
function is undefined behaviour on both — there is no cross-check.

## What the bible specifies and V3 does not have

Section 16 of the bible describes a full FFI contract. Essentially none of it
is in V3:

| Feature | Status |
|---|---|
| `extern [C] { ... }` blocks | V4 — V3 takes exactly one `extern task` per declaration |
| Calling conventions (`cdecl`, `stdcall`, `system`, …) | V4 |
| `link="user32"` library binding | V4 |
| `@link_name("symbol")` | V4 |
| Variadics `args: ...` | V4 |
| `std::ffi` type aliases | V4 |
| Raw pointers `*T`, `*const T`, `*mut T` | V4 |
| `*ptr`, `.read()`, `.write()`, `.offset()`, `.cast<U>()`, `.is_null()` | V4 |
| `@layout(C)`, `@layout(C, packed=N)`, `@layout(transparent)` | V4 |
| `@repr(u32)` on fieldless variants | V4 |
| `@extern_callback("C")` and panic-abort trampolines | V4 |
| `@allow_unwinder` | V4 |
| `trust me "..." on my honor as .level { }` | V4 — does not parse |
| `alloc`, `free`, `size_of<T>()`, `align_of<T>()` | V4 |
| `std::os::windows` / `macos` / `linux` | V4 |
| Conditional imports `use[target_os="windows"] ...` | V4 |

There is no `trust me` block in V3, which means there is no unsafe boundary to
gate — and equally, no honour-level audit trail on the code you actually
compile. `freak audit-trust` scans source text for `trust me` blocks that the
compiler itself would reject.

## Practical guidance

Keep the FFI surface to scalars:

```fk
extern task abs(v: int) -> int
extern task labs(v: int) -> int

task main() -> void {
    say word_from_int(abs(0 - 7))
}
```

If you need to hand a string to C, do it from the C side instead: add your
function to `freakc/runtime/freak_runtime.c`, expose it the way the existing
runtime bridges do, and call it through the builtin table rather than through
`extern`. That is how `fs::read`, `tcp::send` and the `ui::*` family are wired,
and it is the only path that handles the `word` representation correctly.
