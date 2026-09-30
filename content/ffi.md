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

| FREAK type | C backend | LLVM backend (default) |
|---|---|---|
| `int` | `int64_t` | `i64` |
| `bool` | `bool` | `i64` (0 / 1) |
| `void` | `void` | `void` |
| `num` | `double` | **`i64` — broken, see below** |
| `word` | `freak_word` struct, by value | `i64` handle |

> [!warn]
> **`num` across `extern` is silently wrong on the LLVM backend**, which is the
> default. The declaration is emitted as `declare i64 @f(i64)`, so a C function
> expecting a `double` receives the bit pattern of an unrelated integer and
> hands back garbage that nothing flags.

Declaring two libm functions and calling them both ways:

```fk
extern task sqrt(v: num) -> num
extern task floor(v: num) -> num
```

| Call | LLVM backend (default) | C backend (`--c`) |
|---|---|---|
| `sqrt(2.0)` | `nan` | `1.414213562` |
| `floor(3.7)` | `4.940656458e-324` | `3` |

Verified on 0.14.2. If you need doubles across the boundary, build with `--c`,
or pass them as scaled integers.

The dependable subset on **both** backends is `int`, `bool` and `void`.

> [!warn]
> **`word` is not `char*`** on either backend. Under LLVM it is an `i64` handle
> into the runtime's word table; under the C backend it is a four-field
> `freak_word` struct passed by value. Declaring
> `extern task puts(s: word) -> int` compiles and then hands C something that is
> not a pointer.
>
> This is not hypothetical: `std/algorithm.fk` declares
> `extern task freak_word_compare(a: word, b: word) -> int` and the resulting
> `array_sort_word` **segfaults**.

Strings do cross the boundary, but through a shim you write rather than through
a direct declaration — see [Linking a real C library](#linking-a-real-c-library).

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

## Linking a real C library

`extern task` resolves a symbol; it does not tell the linker where to find one.
There is no `link="raylib"`, no `-l` flag on `freak build`, and no way to add
one. `freak build` links the FREAK runtime and the platform C library and
nothing else, which is why the `abs` example above works and a third-party
library does not.

The way through is to stop using `freak build` for the final step. `freak
transpile` emits the C or LLVM IR, and you link it yourself:

```sh
freak transpile app.fk --c
clang -o app app.fk.c       path/to/freakc/runtime/freak_runtime.c       shim.c       -Ipath/to/freakc/runtime       -lraylib -lopengl32 -lgdi32 -lwinmm       -O2 -w -D_CRT_SECURE_NO_WARNINGS -lws2_32
```

On the LLVM backend the same idea holds — `freak transpile app.fk --llvm`, then
hand clang `app.fk.ll` plus **both** `freak_runtime.c` and
`freak_llvm_runtime.c`.

### Why you need a shim

`extern` only speaks `int`, `bool`, `void` and (on the C backend) `num`. Most C
libraries ask for more than that: `const char*` for names and titles, and small
structs by value for points, colours and rectangles. Neither crosses a bare
`extern`.

So put a shim between them — a small C file, compiled and linked alongside,
that takes the flat scalars FREAK can express and builds the real arguments:

```c
/* shim.c -- compiled and linked alongside, C backend */
#include "freak_runtime.h"
#include <raylib.h>

void shim_window(freak_word title, int64_t w, int64_t h) {
    InitWindow((int)w, (int)h, freak_word_to_cstr(title));
}

void shim_circle(int64_t x, int64_t y, int64_t radius,
                 int64_t r, int64_t g, int64_t b, int64_t a) {
    Vector2 centre = { (float)x, (float)y };
    Color colour = { (unsigned char)r, (unsigned char)g,
                     (unsigned char)b, (unsigned char)a };
    DrawCircleV(centre, (float)radius, colour);
}
```

`freak_word_to_cstr` is declared in `freak_runtime.h` and is the supported way
to get bytes out of a `word`. Declaring the shim is then ordinary:

```fk
extern task shim_window(title: word, w: int, h: int) -> void
extern task shim_circle(x: int, y: int, radius: int,
                        r: int, g: int, b: int, a: int) -> void
```

> [!note]
> A shim written for one backend will not work on the other. The C backend
> passes a `freak_word` struct; the LLVM backend passes an `i64` handle, which
> the shim turns into a `freak_word` with
> `freak_word freak_llvm_word_view(int64_t handle)`. Everything else is the
> same. Pick a backend and stay on it.

### So, raylib?

Yes, with a shim, and no, not comfortably.

Every raylib call you want needs a line of C: `Vector2`, `Color`, `Rectangle`
and `Camera2D` are structs by value, `InitWindow` and `DrawText` take
`const char*`, and `float` is not a FREAK type at all. None of that reaches
`extern` directly. What you end up with is a hand-written C wrapper for your
slice of the raylib API, plus a FREAK file of `extern` declarations mirroring
it, plus a manual clang line. That is a real, working program — the shim
pattern above is verified end to end against a C library with exactly these
shapes — but the interesting part of it is C, and it does not survive a
`freak build`.

There is also no float type. Positions and colours go across as `int` and get
cast in the shim, which is fine for pixels and 0-255 channels and lossy for
anything else. `num` would be the answer and it is broken on the default
backend, as above.

If the goal is to see something on screen from FREAK today, that is the price.
If the goal is a comfortable binding, wait for V4: `extern` blocks, `link=`,
`@layout(C)` structs and raw pointers are all specified, and all of them are
what this section is working around.

## Practical guidance

Keep the FFI surface to scalars:

```fk
extern task abs(v: int) -> int
extern task labs(v: int) -> int

task main() -> void {
    say word_from_int(abs(0 - 7))
}
```

Anything past scalars belongs in a shim you compile alongside, not in the
`extern` declaration — see [Linking a real C library](#linking-a-real-c-library).

Forking the runtime is the other option, and a worse one for library work: add
your function to `freakc/runtime/freak_runtime.c` and wire it through the
builtin table, the way `fs::read` and `tcp::send` are. That gets you a builtin
rather than an `extern`, and it means maintaining a patched compiler.
