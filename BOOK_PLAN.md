# The Freak Book: plan

The outline, the rules the book is written to, and what is done.

Status on 2026-10-05: Part I is written (introduction and five chapters).
Everything else below is outline.

## What the book is

A tutorial read in order, in the manner of *The Rust Programming Language*:
it starts with installing the compiler and ends inside the compilers. It is
not a second reference. The reference pages in this repository stay organised
by topic; the book is organised by what a learner needs next.

One book covers both compilers:

- The body of every chapter teaches **V3**, the compiler people can install.
- **In V4** boxes and sections state where V4 differs, checked against one
  pinned V4 commit.
- **Planned** boxes describe what the specification promises and no compiler
  runs.

## Rules the book is written to

1. **A statement that something works is backed by a program that ran.**
   Listings are `{{example:name}}` cards from `examples/`, built and run by the
   pinned V3 release with reviewed output.
2. **A statement that something is rejected is backed by the real diagnostic.**
   `{{diagnostic:name}}` cards come from `diagnostics/v3/`; the release must
   refuse the program and its message must contain the reviewed text.
3. **A statement about V4 is backed by the pinned snapshot.** `{{v4:name}}`
   cards come from `examples-v4/`, checked at the commit in `v4-snapshot.txt`.
   A V4 note describes that commit and nothing newer.
4. **Planned is never mixed with real.** Specification-only material goes in
   `> [!planned]` boxes, or in Part VII, which is planned from end to end.
5. **Surprising behaviour is shown, not hidden.** If V3 or V4 does something a
   reader would not expect, the chapter says so and shows it.
6. **Fenced `fk` fragments are for shape only.** The renderer labels them
   unverified. Anything that claims to run becomes an example.
7. **Lore below tech.** The vocabulary is FREAK's and the example names are
   pilots and squadrons, but no joke stands in front of an instruction.

### The shape of a chapter

- A title, a one-sentence lede, and a short list of what the chapter covers.
- Sections that each introduce one idea, with a listing, then the rule, then
  the mistake and its diagnostic.
- `## In V4`: differences at the pinned commit, each with a V4 card.
- `## Planned`: specification features that belong to the topic.
- `## Summary`, ending with a link to the next chapter.

### Voice

Second person, plain sentences, present tense. Explain the rule, then show it.
Name a term once in italics when it is introduced and use it consistently
afterwards. No semicolon-style asides, no rhetorical questions, no
exclamation marks outside program output.

### Example conventions

- Example files are prefixed `book_`; V4 examples are unprefixed in their own
  directory.
- `task main() { ... }` with no return type in V3 listings; `-> int` in V4
  listings, with the result in the exit code while V4 cannot print values.
- `pilot mut` for every pilot that is reassigned. Every V3 listing in Part I
  also builds under `--strict-borrow`, checked by `strict_borrow` in its
  expectation.
- Interactive programs are verified with reviewed `stdin`, and take any
  non-deterministic input (a secret, a time) from an argument when one is
  given, so that their output can be checked.

## Outline

Legend: **V3** runs on the release and will be verified. **V4** is to be
checked on the snapshot when the chapter is written. **Planned** is
specification only. Bible sections are from `freak-full-bible.md`.

### Front matter

| Page | Status | Contents |
|---|---|---|
| Contents (`book`) | written | The three marks; table of contents |
| Introduction (`book-introduction`) | written | What FREAK is; V3, V4 and the bible; how each kind of statement is checked; the vocabulary; how the project is made |

### Part I: First sortie (written)

