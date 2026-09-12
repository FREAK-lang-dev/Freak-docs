# Standard library

> Every callable V3 recognises: the compiler builtins, and the FREAK-source modules linked into your build.

There are two distinct surfaces, and the difference matters.

**Compiler builtins** are known to the type checker itself. They always exist,
need no import, and work under `freak check`.

**Standard-library tasks** live in `std/*.fk` as ordinary FREAK source. The CLI
concatenates those files ahead of yours during `freak build` and `freak run`.
They are global tasks in the same flat namespace as your own.

> [!warn]
> `freak check` compiles your file **alone**. Anything from `std/` reports
> `unknown callable`. Use `freak build` or `freak run` to type-check code that
> uses the standard library.

## How modules are loaded

`use` lines are rewritten to comments before parsing, so they never reach the
grammar. They survive only as a **textual trigger** telling the build to link
an optional module.

| Module | Loaded |
|---|---|
| `std/math.fk`, `std/string.fk`, `std/convert.fk`, `std/algorithm.fk`, `std/json.fk`, `std/version.fk` | Always |
| `std/runtime.fk`, `std/http.fk` | Always, LLVM backend only |
| `std/math3d.fk` | Only if the source text contains `use std::math3d` |
| `std/zip.fk` | Only if the source text contains `use std::zip` |
| `std/ui/window.fk` | Only if the source text contains `use std::ui` |
| `packages/cockpit/src/*.fk` | Only if the source text contains `use cockpit` |

So `use std::ui` is not an import — it is a build flag written in import
syntax. Everything else is already in scope without it.

## Prelude builtins

| Call | Signature | Notes |
|---|---|---|
| `say(value)` | scalar `-> void` | Prints with a newline. Accepts `int`, `num`, `word`, `bool` — **not** a shape |
| `ask(prompt)` | `word -> word` | Reads a line from stdin |
| `panic(message)` | `word -> void` | Aborts the process |

`say` takes a statement form as well as a call form — `say "x"` and
`say("x")` are identical, because `("x")` is just a parenthesised expression.

## Conversion builtins

| Call | Signature |
|---|---|
| `word_from_int(i)` | `int -> word` |
| `word_from_bool(b)` | `bool -> word` |
| `word_to_int(w)` | `word -> int` |
| `word_concat(a, b)` | `word, word -> word` |
| `word_join(handle)` | `int -> word` |
| `char_to_word(code)` | `int -> word` |
| `format_num(f)` | `num -> word` |
| `parse_num(w)` | `word -> num` |
| `parse_status()` | `-> int` — non-zero if the last checked parse failed |
| `parse_clear_status()` | `-> void` |

## `word` methods

