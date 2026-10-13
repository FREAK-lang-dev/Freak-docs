# Hangar & packages

> A project is a `hangar.toml` and the sources it names. This page covers what the compiler reads from that manifest, how one project uses another, and what is still missing.

Hangar is FREAK's package manager, shipping as `freak hangar <cmd>` and as a
standalone `hangar` binary. As of 0.15 the compiler reads the project manifest
too: `freak build`, `freak run` and `freak test` work on a whole project, and a
project can import tasks from another one.

## A project

`freak init NAME` creates one; `--template=cli`, `lib` or `http` chooses the
starting layout. Its manifest looks like this:

```toml
[project]
name = "sortie"
version = "0.1.0"
kind = "app"
entry = "src/main.fk"

[modules]
greet = "src/greet.fk"

[exports]
greet = "greet::greet"

[tests]
greeting = "tests/greeting_test.fk"

[dependencies]
```

| Table | What it is for |
|---|---|
| `[project]` | `kind` must be `app` or `lib`. An app names its `entry` file |
| `[modules]` | The project's other source files, each under a module name |
| `[exports]` | The tasks another project may import, written `module::task` |
| `[tests]` | The programs `freak test` builds and runs |
| `[dependencies]` | The projects this one may import from |

Inside the project directory, `freak build` and `freak run` need no file name.
A file imports from one of the project's own modules with `use self::`:

```fk
use self::greet::{greet}

task main() {
    say greet("sortie")
}
```

## Using another project

A library lists what it offers under `[exports]`. A project that wants it names
it under `[dependencies]`, and imports the exported task through that name:

```toml
[dependencies]
demo = { path = "../.." }
```

```fk
use demo::{greet}

task main() {
    say greet("consumer")
}
```

Verified against the shipping compiler, in the consumer project that
`freak init greeter --template=lib` generates under `examples/consumer`:

```text
$ freak run
Hello, consumer!
```

An import is checked, not skipped:

| You write | The compiler answers |
|---|---|
| `use greeter::{hello}` with no `greeter` dependency declared | `undeclared direct dependency 'greeter'` |
| `use demo::{nothing}` | `missing public export 'nothing'` |
| `use demo::*` | `import requires {symbol, symbol as alias}` |
| `use std::nonexistent` | `unsupported standard module 'nonexistent'` |

> [!note]
> Only a path dependency was run for this page. The 0.15.0 release notes say
> build, run and test also consume Git dependencies pinned in `hangar.lock`.

> [!warn]
> `freak hangar init` still writes the older, smaller manifest, without `kind`
> or `entry`. `freak build` refuses a project like that: *"project.kind must be
> 'app' or 'lib'"*. Create projects with `freak init`, or add the two keys.

## What does get linked

`cli_load_std` in `src/cli/build.fk` is how the standard library reaches your
program. It concatenates a fixed list ahead of your source:

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

These are the `hangar` subcommands. One no longer does what its row says: a
registry constraint such as `hangar add muvluv "^2.0"` is refused in 0.15.0
with *"Registry package sources are unavailable; specify an explicit Git
source"*.

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

### Signing in

In 0.15.0, `hangar login` stores a registry token in
`~/.hangar/credentials` — a string an administrator mints and you paste in.
`hangar publish` sends it as a bearer token.

> [!note]
> This is being replaced. On `main`, tokens are gone: `hangar auth login` runs
> a device flow instead — it prints a short one-time code, opens the registry
> in your browser, and waits while you approve it there. What lands in
> `~/.hangar/credentials` is then a session tied to your account, which you can
> revoke yourself with `hangar auth logout`. `hangar auth status` says who you
> are signed in as, and `hangar login` still works as an alias. Publishing is
> tied to an account too: the first publish of a name claims it, and nobody
> else can ship that name afterwards. Not in 0.15.0 — this page follows the
> shipping compiler, and will change when a release carries it.

## hangar.toml

`freak init` writes the manifest shown at the top of this page. `hangar init`
writes a smaller one, in dotted-key form:

```toml
project.name = "demo"
project.version = "0.1.0"
```

> [!warn]
> The specification's §6.2 shows a different manifest — `[unit]` rather than
> `[project]`, plus `edition`, a `[build]` table with `mode`/`target`/`voice`,
> and `[profile.*]` sections. None of that is written or read by the shipping
> tools. They use the tables listed under [A project](#a-project).

Version constraints are resolved by `std/version.fk`, which is real, working
semver: `ver_satisfies("1.4.2", "^1.4")` is `true`. You can call that machinery
directly — see [Standard library](stdlib.html#stdversion).

`hangar.lock` records resolved versions.

## Single files

A file built on its own, outside any project, is still one translation unit in
one flat global namespace. There a "library" is just source you concatenate
ahead of your program:

```sh
cat lib/text.fk src/app.fk > build/combined.fk
freak build build/combined.fk
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

A single file shares one flat namespace with every linked `std/` file and
every library you concatenate. Two tasks of your own with one name are an
error, and a task named like a `std/` task quietly replaces it, so:

- **Prefix everything a library exports.** `text_count_words`, not
  `count_words`. The standard library already does this — `string_*`, `std_*`,
  `ver_*`, `json_*`, `array_*`.
- **Watch for `std/` collisions.** Defining your own `array_find` or
  `string_trim` replaces the standard one for your whole program. A compiler
  builtin such as `ask` cannot be redefined at all.
- **Remember reserved words are case-insensitive.** A library cannot export
  anything named `Result`, `Max`, `Route` or `Check` in any casing. See
  [reserved words](language-basics.html#reserved-words-are-case-insensitive).
- **Keep a build script.** Outside a project, a one-line `cat` in a
  `.sh`/`.bat` is your build system. Regenerate the combined file every time.

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

## What is still missing

The specification's module system (§6 and §17) goes further than the manifest
does. `launch` visibility does not parse, there is no `launch(package)`, and a
glob import is refused. `[exports]` is the only visibility there is: it limits
what another project can import. Inside one project, any module can import any
task of another with `use self::`.