| # | Chapter | Covers |
|---|---|---|
| 1 | Getting started | Installer and what it installs; Clang; `freak doctor`; `freak upgrade`; hello; anatomy; the build report; first diagnostics; `run` / `build` / `check`; comments; `freak init`. **V4:** building from a checkout, every task needs a return type, no top-level statements, literal-only `say`, semicolons accepted |
| 2 | A guessing game | `ask`, `pilot`, interpolation, `trim` / `parse_int` / `parse_status`, a secret from the clock, `if` chain, `repeat until`, `mut`, `break` / `continue`, arguments, making a program testable. **V4:** the game's logic as scalars; `pilot mut` rejected. **Planned:** `maybe<int>`, `std::random` |
| 3 | Pilots, values and types | Declaring, inference, annotations; `mut` and `fixed` and how far each mode enforces them; scope and shadowing; top-level pilots; the 54 reserved words, letter case, and the words that are used but not reserved; `int`, `num`, `bool`, `word`; no implicit conversion; the conversion table. **V4:** case-sensitive keywords, capitalised truth literals that mean true, no `mut`, `fixed` not enforced, num accepted for int, no conversion methods, no top-level pilots, hex literal misread, no inner shadowing, weak unknown-name diagnostic, `uint` / `tiny` / `float` / `float32` / `char`. **Planned:** `big`, `num` as the default numeric type, tuples, fixed arrays |
| 4 | Tasks | Declaring and calling; parameters; `give back`; every path must give back; `void`; argument checking; copies; order and recursion; `main` and exit codes; the top level with a `main`; one namespace; `\|>`. **V4:** every task needs a return type; named arguments; arrow bodies with a written type; `\|>` silently ignored. **Planned:** arrow bodies with an inferred type, `done`, generics, closures, visibility |
| 5 | Control flow | `if` (bool only, statement only); `when` (literal arms, first match, no exhaustiveness); `repeat N times`; `repeat until`; `training arc`; `for each` over lists; `break` / `continue`; FizzBuzz and Collatz. **V4:** loops and `when` on ints; an all-give-back `else if` chain does not build; an arm after `_` is an error; `for each` not buildable; `training arc` limit not enforced; `with growth` accepted and checked. **Planned:** patterns, `enumerate` |

### Part II: Working with data

| # | Chapter | Covers | Sources |
|---|---|---|---|
| 6 | Words | Literals and escapes; length in bytes, and what that means for text outside ASCII; methods (`trim`, case, `contains`, `starts_with`, `replace`, `substring` by length, `char_at`, `repeated`); indexing; the exact interpolation rules including `.field` paths; `+` and `+=`; checked and unchecked parsing in full; `word_builder::*`; `std/string.fk`; no embedded NUL. **V4:** owned words, once the words work is on the snapshot. **Planned:** `slice`, `split`, `chars`, `char` | `words.md`; bible §1.2, §7.2 |
| 7 | Shapes | Declaring; constructing with every field named; reading and assigning fields; nesting; shapes are handles (what a task can change); `say` cannot print a shape; LLVM backend only. **V4:** shape layout status. **Planned:** generic shapes | `shapes.md`, `tutorial-data.md`; bible §1.5 |
| 8 | Methods and `impl` | Instance methods with `self`; associated methods with `Shape::name`; constructors by convention; methods that change `self`; `impl Doctrine for Shape` parses but dispatches by name only. **V4:** doctrine-bound calls and UFCS on the snapshot. **Planned:** doctrines proper, operator dispatch, `dyn` | `shapes.md`, `operators.md`; bible §1.5, §1.6 |
| 9 | Lists | `List<T>`; literals; `List::new`, `with_capacity`, `filled`; `push`, `pop`, `length`, `capacity`, `reserve`, `clear`; indexing and assignment; `pilot mut` is always required; `for each`; lists of shapes; what a list cannot hold (no nesting). **V4:** fixed arrays and list status. **Planned:** `sort`, `insert`, iterators | `arrays.md`; bible §1.4, §1.15, §7.4 |
| 10 | Legacy arrays and lookups | The `array_*` handle API; when it still matters; `std/algorithm.fk`, including the two defective helpers; parallel collections in place of a map; `word_join` | `arrays.md`, `not-in-v3.md` |
| 11 | Bytes | `ByteBuffer`: writing, the read cursor, endianness, `slice`, `status()`, `release()`; reading a binary file | `stdlib.md`; bible §7.14 |

### Part III: Ownership

| # | Chapter | Covers | Sources |
|---|---|---|---|
| 12 | What ownership is | Values that are copied and values that are shared; what "handle" means for shapes, lists and words; V3's default mode keeps everything alive; why a language would want more | `cli.md`, `tasks.md`; bible §4 preamble |
| 13 | The strict borrow checker | `--strict-borrow`: immutable by default, single-owner moves for words, lists and shapes, copy for scalars; both diagnostics with their text; patterns that satisfy it; what it does not check; where it is wrong (an int initialised from an expression is treated as moved by a call) | `cli.md`, `conformance.md`; bible §4 "what ships" |
| 14 | Meiya | V4's borrow checker: moves, `lend` and `lend mut`, drops and where they are placed, returned loans, lifetimes, the diagnostics. Everything here is **V4**, verified on the snapshot. **Planned:** `Shared<T>` / `Weak<T>`, `trust me` and honor ranks | bible §4.1 to §4.5; V4 README |

