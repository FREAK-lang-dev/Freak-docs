# Getting started

> Build a real V3 compiler from source, then compile and run your first program.

## What you need

- **Clang** — V3 emits LLVM IR or C and hands it to Clang to produce a binary.
- **Bash** — for the reconstruction script. Git for Windows supplies a suitable shell.
- **Python 3** — only for the test harnesses and this site's tooling.

Check Clang is reachable:

```sh
clang --version
```

## Build the compiler from source

V3 is self-hosted, so building it is a bootstrap. The repository carries a
reviewed, version-controlled C seed at `build/freakc_v3.fk.c` precisely so you
never need a pre-existing FREAK binary.

The order of the eight compiler sources is fixed — they are concatenated into
one translation unit before compiling:

```text
globals.fk  helpers.fk  lexer.fk  parser.fk
checker.fk  emit_c.fk   emit_llvm.fk  main.fk
```

Build the seed, then regenerate the compiler from itself:

```sh
repo="$PWD"
work="$(mktemp -d)"

cat src/compiler/v3/globals.fk src/compiler/v3/helpers.fk \
    src/compiler/v3/lexer.fk src/compiler/v3/parser.fk \
    src/compiler/v3/checker.fk src/compiler/v3/emit_c.fk \
    src/compiler/v3/emit_llvm.fk src/compiler/v3/main.fk > "$work/freakc_v3.fk"

clang -o "$work/freakc-seed" build/freakc_v3.fk.c freakc/runtime/freak_runtime.c \
  -I freakc/runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS -lws2_32

"$work/freakc-seed" "$work/freakc_v3.fk" --c && mv "$work/freakc_v3.fk.c" "$work/stage1.c"
clang -o "$work/freakc-stage1" "$work/stage1.c" freakc/runtime/freak_runtime.c \
  -I freakc/runtime -O2 -w -lws2_32

"$work/freakc-stage1" "$work/freakc_v3.fk" --c && mv "$work/freakc_v3.fk.c" "$work/stage2.c"
clang -o "$work/freakc-stage2" "$work/stage2.c" freakc/runtime/freak_runtime.c \
  -I freakc/runtime -O2 -w -lws2_32

"$work/freakc-stage2" "$work/freakc_v3.fk" --c && mv "$work/freakc_v3.fk.c" "$work/stage3.c"
cmp "$work/stage2.c" "$work/stage3.c" && echo "fixed point reached"
```

> [!note]
> The last line is the point of the whole exercise. `stage2.c` and `stage3.c`
> must be byte-identical: the compiler built from generation 2 has to reproduce
> its own generated C exactly. That equality is the self-host fixed-point
> invariant. Native binary bytes are *not* expected to match across operating
> systems or Clang versions — only the generated C is.

On non-Windows hosts drop `-lws2_32`; use `-lm` on Linux and no extra link flag
on macOS. The cross-platform automated equivalent is:

```sh
python -u tests/v3_fixed_point.py
```

## Build the `freak` CLI

The standalone `freakc` you just built takes a file and a backend flag. The
public `freak` command is a second aggregate: the same seven compiler files
plus the CLI, with `src/cli/main.fk` as the entry point instead of
`v3/main.fk`.

```sh
cat std/version.fk \
    src/compiler/v3/globals.fk src/compiler/v3/helpers.fk \
    src/compiler/v3/lexer.fk src/compiler/v3/parser.fk \
    src/compiler/v3/checker.fk src/compiler/v3/emit_c.fk \
    src/compiler/v3/emit_llvm.fk \
    src/cli/version.fk src/cli/toml.fk src/cli/lockfile.fk \
    src/cli/build.fk src/cli/run.fk src/cli/hangar.fk \
    src/cli/doctor.fk src/cli/audit.fk src/cli/main.fk > "$work/freakc_cli.fk"

"$work/freakc-stage2" "$work/freakc_cli.fk" --c
mkdir -p "$work/freak-home/bin"
clang -o "$work/freak-home/bin/freak" "$work/freakc_cli.fk.c" \
  freakc/runtime/freak_runtime.c -I freakc/runtime -O2 -w -lws2_32
```

## Install the payload

The compiler is not self-sufficient: it needs the C runtime and the standard
library beside it. The canonical inventory is
`packaging/distribution-files.manifest`, a list of `source|destination` pairs.

```sh
while IFS='|' read -r src dst; do
  case "$src" in ''|\#*) continue ;; esac
  mkdir -p "$work/freak-home/$(dirname "$dst")"
  cp "$src" "$work/freak-home/$dst"
done < packaging/distribution-files.manifest
```

The layout that results:

```text
freak-home/
  bin/freak            the compiler CLI
  runtime/             freak_runtime.c, freak_llvm_runtime.c, headers
  std/                 math.fk, string.fk, convert.fk, algorithm.fk, ...
```

Both `runtime/freak_abi` and `std/freak_abi` must contain the marker the
compiler expects (`freak-v3-abi-1`), or every build stops with an ABI mismatch.

Point `FREAK_HOME` at that directory, or leave it unset and let the CLI find
the payload next to the executable:

```sh
export FREAK_HOME="$work/freak-home"
freak --version
```

## Your first program

{{example:hello}}

```sh
freak run hello.fk
```

`freak build` leaves a native binary beside the source, named after it:

```sh
freak build hello.fk     # produces hello.exe (or hello)
./hello
```

## A program with a bit more to it

{{example:fizzbuzz}}

## Check your setup

`freak doctor` validates far more than `clang --version` — it checks the C
headers, native link and execution, the optional LLD linker, the complete
runtime and standard-library payload, and a full FREAK compile-link-execute
probe.

```sh
freak doctor
freak doctor --fix
freak doctor --json
```

## Common first errors

| Message | Cause |
|---|---|
| `unexpected 'use' — this token cannot start an expression` | You ran `freak check`, which does not strip `use` lines or load the standard library. Use `freak build` or `freak run`. |
| `expected an identifier for shape name, found 'Pilot'` | Keywords are case-insensitive; `Pilot` is the `pilot` keyword. Rename. |
| `unknown callable 'string_reverse'` | Same cause — `freak check` compiles your file alone, without `std/`. |
| `ABI MISMATCH` | `runtime/freak_abi` or `std/freak_abi` does not match the compiler's expected marker. Reinstall the payload. |
| `expected '=', found '<'` | Generic type syntax. V3 has none — see [Not in V3](not-in-v3.html). |
