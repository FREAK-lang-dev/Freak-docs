# Compiler CLI

> Every subcommand and flag the shipping V3 `freak` binary actually recognises.

```sh
freak <command> [file.fk] [options]
```

## Commands

| Command | What it does |
|---|---|
| `freak build <file.fk>` | Compile to a native binary beside the source |
| `freak run <file.fk>` | Build, then execute |
| `freak check <file.fk>` | Lex, parse and type-check only — **no standard library** |
| `freak transpile <file.fk>` | Emit `.c` or `.ll` and stop |
| `freak init` | Scaffold a new project |
| `freak doctor` | Validate the toolchain and payload |
| `freak upgrade` | Download and stage a newer FREAK |
| `freak hangar <cmd>` | Package manager (also a standalone `hangar` binary) |
| `freak version`, `freak --version`, `freak -V` | Print the version |
| `freak help`, `freak --help`, `freak -h` | Print the help screen |
| `freak flex` | Print the banner |
| `freak test` | Source-checkout shim around `python tests/suite/run_tests.py` |
| `freak audit-science` | List every `for science,` call site |
| `freak audit-trust` | List every `trust me` block with its honor level |
| `freak audit-miracles` | List every `deus_ex_machina` block |
| `freak foreshadow-audit` | Report unpaid `foreshadow` bindings |
| `freak audit-conformance` | Verify the implementation status table against the code |

> [!warn]
> **`freak check` is not a fast `freak build`.** It compiles your file *alone*.
> It does not strip `use` lines and it does not link the standard library, so
> anything from `std/` — `string_reverse`, `std_gcd`, `ver_parse`, `json_parse`
> — reports `unknown callable`. Use `check` for pure-builtin code; use `build`
> or `run` for everything else.

> [!note]
> The audit subcommands shell out to `python -m freakc`. They need the Python
> bootstrap package and the repository's audit inputs; the native V3 binary
> does not contain that auditor. The same is true of `freak test`.

## Options

| Flag | Effect |
|---|---|
| `--llvm` | LLVM IR backend. **Default.** Full language surface |
| `--c` | Portable C backend. No claimed executable shape storage |
| `--opt=N` | Optimisation level, `0`–`3`. Default `2` |
| `--target=TRIPLE` | Cross-compile target triple |
| `--strict-borrow` | Enable the opt-in Phase-1 ownership checker |

Flags may appear in any order after the file:

```sh
freak run game.fk --c --opt=3
freak build game.fk --target=x86_64-linux-gnu
freak build game.fk --strict-borrow
```

> [!v4]
> `-o output_path` does not exist. The output name is always the source
> basename plus `.exe` (Windows) or no extension elsewhere. `--voice=`,
> `--clearance=` and `--build-mode=` are also V4-only.

## `--strict-borrow`

Without this flag V3 does no ownership checking at all. With it, a Phase-1
checker runs after type checking and enforces three rules:

- **Immutable bindings.** `pilot x = ...` cannot be reassigned; `pilot mut x = ...` can.
  Reassigning without `mut` reports *"This binding was sworn to silence."*
- **Single-owner moves** for `word`, arrays and user shapes. Use after move
  reports *"Shirogane. You gave this away."*
- **Copy primitives.** `int`, `num` and `bool` are copied on assignment; both
  bindings stay valid.

Nominal member validation — checking that a field or method you name actually
exists on the shape — always runs, flag or not.

## Backends compared

| | LLVM (`--llvm`) | C (`--c`) |
|---|---|---|
| Scalars, control flow, words | yes | yes |
| Arrays and native calls | yes | yes |
| `shape` construction, fields, methods | yes | **not a claimed executable path** |
| Dotted `{shape.field}` interpolation | yes | not claimed |
| `std::ui` windows | Windows only, Win32/GDI | no |
| `std::http` | yes | not linked |
| Debug info | LineTablesOnly DWARF | via Clang |

The rule of thumb: if your program declares a `shape`, build it with the
default LLVM backend.

## Hangar

`hangar` is the package manager, reachable as `freak hangar <cmd>` or as a
standalone binary.

| Subcommand | Status |
|---|---|
| `hangar init [name]` | works |
| `hangar add <name> [constraint]` | works |
| `hangar add <name> <repo> [version]` | works |
| `hangar remove <name>` | works |
| `hangar install` | works |
| `hangar install freak` | works |
| `hangar update [package]` | works |
| `hangar outdated` | works |
| `hangar version [patch\|minor\|major]` | works |
| `hangar audit [--fix]` | works |
| `hangar login`, `hangar publish [--dry-run]` | works |
| `hangar search <query>` | not in this build |

A `hangar.toml` as the tool actually writes it:

```toml
[project]
name = "demo"
version = "0.1.0"

[dependencies]
muvluv = "^2.0"
```

Dependency constraints are matched by `std/version.fk`, whose semver
comparison and `^`-constraint logic you can call directly — see
[Standard library](stdlib.html#stdversion).

> [!warn]
> **Installing a package does not make it usable.** `freak build` never reads
> `hangar_modules/` or `[dependencies]`, and `use pkg::{…}` is stripped to a
> comment before parsing. Dependencies have to be concatenated into your source
> by hand. See [Hangar & packages](hangar.html) for the full picture and the
> working pattern.

## Environment

| Variable | Meaning |
|---|---|
| `FREAK_HOME` | Authoritative payload root. Overrides checkout-relative and executable-adjacent discovery |

Discovery order for `runtime/` and `std/`:

1. `$FREAK_HOME`
2. the repository root, if the executable sits inside a checkout
3. the directory beside the executable
4. the default installed home

Both `runtime/freak_abi` and `std/freak_abi` must carry the marker the compiler
expects, or the build stops before parsing.

## Generated files

`freak build hello.fk` leaves behind:

```text
hello.fk        your source
hello.fk.ll     LLVM IR   (or hello.fk.c with --c)
hello.exe       the binary
hello.pdb       debug info, Windows
```

`freak transpile` produces only the `.ll` or `.c`.