### Part IV: Building programs

| # | Chapter | Covers | Sources |
|---|---|---|---|
| 15 | Failure without `result` | Sentinel values; status shapes; `parse_status()`; `ByteBuffer.status()`; `process::exit`; `panic` and its state on the LLVM backend. **Planned:** `maybe`, `result`, `?`, `or else`, `check` (forward reference to chapter 27) | `not-in-v3.md`; bible §1.10 |
| 16 | Program structure | One flat namespace; what `use` really does; which standard modules are always loaded and which need a `use` line as a trigger; name prefixes; the concatenation pattern for several files; the top level | `stdlib.md`, `hangar.md`, `not-in-v3.md` |
| 17 | A tour of the standard library | `math::`, `std_*` integer maths, `std/convert.fk`, `std/string.fk`, `std/json.fk`, `std/version.fk`, `time::` | `stdlib.md` |
| 18 | Input, output and the terminal | `say`, `ask`, arguments, environment, exit codes, `fs::` reading and writing, ANSI colour, printing on one line, respecting `NO_COLOR` | `console.md`, `tutorial-cli-tool.md`, `stdlib.md` |
| 19 | Networking | `tcp::connect` clients; the `tcp::socket_*` family: listen, accept, timeouts, `ByteBuffer` transfer; `std/http.fk` | `stdlib.md`; bible §7.8 |
| 20 | Hangar | `hangar.toml`; `init`, `add`, `install`, `update`, `outdated`, `version`, `audit`; signing in and publishing; what the compiler does not link, and the working substitute | `hangar.md`, `cli.md`; bible §6 |
| 21 | Calling C | `extern task`; type mapping; the reserved symbol namespace; backend differences. **V4:** `extern [C]` blocks, calling conventions, callbacks, layout attributes, the C-width fence. **Planned:** the rest of §16 | `ffi.md`; bible §16 |

### Part V: Projects

Each project is one chapter that builds a complete program in steps, like
Chapter 2, with a final listing verified end to end.

| # | Chapter | Program |
|---|---|---|
| 22 | A command-line tool | A text report: arguments, reading a file, counting, coloured output, exit codes |
| 23 | A squadron roster | Shapes, methods and lists together: build a roster, total it, find and sort |
| 24 | A line server | A TCP server with the `tcp::socket_*` family that answers line commands, and a client for it |

### Part VI: The anime layer

| # | Chapter | Covers | Sources |
|---|---|---|---|
| 25 | Narrative syntax you can run | `training arc` again; `eventually` and why it is not a deferred block in V3; single bare annotations; the four operators as V3 implements them; the truth-value aliases; the build quotations | `anime-layer.md`, `operators.md`; bible §5 |
| 26 | The audit suite | `foreshadow` / `payoff`, `for science,`, `trust me`, `deus_ex_machina`: what the Python auditor checks from a source checkout, and that the native compiler rejects the same files | `anime-layer.md`, `cli.md`; bible §5.2, §5.5 |

### Part VII: The language ahead

Every chapter in this part is **Planned** from end to end, with **V4** cards
wherever the snapshot already accepts or runs something. Each one states what
V3 users write instead today.

| # | Chapter | Bible |
|---|---|---|
| 27 | Optional and fallible values: `maybe`, `result`, `?`, `or else`, `check` | §1.4, §1.10 |
| 28 | Variants, routes and patterns: `variant`, `alias`, destructuring `when`, exhaustiveness | §1.14, §1.7, §5.3 |
| 29 | Doctrines and generics: `doctrine`, bounds, `dyn Doctrine` | §1.6, §1.11 |
| 30 | Closures and iterators: capture modes, `std::iter`, `for each` in full | §1.8, §7.5 |
| 31 | Collections: `Map`, `Set`, `Lineup`, tuples, fixed arrays | §1.3, §1.4, §7.4 |
| 32 | Borrowing in full: `lend`, lifetimes, `Shared` / `Weak`, `trust me` | §4 |
| 33 | Concurrency: `xm3`, `sortie` / `debrief`, `formation`, `Comms`, `BriefingRoom`, `wingman` | §3 |
| 34 | The advanced types: `power<N>`, `prob[lo..hi]`, `causality<T>`, `mood` | §2 |
| 35 | Modules, visibility and packages: `use`, `launch`, the full `hangar.toml` | §1.13, §6, §17.4, §17.5 |
| 36 | Build modes, voices and tests: the build modes, the error voice cast, `std::test` | §12, §14, §7.17 |

