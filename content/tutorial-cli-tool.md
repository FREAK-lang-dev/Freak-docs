# Tutorial 2: A command-line tool

> Read arguments, read a file, count what is in it, and print a coloured report that respects `NO_COLOR`. About 25 minutes.

By the end you will have a small `wc`-style tool. Along the way: the argument
API, file I/O without `result<T,E>`, hand-rolled text scanning, ANSI colour,
and exit codes.

Start from [Tutorial 1](tutorial-first-program.html) if you have not written
any FREAK yet.

## Step 1 — Arguments

There is no `process::args()` returning a list. V3 rejects it deliberately
rather than handing you the runtime's raw `argv` as a fake handle. Use the
indexed pair instead:

```fk
task main() -> void {
    say word_from_int(process::args_count())

    pilot mut i: int = 0
    repeat process::args_count() times {
        say "arg {i}: " + process::arg(i)
        i += 1
    }
}
```

Argument 0 is the executable path, so the first real argument is index 1.

That loop is the standard V3 iteration idiom: a counted `repeat` plus a manual
index. There is no `for each`.

## Step 2 — Reading a file

`fs::*` are builtins. There is no `result<T,E>` anywhere in V3, so failures
come back as sentinel values — an empty `word`, or `false`:

```fk
task main() -> void {
    pilot path: word = "notes.txt"

    if not fs::exists(path) {
        say "no such file: " + path
        process::exit(1)
    }

    pilot text: word = fs::read(path)
    say word_from_int(text.length())
}
```

`process::exit(code)` ends the program immediately. Check `fs::exists` before
reading — an unreadable file and an empty file both come back as `""`.

> [!note]
> `fs::delete` returns `true` when the file is gone, whether this call removed
> it or it was already absent. It only returns `false` when the path could not
> be unlinked.

## Step 3 — Making the tool self-contained

So it always has something to work on, write a sample when no argument is
given:

```fk
task sample_path() -> word {
    pilot path: word = "sample.txt"
    fs::write(path, "the beta do not negotiate\nhumanity answers with steel\n")
    give back path
}

task target_path() -> word {
    if process::args_count() > 1 {
        give back process::arg(1)
    }
    give back sample_path()
}
```

## Step 4 — Counting

No regex, no `.split()` into a list. Walk the characters:

```fk
task count_words(text: word) -> int {
    pilot mut total: int = 0
    pilot mut in_word: bool = false
    pilot mut i: int = 0

    repeat text.length() times {
        pilot c: word = text.char_at(i)
        pilot blank: bool = c == " " or c == "\n" or c == "\t" or c == "\r"
        if blank {
            in_word = false
        } else {
            if not in_word { total += 1 }
            in_word = true
        }
        i += 1
    }
    give back total
}
```

`.char_at(i)` returns a one-character `word` — there is no `char` type. Note
`and` / `or` take `bool` only; there is no truthiness, so `if count` is an
error where `if count > 0` is fine.

Counting lines is the same shape of loop, with one adjustment so a trailing
newline does not invent an extra line:

```fk
task count_lines(text: word) -> int {
    if text.length() == 0 { give back 0 }
    pilot mut total: int = 1
    pilot mut i: int = 0
    repeat text.length() times {
        if text.char_at(i) == "\n" { total += 1 }
        i += 1
    }
    if text.char_at(text.length() - 1) == "\n" { total -= 1 }
    give back total
}
```

## Step 5 — Colour

There is no colour library. You build ANSI escape sequences as `word` values.
`\x1b` is the ESC byte:

```fk
pilot C_RESET = "\x1b[0m"
pilot C_BOLD  = "\x1b[1m"
pilot C_RED   = "\x1b[1;31m"
pilot C_GREEN = "\x1b[32m"
```

Then concatenate:

```fk
say C_RED + "error" + C_RESET + ": no such file"
```

Windows consoles are switched into ANSI mode automatically — the runtime calls
`freak_enable_ansi()` at the start of every FREAK program, on both backends.
You do not need to do anything platform-specific.

The full code tables — attributes, 16 colours, backgrounds, 256-colour,
truecolour, cursor control — are in [Coloured output](console.html).

## Step 6 — Respecting NO_COLOR

Nothing does this for you. The trick the CLI uses is to make the constants
`pilot mut` and blank them, so every call site keeps working unchanged:

```fk
pilot mut C_RESET = "\x1b[0m"
pilot mut C_RED   = "\x1b[1;31m"

task configure_output() -> void {
    if process::env("NO_COLOR") != "" {
        C_RESET = ""
        C_RED = ""
    }
}
```

Call `configure_output()` first thing in `main`.

> [!warn]
> There is no TTY detection in V3, so your program cannot tell whether stdout
> is a pipe. Escapes are emitted even when output is redirected. Honouring
> `NO_COLOR` is the only politeness available.

## The finished tool

{{example:tut_cli}}

Run it against your own file:

```sh
freak run wordcount.fk README.md
NO_COLOR=1 freak run wordcount.fk README.md
```

## What you would reach for next, and cannot

Worth knowing before you plan a bigger tool:

| You might want | V3 reality |
|---|---|
| `result<T, E>` and `?` | None. Sentinels and `process::exit` |
| `.split(",")` into a list | `string_split` returns an encoded word, not a list. Walk characters |
| A map for counting words | No `Map<K,V>`. Two parallel collections and `array_find` |
| `for each line in lines` | Counted `repeat` plus an index |
| Writing to stderr | No stderr writer. Everything goes to stdout |
| A `-o` output flag | Output path is fixed to the source basename |

See [Not in V3](not-in-v3.html) for substitutes.
