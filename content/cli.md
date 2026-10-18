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
| `freak init NAME [--template=cli\|lib\|http]` | Create a project: manifest, sources and a test |
| `freak doctor` | Validate the toolchain and payload |
| `freak upgrade` | Download and stage a newer FREAK |
| `freak hangar <cmd>` | Package manager (also a standalone `hangar` binary) |
| `freak version`, `freak --version`, `freak -V` | Print the version |
| `freak help`, `freak --help`, `freak -h` | Print the help screen |
| `freak flex` | Print the banner |
| `freak test` | In a project: build and run the tests listed in `hangar.toml` |
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
> does not contain that auditor.

## Options

| Flag | Effect |
|---|---|
| `--llvm` | LLVM IR backend. **Default.** Full language surface |
| `--c` | Portable C backend. No claimed executable shape storage |
| `--O0` … `--O3` | Optimisation level. Default `--O2`. The older `--opt=N` still works |
| `--flto`, `--tlto` | Full or thin LTO. The older `--lto[=thin\|full\|off]` still works |
| `--diagnostic-cast=MODE` | `off` (default), `minimal` or `normal`. Adds a character's comment after each diagnostic; the diagnostic and exit status are unchanged |
| `--target=TRIPLE` | Cross-compile target triple |
| `--strict-borrow` | Enable the opt-in Phase-1 ownership checker |
| `-o NAME`, `--output=NAME` | Name of the output binary. Default: the source basename |

Flags may appear in any order after the file:

```sh
freak run game.fk --c --O3
freak build game.fk --O3 --flto
freak build game.fk --target=x86_64-linux-gnu
freak build game.fk --strict-borrow
```

> [!note]
> `-O` and LTO flags apply to `build` and `run` only. Both commands keep
> verified runtime objects in a per-user cache and reuse them on later builds.
> An entry is reused only when the compiler, runtime sources, target,
> optimisation level and LTO setting all match; otherwise the runtime is
> compiled again. Your own code is still compiled fresh every time.

> [!v4]
> `--voice=`, `--clearance=` and `--build-mode=` are V4-only. The output name
> can be chosen with `-o NAME` or `--output=NAME`; without it, it is the source
> basename plus `.exe` (Windows) or no extension elsewhere.

## `--strict-borrow`

Without this flag V3 does no ownership checking. With it, a Phase-1 checker
runs after type checking and enforces two rules:

- **Single-owner moves** for `word`, arrays and user shapes. Use after move
  reports *"Shirogane. You gave this away."*
- **Copy primitives.** `int`, `num` and `bool` are copied on assignment; both
  bindings stay valid.

Mutability is not part of this flag. `fixed` and `grounded` pilots are always
enforced, and plain pilots can always be reassigned. Nominal member validation
— checking that a field or method you name actually exists on the shape —
also always runs, flag or not.

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
| `hangar add <name> [constraint]` | works: resolves against the registry and pins the version in `hangar.lock` |
| `hangar add <name> --path <dir>` | works |
| `hangar add <name> <repo> [version]` | works |
| `hangar remove <name>` | works |
| `hangar install` | works |
| `hangar install freak` | works |
| `hangar update [package]` | works |
| `hangar outdated` | works |
| `hangar version [patch\|minor\|major]` | works |
| `hangar audit [--fix]` | works |
| `hangar auth login`, `hangar auth status`, `hangar auth logout` | works (`hangar login` / `hangar logout` are shortcuts) |
| `hangar publish [--dry-run]` | works |
| `hangar search <query>` | not in this build |

> [!warn]
> On Windows, `hangar add <name> <git-url>` fails in 0.15.1 while cleaning up
> its temporary clone (*"could not safely remove complete owned temporary
> directory"*), because Git's read-only object files can't be deleted. Clone
> the repository yourself and use `hangar add <name> --path <clone>` until the
> fix ships.

What `hangar init` writes:

```toml
project.entry = "src/main.fk"
project.kind = "app"
project.name = "demo"
project.version = "0.1.0"
```

Dependency constraints are matched by `std/version.fk`, whose semver
comparison and `^`-constraint logic you can call directly — see
[Standard library](stdlib.html#stdversion).

> [!note]
> As of 0.15, `freak build`, `freak run` and `freak test` read `hangar.toml`. A
> project's modules and its declared dependencies are compiled in, and
> `use name::{item}` imports an exported task. A project needs `kind` and, for
> an app, `entry`, which both `freak init` and `hangar init` write. See
> [Hangar & packages](hangar.html).

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