### Part VIII: Inside the compilers

| # | Chapter | Covers | Sources |
|---|---|---|---|
| 37 | How V3 works | Eight files concatenated into one program; lexer, parser, checker, two emitters; the runtime; building it from the C seed and the fixed-point check; the two backends | `getting-started.md`; V3 README |
| 38 | How V4 works | The crates; lex, parse, expand, HIR, resolve, TY, MIR, Meiya, LLVM; the four boundaries; queries and snapshots; `build_v4.py` and `check_v4.py` | V4 README, `freakc-v4-00-unit-architecture.md` |
| 39 | Reading diagnostics | V3's two formats; V4's coded diagnostics; the borrow-checker voices; what an editor does with them | bible §14, §17 |
| 40 | Contributing | The repository's gates, the conformance audit, how this book and the docs are verified | `CONTRIBUTING.md`, `MAINTENANCE.md` |

### Appendices

| | Appendix | Contents |
|---|---|---|
| A | Reserved words | The 54 V3 words (48 keywords and 6 truth literals), the multi-word keywords, what each is for, V4's case rule |
| B | Operators | Precedence, type rules, the anime operators |
| C | The command line | Every `freak` and `hangar` command and flag |
| D | Types and conversions | Every type in V3 and every conversion |
| E | Grammar | The V3 grammar |
| F | Glossary | FREAK's vocabulary and the usual term for each |
| G | From V3 to V4 | Every difference recorded in an In V4 box, in one table |
| H | Feature status | Each language feature: V3, V4 snapshot, or planned |
| I | How this book is checked | The three lanes, the pins, how to re-run them |

## Decisions still open

1. **Where the book appears on freaklang.dev.** The site's `/book` route is
   driven by `chapters.ts` (eleven short chapters, separate from this
   repository). The fragments this repository emits would put the book under
   `/docs/v3`. Either the site's `/book` route should read these fragments, or
   the old chapters should be retired when Part II lands.