Covered in full in [Words & interpolation](words.html#methods):
`.length()`, `.trim()`, `.to_upper()`, `.to_lower()`, `.contains()`,
`.starts_with()`, `.ends_with()`, `.replace()`, `.substring()`, `.char_at()`,
`.to_int()`, `.to_num()`, `.parse_int()`, `.parse_num()`, `.checksum()`,
`.repeated(n)`, plus seven internal
`snapshot_*` helpers.

Scalar methods: `int.to_num()`, `int.to_word()`, `num.to_int()`,
`num.to_word()`, `bool.to_word()`.

## Lists and arrays

Typed `List<T>`: `List::new()`, `List::with_capacity(n)`,
`List::filled(v, n)`, indexing, `.length()`, `.push()`, `.pop()`,
`.capacity()`, `.reserve(n)`, `.clear()`.

Legacy handle: `array_new`, `array_push`, `array_get`, `array_set`,
`array_len`, `array_release`, `word_join`.

Both, and when each applies — see [Lists & arrays](arrays.html).

## WordBuilder

`word_builder::new`, `with_capacity`, `reserve`, `append`, `append_char`,
`append_int`, `length`, `capacity`, `clear`, `finish`, `discard` — see
[Words & interpolation](words.html#building-words-incrementally).

## ByteBuffer

The only builtin type with real method syntax. Constructed with
`ByteBuffer::new()` or `ByteBuffer::with_capacity(n)`.

{{example:bytebuffer}}

| Method | Signature | Notes |
|---|---|---|
| `.length()` | `-> int` | Bytes written |
| `.capacity()` | `-> int` | |
| `.position()` | `-> int` | The read/seek cursor |
| `.remaining()` | `-> int` | Bytes from the cursor to the end |
| `.reserve(n)` | `int -> void` | |
| `.seek(pos)` | `int -> void` | Move the read cursor |
| `.clear()` | `-> void` | |
| `.truncate(n)` | `int -> void` | |
| `.write_byte(b)` | `int -> void` | |
| `.write_int(n)` | `int -> void` | |
| `.write_int_be(n)` | `int -> void` | Big-endian |
| `.write_word(w)` | `word -> void` | |
| `.read_byte()` | `-> int` | |
| `.read_int()` | `-> int` | |
| `.read_int_be()` | `-> int` | |
| `.read_word(len)` | `int -> word` | |
| `.slice(from, len)` | `int, int -> ByteBuffer` | |
| `.to_word()` | `-> word` | |
| `.status()` | `-> int` | Last failure code; `0` is clean |
| `.clear_status()` | `-> void` | |
| `.release()` | `-> void` | Free the buffer |

> [!note]
> Writes append to the end; `position()` is the **read** cursor, so it stays at
> `0` until you read or `seek`. Errors are reported out-of-band through
> `status()` rather than by return value, since V3 has no `result<T, E>`.

This is the closest thing V3 has to the bible's `std::bytes` §7.14.

## `math::` builtins

Floating point, over `num`.

{{example:stdlib_math}}

| Call | Signature |
|---|---|
| `math::sqrt(x)` | `num -> num` |
| `math::pow(base, exp)` | `num, num -> num` |
| `math::sin(x)` / `math::cos(x)` / `math::tan(x)` | `num -> num` |
| `math::floor(x)` / `math::ceil(x)` | `num -> num` |

That is the entire `math::` namespace. No `log`, `exp`, `asin`, `atan2`, `abs`,
`gcd`, `simd` — those bible entries are V4.

## `fs::` builtins

{{example:files}}

| Call | Signature | Notes |
|---|---|---|
| `fs::read(path)` | `word -> word` | Empty word on failure |
| `fs::write(path, content)` | `word, word -> void` | |
| `fs::append(path, content)` | `word, word -> void` | |
| `fs::exists(path)` | `word -> bool` | |
| `fs::delete(path)` | `word -> bool` | **File only.** `true` when the file was removed *or was already absent*; `false` when it could not be unlinked |
| `fs::list_dir(path)` | `word -> word` | Encoded listing |
| `fs::make_dir(path)` | `word -> void` | |

There is no `fs::copy`, `fs::move`, `fs::is_file`, `fs::is_dir`,
`dir::create_all` or `dir::delete`, and no `result<T, E>` — errors surface as
empty words or `false`.

## `process::` builtins

{{example:process_time}}

| Call | Signature |
|---|---|
| `process::args_count()` | `-> int` |
| `process::arg(i)` | `int -> word` |
| `process::env(name)` | `word -> word` |
| `process::exec(cmd)` | `word -> int` |
| `process::exec_capture(cmd)` | `word -> word` |
| `process::exit(code)` | `int -> void` |
| `process::input()` | `-> word` |
| `process::pid()` | `-> int` |
| `process::set_env(name, value)` | `word, word -> void` |

> [!warn]
> `process::args()` is **deliberately rejected** by V3 rather than exposing the
> runtime's raw `argv` pointer as a fake array handle. Use the indexed pair
> `process::args_count()` and `process::arg(i)`. Argument 0 is the executable
> path.

## `time::` builtins

| Call | Signature |
|---|---|
| `time::now_ms()` | `-> int` — milliseconds since the epoch |
| `time::monotonic_ns()` | `-> int` — nanoseconds from a monotonic clock |

Use `monotonic_ns()` for measuring elapsed time; it does not jump when the wall
clock is adjusted.

There is no `sleep`, no `Instant`, no `Duration`, and no duration literals like
`500.milliseconds`.

## `tcp::` builtins

| Call | Signature |
|---|---|
| `tcp::connect(host, port)` | `word, int -> int` — socket handle |
| `tcp::send(sock, data)` | `int, word -> int` |
| `tcp::recv(sock, max)` | `int, int -> word` |
| `tcp::recv_all(sock, max)` | `int, int -> word` |
| `tcp::close(sock)` | `int -> void` |

`std/http.fk` builds on these and is linked automatically on the LLVM backend.

### The newer socket API

A second, lower-level socket surface exists alongside the calls above. It adds
listening, accepting, timeouts and `ByteBuffer`-based transfer.

| Call | Signature |
|---|---|
| `tcp::socket_connect(host, port)` | `word, int -> int` |
| `tcp::socket_listen(host, port)` | `word, int -> int` |
| `tcp::socket_accept(listener)` | `int -> int` |
| `tcp::socket_local_port(sock)` | `int -> int` |
| `tcp::socket_status(sock)` | `int -> int` |
| `tcp::socket_eof(sock)` | `int -> bool` |
| `tcp::socket_set_timeout(sock, ms)` | `int, int -> void` |
| `tcp::socket_send(sock, buf, off, len)` | `int, ByteBuffer, int, int -> int` |
| `tcp::socket_send_all(sock, buf, off, len)` | `int, ByteBuffer, int, int -> int` |
| `tcp::socket_receive(sock, buf, max)` | `int, ByteBuffer, int -> int` |
| `tcp::socket_close(sock)` | `int -> void` |

> [!note]
> This is the first V3 API that can write a server, since `socket_listen` and
> `socket_accept` have no equivalent in the older `tcp::connect` family. Like
> `ByteBuffer`, it reports failure through a `status()`-style code rather than a
> `result<T, E>`.

## `ui::` builtins

A raw, indexed windowing API: `ui::create_window`, `ui::destroy_window`,
`ui::poll_events`, `ui::begin_frame`, `ui::end_frame`, `ui::clear`,
`ui::fill_rect`, `ui::stroke_rect`, `ui::fill_circle`, `ui::draw_line`,
`ui::draw_text`, `ui::measure_text`, `ui::get_width`, `ui::get_height`,
`ui::set_clip`, `ui::reset_clip`, and an `ui::event_*` family (`kind`, `key`, `pressed`, `character`, `mouse_x`,
`mouse_y`, `button`, `repeat`, `scroll_dy`, `width`, `height`, `gained`).

> [!warn]
> `std::ui` runs on the **LLVM backend, on Windows, through the Win32/GDI
> runtime only**. There is no macOS or Linux native backend, and the C backend
> has no executable shape storage for UI programs. `WindowConfig.vsync` is
> retained but ignored, events use the raw indexed API rather than an owned
> event list, and COCKPIT is a source preview, not a frozen package.

Geometry crosses this ABI as pixel-addressed `int`. Convert from `num` before
calling.

## `std::math` — integer maths

{{example:stdlib_math|source}}

| Task | Signature |
|---|---|
| `std_abs(x)` | `int -> int` |
| `std_sign(x)` | `int -> int` |
| `std_min(a, b)` / `std_max(a, b)` | `int, int -> int` |
| `std_clamp(x, lo, hi)` | `int, int, int -> int` |
| `std_pow(base, exp)` | `int, int -> int` |
| `std_gcd(a, b)` / `std_lcm(a, b)` | `int, int -> int` |
| `std_factorial(n)` | `int -> int` |
| `std_fibonacci(n)` | `int -> int` |
| `std_is_even(x)` / `std_is_odd(x)` | `int -> bool` |
| `int_to_word(n)` | `int -> word` |

## `std::string`

Listed in full in [Words & interpolation](words.html#standard-library-word-tasks).

## `std::convert`

{{example:stdlib_convert}}

| Task | Signature |
|---|---|
| `int_to_hex(n)` / `int_to_bin(n)` / `int_to_oct(n)` | `int -> word` |
| `char_to_digit(c)` | `word -> int` |
| `word_to_int_safe(s)` | `word -> int` — `0` on failure, never panics |
| `bool_to_word(b)` | `bool -> word` |

## `std::algorithm`

See [Arrays](arrays.html#stdalgorithmfk-helpers), including the two functions
that are broken.

## `std::json`

A complete JSON parser in pure FREAK. Values are `int` handles.

{{example:stdlib_json}}

| Task | Signature |
|---|---|
| `json_init()` | `-> void` — call once before parsing |
| `json_parse(source)` | `word -> int` |
| `json_stringify(handle)` | `int -> word` |
| `json_get_type(h)` | `int -> word` — `o`, `a`, `s`, `n`, `b`, `z` |
| `json_get_str(h)` / `json_get_int(h)` / `json_get_bool(h)` | `int -> word` / `int` / `bool` |
| `json_is_null(h)` | `int -> bool` |
| `json_obj_len(h)` / `json_obj_has(h, key)` / `json_obj_get(h, key)` / `json_obj_key_at(h, i)` | object access |
| `json_arr_len(h)` / `json_arr_get(h, i)` | array access |

## `std::version`

Semantic-version parsing and constraint matching — the machinery behind
Hangar's dependency resolution.

{{example:stdlib_version}}

| Task | Signature |
|---|---|
| `ver_parse(version)` | `word -> word` — an encoded parse result |
| `ver_major` / `ver_minor` / `ver_patch` | `word -> int` |
| `ver_pre` / `ver_build` / `ver_to_string` | `word -> word` |
| `ver_compare(a, b)` | `word, word -> int` |
| `ver_eq` / `ver_lt` / `ver_gt` / `ver_lte` / `ver_gte` | `word, word -> bool` |
| `ver_bump_major` / `ver_bump_minor` / `ver_bump_patch` | `word -> word` |
| `ver_satisfies(version, constraint)` | `word, word -> bool` |
| `version_matches_constraint(version, constraint)` | `word, word -> bool` |

## Modules that do not exist

The bible's Section 7 lists many more. None of these are in V3:

`std::iter` (`.map`, `.filter`, `.fold`, …), `Map<K,V>`, `Set<T>` and
`Lineup<T>` from `std::collections`, `std::io` beyond `say` / `ask`,
`std::random`, `std::thread`, `std::anime`, `std::narrative`, `std::test`,
`std::mem` (`Shared`, `Weak`, `size_of`, `alloc`), `std::ffi`, `std::os`,
`std::panic`, `std::regex`, `std::crypto`.

Partially covered, in a V3-specific shape rather than the bible's:

| Bible module | V3 equivalent |
|---|---|
| `std::collections` `List<T>` | Typed `List<T>` with indexing and `List::filled` — no `push`/`pop`/`sort` |
| `std::bytes` `ByteBuffer` | The builtin `ByteBuffer` type |
| `std::word` `WordBuilder` | `word_builder::*` over an `int` handle |
| `std::net` | `tcp::socket_*`, including listen and accept |
