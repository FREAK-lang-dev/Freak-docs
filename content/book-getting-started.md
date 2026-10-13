# Getting started

> Install the compiler, check that it works, write and run a first program, and create a first project.

This chapter gets you from nothing to a running program. It covers:

- installing FREAK on Linux, macOS and Windows
- checking the installation with `freak doctor`
- writing a program that prints `Hello, FREAK!`
- the difference between running, building and checking a program
- creating a project with `freak init`

## Installing FREAK

FREAK is installed by a script that downloads the latest release, checks it,
and unpacks it into your home directory. FREAK itself is not installed
system-wide and needs no administrator rights.

On Linux, or on a Mac with Apple silicon, run this in a terminal:

```sh
curl -fsSL https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.sh | bash
```

The installer does not support Macs with Intel processors. On Windows, run
this in PowerShell:

```sh
irm https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.ps1 | iex
```

On Linux the installer prints something close to this, with your own home
directory in place of `/home/you`:

```text
> Detected platform: linux-x64
> Clang is available
> Fetching latest release...
> Release: v0.14.2
> Downloading freak-linux-x64.tar.gz...
> Verified SHA-256 for freak-linux-x64.tar.gz
> Extracting distribution...
> Added /home/you/.freak/bin to PATH in /home/you/.bashrc
>
> FREAK v0.14.2 installed successfully!
>   Compiler: /home/you/.freak/bin/freak
>   Hangar:   /home/you/.freak/bin/hangar
>   Runtime:  /home/you/.freak/runtime/
>   Std lib:  /home/you/.freak/std/
> Restart your shell or run:
>   export PATH="/home/you/.freak/bin:$PATH"
> Then verify the complete toolchain with: freak doctor
> "It was always going to end this way."
```

Do what the lines before the closing quotation say: open a new terminal, or
run the `export` line in the one you have, so that the `freak` command can be
found.

### What was installed

Everything lives in one directory, `~/.freak`. On Windows the installer uses
`%APPDATA%\freak` instead.

| Path | What it is |
|---|---|
| `bin/freak` | The compiler and its command-line tools |
| `bin/hangar` | The package manager, also reachable as `freak hangar` |
| `runtime/` | C source that is compiled into every program you build |
| `std/` | The standard library, written in FREAK |

The installer also appends a short block, a comment and one `export` line, to
the shell startup files it finds, so that `~/.freak/bin` is on your `PATH`. It
looks for `.zshrc` and `.bashrc`, and for `.bash_profile` when there is no
`.bashrc`. It does not create a file that is missing. If you have none of
them, as on a new macOS account, nothing is added and the `Added ... to PATH`
line does not appear. In that case put the `export` line in your shell's
startup file yourself.

On Linux and macOS, that block and the `~/.freak` directory are the whole
installation. To remove FREAK, delete both. On Windows the installer changes
your user `PATH` and, when it finds Clang, sets a user variable named
`FREAK_CLANG`.

### FREAK needs Clang

The FREAK compiler does not produce machine code by itself. It translates your
program into LLVM IR, a lower-level form, and then runs Clang to turn that into
a native program. Clang therefore has to be installed.

The installer checks for it. In the output above it reported `Clang is
available`. If Clang is missing, the installer still installs FREAK, warns you
that programs cannot be built without Clang, and leaves your system's packages
alone. You can then install Clang with your system's package manager, or ask
the FREAK installer to do it:

```sh
curl -fsSL https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.sh | bash -s -- --with-deps
```

On Windows, set `$env:FREAK_INSTALL_DEPS = "1"` before running the PowerShell
line, and the installer fetches a self-contained toolchain.

## Checking the installation

Ask the compiler for its version:

```sh
freak --version
```

```text
freak 0.14.2 (Maverick)
```

If your shell answers `command not found`, the `PATH` change has not taken
effect yet. Open a new terminal and try again. If it still fails, the
installer found no startup file to change, and you need to add the `export`
line by hand.

A version number only proves the `freak` program starts. To check that the
whole toolchain works, run the doctor:

```sh
freak doctor
```

The doctor makes five checks and reports each one. The end of its output,
shortened here, looks like this:

```text
  [3/5] Checking runtime
        ✓ /home/you/.freak/runtime
        ✓ source runtime fallback available
        ✓ LLVM runtime available

  [4/5] Checking standard library
        ✓ 11/11 modules in /home/you/.freak/std

  [5/5] Checking compile pipeline
        ✓ compile, link, and execution work

  ╭──────────────────────────────────────────────────╮
  │  ✨ ALL SYSTEMS GO  5/5 passed
  ├──────────────────────────────────────────────────┤
  │   Get started:  freak build hello.fk
  ╰──────────────────────────────────────────────────╯
```

The five checks are Clang, the optional LLD linker, the runtime files, the
standard library, and a complete trial run: the doctor compiles a small FREAK
program, links it, and executes it. If that last check passes, your
installation can build programs.

If a check fails, `freak doctor --fix` tries to repair it, by installing
missing dependencies or restoring missing runtime and library files. `freak
doctor --json` prints the same report in a form that scripts and editors can
read.

### Updating

When a new release comes out, `freak upgrade` downloads and installs it in
place of the one you have.

### Editor support

Syntax highlighting and snippets for VS Code and Zed are maintained in the
[freak-editors](https://github.com/FREAK-lang-dev/freak-editors) repository.
They colour your code and complete common constructs. Checking by the compiler
itself is not part of them yet; to find type errors you run the compiler.

## Hello, FREAK

Make a directory for your programs and move into it:

```sh
mkdir freak-book
cd freak-book
```

Create a file named `hello.fk`. FREAK source files always end in `.fk`. Put
these lines in it:

{{example:book_hello|source}}

Save the file and run it:

```sh
freak run hello.fk
```

The compiler reports what it is doing, then your program runs:

```text
  ╭─────────────────────────────────────────────╮
  │  ⚡ FREAK  hello.fk
  │    Backend: LLVM IR  Profile: O2
  ╰─────────────────────────────────────────────╯

Source length: 51423
  ✓  Lexing (41ms)
  ✓  Parsing (18ms)
  ✓  Type checking (10ms)
  ✓  Emit LLVM IR (617ms)
  ⚙  Compiling native binary...
  ✓  Native binary (2521ms)

  ╭─────────────────────────────────────────────╮
  │  ✨ BUILD SUCCESSFUL
  ├─────────────────────────────────────────────┤
  │   Binary: hello
  │   Time:   3243ms
  ╰─────────────────────────────────────────────╯

  "The only ones who should kill are those prepared to be killed."

  ╭─────────────────────────────────────────────╮
  │  ▸ RUNNING  hello
  ╰─────────────────────────────────────────────╯

Hello, FREAK!

  ✓ DONE (3ms)
```

`Hello, FREAK!` is your program's output. Everything around it comes from the
compiler. The quotation changes from build to build; yours will differ.

You have written, compiled and run a FREAK program.

### Anatomy of the program

Look at the program again, one piece at a time.

The first line is a comment. Two dashes start a comment, and it runs to the end
of the line. The compiler ignores it.

The second line begins a task:

```fk
task main() {
```

`task` declares a task, which is FREAK's word for a function: a named piece of
work. This one is named `main`. The empty parentheses mean it takes no inputs.
The opening brace starts its body, and the closing brace on the last line ends
it.

`main` is special. It is the entry point: when the program starts, it runs the
task called `main`, and when `main` finishes, the program ends.

Inside the body is one statement:

```fk
    say "Hello, FREAK!"
```

`say` prints a value followed by a new line. Here the value is a piece of text
in double quotes. FREAK calls a piece of text a *word*, whatever its length.
`say` is part of the language. There is nothing to import.

Notice what is absent. There is no semicolon at the end of the statement: FREAK
code does not need them. A semicolon is allowed, and lets you put two short
statements on one line, but the convention is one statement per line. The body is indented by
four spaces, which is the convention in FREAK code, but indentation is for
readers. The compiler finds the structure from the braces.

### Reading the build report

The lines between the first two boxes are the stages your program went
through.

| Stage | What happens |
|---|---|
| Lexing | The text is cut into tokens: names, numbers, words, punctuation |
| Parsing | The tokens are arranged into the structure of the program |
| Type checking | Every value is checked to have the type its use requires |
| Emit LLVM IR | The checked program is written out in LLVM's intermediate form |
| Native binary | Clang turns that into a program your machine can run |

Look at the line `Source length: 51423`. Your file is 90 characters long.
Before compiling, `freak run` places the standard library in front of your
program and compiles the two together as one text. That is why standard-library
tasks are available without importing anything, and it has consequences for how
names work that Chapter 4 and Part IV come back to.

### When something is wrong

Compilers are met mostly through their complaints, so make some mistakes on
purpose. Delete the closing quote:

{{diagnostic:book_unterminated_word}}

The compiler names the problem, points at the place with a caret, and suggests
the fix. When you get several errors, fix the first one and build again: later
errors are often consequences of the first.

Now misspell `say`:

{{diagnostic:book_misspelled_say}}

The compiler does not know `sya`, so it takes it for the name of a value you
never created. "Binding" is the compiler's word for a named value. You will
see `unknown binding` whenever the name of a value is misspelled, and `unknown
callable` when it is the name of a task.

The entry point is the task named `main`, in lowercase. Name it anything else
and the program has nowhere to start, so it does not build:

{{diagnostic:book_no_entry}}

The message mentions a second possibility, a file of statements with no
`main` at all. That is a script, and Chapter 4 shows how it runs.

## Building, running and checking

`freak run` did two things: it built a program and then started it. You can do
them separately.

```sh
freak build hello.fk
```

This stops after the build. Look at the directory afterwards:

```text
hello
hello.fk
hello.fk.ll
```

`hello` is the program. It is an ordinary native executable, and you can run it
directly:

```sh
./hello
```

```text
Hello, FREAK!
```

On Windows the file is named `hello.exe` and you run it as `.\hello.exe`.

The program does not need FREAK or Clang to run. You can copy `hello` to
another machine with the same operating system and processor, and it runs
there using only the system libraries that every program on that machine
uses.

`hello.fk.ll` is the LLVM IR the compiler produced on the way. It is safe to
delete, and interesting to read once you know the language. After `freak run`
you will also find `hello.freak-run-cache`. It lets a second `freak run` of an
unchanged file skip the build and start the program at once.

The third command neither builds nor runs:

```sh
freak check hello.fk
```

```text
  ⚙ CHECKING hello.fk

Source length: 90
  ✓  Lexing (0ms)
  ✓  Parsing (0ms)
  ✓  Type checking (0ms)

  ✨ PASSED -- no type errors found
```

`check` runs the first three stages and stops. It is fast, because it never
calls Clang. Compare the source length with the earlier one: `check` looks at
your 90 characters alone, without the standard library in front of them.

> [!warn]
> Because `freak check` does not load the standard library, it rejects a
> correct program that uses a standard-library task, with `unknown callable`.
> For such programs, use `freak build` to find errors. Every listing in Part I
> uses only what is built into the compiler, so `check` works on all of them.

| Command | Builds | Runs | Standard library |
|---|---|---|---|
| `freak run hello.fk` | yes | yes | loaded |
| `freak build hello.fk` | yes | no | loaded |
| `freak check hello.fk` | no | no | not loaded |

## Comments

You have seen one comment already. The rules are short.

{{example:book_comments}}

A comment starts at `--` and ends at the end of the line. It can have a line to
itself or follow code. There is no form of comment that spans several lines;
write `--` at the start of each one. Putting `--` in front of a line of code is
the usual way to switch it off for a moment.

## A first project

A single file is fine for learning. A program you intend to keep deserves a
directory of its own and a file that describes it. `freak init` creates both:

```sh
freak init sortie
```

```text
Created project sortie
```

The project is called `sortie`, a mission flown by a single unit. The command
made a directory with this in it:

```text
sortie/
  hangar.toml
  README.md
  LICENSE
  src/
    main.fk
    greet.fk
  tests/
    greeting_test.fk
```

`hangar.toml` is the project's description:

```toml
[project]
name = "sortie"
version = "0.1.0"
kind = "app"
entry = "src/main.fk"
readme = "README.md"
license_file = "LICENSE"

[modules]
greet = "src/greet.fk"

[exports]
greet = "greet::greet"

[tests]
greeting = "tests/greeting_test.fk"

[dependencies]
```

It records the project's name and version, which file the program starts in,
the other source files it is made of, and its tests. The empty
`[dependencies]` section is for packages the project uses. The file belongs to
Hangar, FREAK's package manager, which is why it carries that name.

`src/main.fk` is the starting program, and `src/greet.fk` holds one task it
uses. The program says hello to `sortie`, or to a name you give it. You do not
need to follow every line of it yet: Chapter 4 covers tasks, and Part IV
covers splitting a program across files.

Inside the project directory, `freak run` needs no file name, because the
manifest names the entry. Anything after `--` is passed to the program:

```sh
cd sortie
freak run
freak run -- Ada
```

```text
Hello, sortie!
Hello, Ada!
```

`freak test` builds and runs the tests the manifest lists:

```text
  run: passed (11 ms), exit 0
1 passed, 0 failed (1 tests)
```

## In V4

V4 has no installer and no release. To try it you need a copy of the compiler
repository and Python, and you build programs with a script from that
repository:

```sh
python src/compiler/v4/build_v4.py hello.fk -o hello
./hello
```

At the commit this book is pinned to, V4 builds and runs this version of the
first program:

{{v4:hello}}

It is not quite the program you wrote for V3. The differences are the first
concrete things to know about V4.

**A task must state what it gives back.** `-> int` after the parentheses says
that `main` gives back a whole number, and `give back 0` does it. That number
becomes the program's exit code, the value the operating system receives when
the program ends. Zero means success. V4 also accepts `-> void`, meaning
nothing is given back. The form with no arrow at all, which V3 accepts, is
turned away. This is true of every task at this commit, and `main` is where
you meet it first:

{{v4:main_without_type}}

A line beginning `v4-native-contract-error=` comes from the last stage of V4,
the one that generates code. It is how that stage says it has met something it
cannot build yet. The message is worded as "not yet supported": it marks a
gap in this commit, not a rule of the language.

**Statements must be inside a task.** The specification says that only
declarations may appear at the top level of a file, and V4 enforces it. A
script, a file of statements with no `main`, does not build in V4:

{{v4:toplevel_statement}}

V4's diagnostics look different from V3's. The fields are separated by bars:
`2` is the severity, `0@68:88` is file 0 from position 68 to position 88, then
come the message and a detail or hint. V4 is built to hand these to an editor,
which turns the positions into underlines. A readable command-line presentation
is still to come.

**`say` accepts a literal word only.** This commit can print text written
directly in the program, and nothing else yet. The listing creates a named
value with `pilot`, which Chapter 2 introduces, and tries to print it:

{{v4:say_needs_literal}}

That limits what the V4 listings in the next few chapters can show on screen.
Most of them report their result through the exit code instead.

**A semicolon is accepted**, as it is in V3 and in the specification:

{{v4:semicolon}}

## Summary

You installed FREAK and confirmed the installation with `freak doctor`. You
wrote a program with one task, `main`, containing one statement, `say`, and saw
that a FREAK program is built into a native executable by way of LLVM and
Clang. You know three commands: `freak run` to build and run, `freak build` to
build only, and `freak check` to look for errors quickly without the standard
library. You created a project with `freak init`.

You also met V4 for the first time, and saw that it insists on tasks with a
declared result and on keeping statements inside tasks.

[Chapter 2](book-guessing-game.html) puts these pieces to work in a real
program: a number-guessing game that reads what you type.
