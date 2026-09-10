# Hangar & packages

> Hangar manages dependencies. V3 cannot consume them. This page explains the gap and what to do instead.

Hangar is FREAK's package manager, shipping as `freak hangar <cmd>` and as a
standalone `hangar` binary. It initialises projects, edits manifests, resolves
semver constraints, downloads packages and publishes them.

> [!warn]
> **An installed package is not visible to the compiler.** `freak build` never
> reads `hangar_modules/` and never reads `[dependencies]`. A `use pkg::{…}`
> line is rewritten to a comment before parsing, so nothing is imported and the
> first call into the package fails with `unknown callable`.
>
> Hangar today is a manifest and download tool. The link step that would make a
> dependency usable does not exist in V3.

Verified against the shipping compiler:

```text
$ freak hangar init demo
  INITIALIZED demo
    hangar.toml
    src/main.fk
    hangar_modules/

$ cat hangar_modules/greeter/greeter.fk
task greeter_hello(name: word) -> word { give back "hello, " + name }

$ cat src/main.fk
use greeter::{greeter_hello}
task main() -> void { say greeter_hello("Takeru") }

$ freak build src/main.fk
type error: unknown callable 'greeter_hello' (line 4)
  X BUILD FAILED
```

## What does get linked

`cli_load_std` in `src/cli/build.fk` is the whole of the build's source
resolution. It concatenates a fixed list ahead of your file:

| Source | When |
|---|---|
| `std/math.fk`, `std/string.fk`, `std/convert.fk`, `std/algorithm.fk`, `std/json.fk`, `std/version.fk` | Always |
| `std/runtime.fk`, `std/http.fk` | Always, LLVM backend only |
| `std/math3d.fk` | The source text contains `use std::math3d` |
| `std/zip.fk` | The source text contains `use std::zip` |
| `std/ui/window.fk` | The source text contains `use std::ui` |
| `packages/cockpit/src/*.fk` | The source text contains `use cockpit` |

Those four `use` forms are **textual triggers**, not imports — the build greps
your source for the string and links a hard-coded path. Everything else already
in that list is in scope whether you write `use` or not.

> [!note]
> The `cockpit` trigger resolves `packages/cockpit/src`, a **repository-relative
> path**. It only works when you build from inside a Freak-lang checkout, not
> from an installed toolchain — and it is the only package-shaped thing the
> build can link at all.

## Commands

All of these work. What they cannot do is make a package compile.

| Command | Effect |
|---|---|
| `hangar init [name]` | Scaffold `hangar.toml`, `src/main.fk`, `hangar_modules/` |
| `hangar add <name> [constraint]` | Add a dependency to the manifest |
| `hangar add <name> <repo> [version]` | Add a dependency from a git repo |
| `hangar remove <name>` | Remove it |
| `hangar install` | Download all dependencies into `hangar_modules/` |
| `hangar install freak` | Install or update the FREAK toolchain itself |
| `hangar update [package]` | Re-resolve and update `hangar.lock` |
| `hangar outdated` | Report packages behind their constraint |
| `hangar version` | Print the project version |
| `hangar version patch\|minor\|major` | Bump it in the manifest |
| `hangar audit` / `hangar audit --fix` | Verify or repair package integrity |
| `hangar login` | Authenticate with the registry |
| `hangar publish [--dry-run]` | Publish to the registry |

`hangar search` from the specification does not exist in this build.

## hangar.toml

What `hangar init` actually writes:

```toml
[project]
name = "demo"
version = "0.1.0"
```

And after `hangar add muvluv "^2.0"`:

```toml
[project]
name = "demo"
version = "0.1.0"

[dependencies]
muvluv = "^2.0"
```

> [!warn]
> The specification's §6.2 shows a different, larger manifest — `[unit]` rather
> than `[project]`, plus `author`, `entry`, `edition`, a `[build]` table with
> `mode`/`target`/`voice`, and `[profile.*]` sections. None of that is written
> or read by the shipping tool. Only `[project]` and `[dependencies]` matter.

Version constraints are resolved by `std/version.fk`, which is real, working
semver: `ver_satisfies("1.4.2", "^1.4")` is `true`. You can call that machinery
directly — see [Standard library](stdlib.html#stdversion).

`hangar.lock` records resolved versions.

## Reusing code, for real

Because the compiler takes exactly one file and everything lands in one flat
global namespace, a "library" is just source you concatenate ahead of your
program:

```sh
cat lib/text.fk src/app.fk > build/combined.fk
freak build build/combined.fk
```

Verified working, including against a file downloaded into `hangar_modules/`:

```sh
cat hangar_modules/greeter/greeter.fk src/app.fk > combined.fk
freak build combined.fk     # BUILD SUCCESSFUL
```

Order matters only for `shape` declarations: a shape must be registered before
a constructor for it is parsed, so put library shapes first. Tasks can be in
any order — every task is indexed before any body is checked.

This is exactly how the compiler builds itself. The eight V3 sources and the
CLI sources are `cat`-ed into one translation unit; the file split is a
maintenance convention, not a module system. See
[Getting started](getting-started.html#build-the-compiler-from-source).

## The concatenated pattern

{{example:module_pattern}}

## Conventions that make it survivable

One flat namespace across your code, every linked `std/` file, and every
library you concatenate. Collisions are silent until they are a redefinition
error, so:

- **Prefix everything a library exports.** `text_count_words`, not
  `count_words`. The standard library already does this — `string_*`, `std_*`,
  `ver_*`, `json_*`, `array_*`.
- **Watch for `std/` collisions.** Defining your own `array_find` or
  `string_trim` clashes with a task the build already linked.
- **Remember reserved words are case-insensitive.** A library cannot export
  anything named `Result`, `Max`, `Route` or `Check` in any casing. See
  [reserved words](language-basics.html#reserved-words-are-case-insensitive).
- **Keep a build script.** A one-line `cat` in a `.sh`/`.bat` is your build
  system. Regenerate the combined file every time.

## A Makefile-shaped example

```sh
#!/bin/sh
set -e
mkdir -p build
cat lib/text.fk lib/report.fk src/app.fk > build/combined.fk
freak build build/combined.fk
mv build/combined.exe build/app.exe
```

Line numbers in diagnostics refer to the combined file. The compiler maintains
a source map for the std prefix it adds itself, but it cannot know about your
`cat`, so keep the concatenation order stable if you want stable offsets.

## What ships when this is fixed

Real imports need the module system from §6 and §17 of the specification —
`launch` visibility, `use module::{names}`, `launch(package)`, glob imports,
namespace collision rules. All of that is V4 work; `launch` does not currently
parse at all. Until then, Hangar is useful for versioning and distributing
source, and `cat` is the linker.