2. **The V4 pin.** Part I is pinned to `main` at `7c9a1f3c`. The words work
   (Freak-lang PR #143) is not on that commit. Moving the pin after it merges
   will change several Part I notes: `say` of values, `pilot mut`, checked
   arithmetic.
3. **`task main()` or `task main() -> void`.** The book uses the short form,
   which V3 accepts and the V4 snapshot does not. If V4 is going to keep
   requiring the type, the book should switch.
4. **Translations.** The site translates the reference pages. The book is
   English only until its text settles.
5. **How much of Part VII to write before V4 can run it.** The chapters can be
   written from the bible now and gain V4 cards later, or wait.
6. **Is a pilot mutable by default?** The bible says both. Section 1.1 says
   "Mutable by default" with `fixed pilot` as the immutable form. The
   borrow-checker note in section 4 describes V3's strict rule, where only
   `pilot mut` may be reassigned. V3 follows section 1.1 by default and
   section 4 under `--strict-borrow`. V4 `main` follows section 1.1 and
   rejects `mut`; PR #143 accepts `mut`. The book tells readers to write
   `pilot mut` for anything they reassign. If the answer is section 1.1, that
   advice and every listing change.

## Found while writing Part I

Things the checks turned up that are not the book's to fix. Each was
reproduced with the pinned release or the pinned V4 commit, on Linux x64. No
listing has been run on Windows or macOS; statements about those systems in
Chapter 1 come from reading the installer scripts, not from running them there.

### V3 0.14.2 behaviour that differs from the reference pages

| Reference page says | The release does |
|---|---|
| `for each` is rejected (`control-flow.md`, `not-in-v3.md`, `conformance.md`, `tutorial-first-program.md`) | `for each x in list` works over a `List<T>` |
| A bare `{ }` block does not create a scope (`control-flow.md`) | A pilot declared in any block ends with it |
| `when` arms are expressions compared for equality (`control-flow.md`) | An arm must be a literal or `_`: `when case must be a literal or '_'` |
| With a `main`, top-level statements run first (`tasks.md`) | They are not run at all; only top-level declarations take effect |
| `pilot`, `Pilot` and `PILOT` are the same token (`language-basics.md`, `index.md`) | All are reserved, but a single-word keyword works only in lowercase; `Pilot x = 1` is a syntax error. The two-word keywords `Give Back`, `For Each` and `Training Arc` do work in any case |
| There is no negative literal (`language-basics.md`, `operators.md`) | `-5` works as an initialiser, argument and operand |
| `.length()` counts characters (`words.md`) | It counts bytes: a word holding one accented letter has length 2 |

### V3 0.14.2 defects and sharp edges

| What | Detail |
|---|---|
| `TRUE`, `Yes` and other capitalised truth literals | Accepted, and evaluate to `false` |
| `panic(...)` on the LLVM backend, Linux x64 | Fails to link: undefined reference to `freak_llvm_panic`. Works with `--c` |
| Integer division by zero | Unchecked: killed by a signal with a runtime zero, a meaningless value with a constant zero |
| A program with no `main` and no top-level statements, for example `task Main()` | Builds and exits 0 without a diagnostic |
| `freak run` | Cannot pass arguments to the program |
| `--strict-borrow` and an int pilot initialised from an expression | Passing it to a task marks it as moved; the next use is refused with `Shirogane. You gave this away`. An int initialised from a literal is copied as expected |
| `parse_status()` | Sticky: it keeps the last failure until `parse_clear_status()` is called, so a later successful parse still reads as failed |
| `to_int()` and `to_num()` on a word | Parse a leading numeric prefix and ignore the rest: `"12abc".to_int()` is 12, with no status set |
| `give` and `back` as pilot names | Accepted, and then `say give` followed on the next line by `back = 3` is read as `give back`: the two-word keyword is joined across a line end |
| `install.sh` | Adds the `PATH` block only to startup files that already exist. With no `.zshrc`, `.bashrc` or `.bash_profile` (a new macOS account), nothing is added and a new terminal does not find `freak` |
| The bible's own status lines | Say `launch` ships (section 6) and `maybe<T>` is implemented (section 1.4). The release rejects `launch task f()` and `pilot m: maybe<int>` |

### V4 at `7c9a1f3c`

| What | Detail |
|---|---|
| `training arc ... max N sessions` | The limit is type-checked and not enforced; the loop runs until the condition is true |
| `\|>` | Accepted and left out of the generated program |
| An unknown name, and `task main()` without a return type | Reported only by code generation, as `native type not yet supported: unknown` |
| `pilot mut` | Rejected as `unsupported local pattern` |
| Shadowing in an inner block | Rejected as a duplicate local |
| A pilot named `sessions` | Accepted, and then breaks the parse of a `training arc` heading that uses it |
| Capitalised truth literals (`TRUE`, `Yes`) | Literals that mean true, where V3 reads them as false. V4 is right; programs that relied on V3 change meaning |
| Semicolons | Accepted as statement separators, where V3 rejects them |
| `uint`, `tiny`, `float`, `float32`, `char` and their literal suffixes | Build and run, ahead of V3. `big` is recognised and cannot be built |
| Named arguments | Build and run, ahead of V3 |
| `training arc ... with growth` | Accepted, and a body that cannot change the condition's pilot is refused |
| An `if` / `else if` / `else` chain in which every branch gives back | Does not build: `mir cfg unreachable live block`. Works when the last case follows the chain |
| A num where an int is required (initialiser, assignment, argument, return) | Accepted, and the fraction is dropped without a message. V3 rejects each |
| `0xFF` | Read as `0` with no diagnostic. V3 reports `unknown binding 'xFF'` |
| `fixed pilot` | Accepted and reassignable |
| A task with no return type | Any task, not only `main`, fails as `native type not yet supported: unknown` |
| Top-level `pilot`; top-level `fixed pilot` | The first is a syntax error (the bible allows only declarations and constants at root). The second fails in code generation: `native symbol values currently support only task pointers` |
| `to_num()`, `to_int()` and the other conversion methods | Missing: `int offers no method to_num` |
| A `when` arm after `_` | An error (`unreachable when arm`), where V3 accepts it silently. V4 is right |
| Storing a `void` result; a task inside a task | Rejected only by code generation, with `not yet supported` wording |
| A num as the `training arc` session limit | Accepted. V3 requires an int |
| `task f(x: int) -> int => x * x` | Builds and runs, ahead of V3. The bible's form without a return type does not |
