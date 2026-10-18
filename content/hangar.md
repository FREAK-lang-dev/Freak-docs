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

> [!note]
> `hangar init` writes `kind = "app"` and `entry = "src/main.fk"` since 0.15.1.
> A project made by an older `hangar init`, without those keys, still installs,
> but `freak build` refuses it: *"project.kind must be 'app' or 'lib'"*. Add the
> two keys to fix it.

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
| `std/test.fk` | The source text contains `use std::test` |
| `std/json_document.fk` | The source text contains `use std::json_document` |
| `std/http_server.fk` | The source text contains `use std::http_server` |

Those six `use` forms are **textual triggers**, not imports — the build greps
your source for the string and links a hard-coded path. Everything else already
in that list is in scope whether you write `use` or not. Packages are not part
of this list: they come in through `[dependencies]` and `use name::{item}`, as
described above.

## Commands

These are the `hangar` subcommands.

| Command | Effect |
|---|---|
| `hangar init [name]` | Scaffold `hangar.toml`, `src/main.fk`, `hangar_modules/` |
| `hangar add <name> [constraint]` | Add a registry dependency (latest version if no constraint) |
| `hangar add <name> --path <dir>` | Add a local path dependency |
| `hangar add <name> <repo> [version]` | Add a dependency from a git repo |
| `hangar remove <name>` | Remove it |
| `hangar install` | Download all dependencies into `hangar_modules/` |
| `hangar install freak` | Install or update the FREAK toolchain itself |
| `hangar update [package]` | Re-resolve and update `hangar.lock` |
| `hangar outdated` | Report packages behind their constraint |
| `hangar version` | Print the project version |
| `hangar version patch\|minor\|major` | Bump it in the manifest |
| `hangar audit` / `hangar audit --fix` | Verify or repair package integrity |
| `hangar auth login` / `hangar auth status` / `hangar auth logout` | Sign in, see who you are, sign out (`hangar login` / `hangar logout` are shortcuts) |
| `hangar publish [--dry-run]` | Publish to the registry |

`hangar search` from the specification does not exist in this build.

> [!warn]
> On Windows, `hangar add <name> <git-url>` fails in 0.15.1 while cleaning up
> its temporary clone (*"could not safely remove complete owned temporary
> directory"*), because Git's read-only object files can't be deleted. Clone
> the repository yourself and use `hangar add <name> --path <clone>` until the
> fix ships.

### Signing in

`hangar auth login` runs a device flow: it prints a short one-time code, opens
the registry in your browser, and waits while you approve it there. What it
saves is a session tied to your account, stored in your user config directory
with owner-only permissions. `hangar auth status` says who you are signed in
as (*"Not signed in to https://hangar.freaklang.dev/api/v1. Run: hangar auth
login"* when you aren't), and `hangar auth logout` revokes the session.

Publishing is tied to an account: the first publish of a name claims it, and
nobody else can ship that name afterwards. `hangar publish --dry-run` shows
what would be uploaded. The registry defaults to
`https://hangar.freaklang.dev/api/v1`; set `HANGAR_REGISTRY` to use another.

> [!note]
> Tokens saved by 0.15.0's `hangar login` don't record which registry they
> belong to, so Hangar only sends them to the default registry. Sign in again
> to use another one.

### Registry dependencies

```toml
[dependencies]
cockpit = "^0.1.0"
```

`hangar install` resolves this against the registry, pins it in `hangar.lock`
by archive SHA-256, and caches the archive so later builds work offline. A
package with dashes in its name is imported with underscores:
`cockpit-extras` becomes `use cockpit_extras::{...}`.

Caret ranges on `0.x` versions follow Cargo and npm since 0.15.1: `^0.1.0`
means `>=0.1.0, <0.2.0`, and `^0.0.3` means exactly `0.0.3`. A constraint
nothing satisfies is refused with *"no published version of NAME satisfies
CONSTRAINT"*. If you want newer minor versions of a `0.x` package, write
`>=0.1.0` instead, knowing that it also accepts `1.0.0` and every later major
version.

## hangar.toml

`freak init` writes the manifest shown at the top of this page. `hangar init`
writes a smaller one, in dotted-key form:

```toml
project.entry = "src/main.fk"
project.kind = "app"
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
