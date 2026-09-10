# Bible vs V3

> A section-by-section comparison of `freak-full-bible.md` against what the V3 compiler accepts, established by compiling probe programs.

## Method

The bible carries its own status table in §0.2, but that table describes the
project as a whole — it counts a feature as landed when it works in the **V4**
compiler under `src/compiler/v4/`. Many rows marked "⚠️ Partial" are entirely
absent from the shipping V3 compiler.

The verdicts below come from a different method: writing a probe program for
each feature and running it through a V3 binary built from source. "Compiles"
means the frontend accepted it. "Rejected" quotes the actual diagnostic.

{{verified-summary}}

> [!note]
> A recurring pattern is worth stating once. Many bible features are
> **lexed but not parsed**: the lexer knows the keyword, so it can never be an
> identifier, but no grammar rule consumes it. These fail with
> *"unexpected 'X' — this token cannot start an expression"*. The feature is
> reserved and unusable at the same time.

## Section 1 — Syntax

Bible status: ⚠️ Partial. Real V3 status: a small core works.

| §1 feature | Bible | V3 | Evidence |
|---|---|---|---|
| 1.1 `pilot` / `fixed pilot` / `pilot mut` | ✅ | **Compiles** | |
| 1.1 Type annotation `x: T` | ✅ | **Compiles** — one identifier, plus `List<T>` | |
| 1.2 `task name(p: T) -> R { }` | ✅ | **Compiles** | |
| 1.2 `give back` | ✅ | **Compiles** | |
| 1.2 Arrow body `=> expr` | ✅ | **Rejected** | `expected '{', found '=>'` |
| 1.2 `done` block terminator | ✅ | **Rejected** | `expected '{', found 'give back'` |
| 1.2 Named call arguments | V4 | **Rejected** | |
| 1.2 `say` | ✅ | **Compiles** — scalars only, not shapes | |
| 1.2 `{path}` interpolation | ✅ | **Compiles** — paths only, never calls | |
| 1.3 `int` `num` `word` `bool` `void` | ✅ | **Compiles** | |
| 1.3 `uint` `tiny` `char` `big` `float` `float32` `never` | V4 | **Absent** | |
| 1.3 `[T; N]`, tuples, `*T` / `*mut T` | V4 | **Rejected** | |
| 1.4 `maybe<T>` / `some` / `nobody` | ✅ | **Rejected** | `expected '{', found '<'` |
| 1.4 `result<T,E>` / `ok` / `err` | ✅ | **Rejected** | |
| 1.4 `List<T>` | ✅ | **Compiles** — typed, indexable, `List::filled`; no `push`/`sort`/iterators | |
| 1.4 `Map<K,V>` `Set<T>` `Lineup<T>` | ✅ | **Absent** | No map literal either |
| 1.5 `shape` declaration | ✅ | **Compiles** | |
| 1.5 Shape construction `S { f: v }` | ✅ | **Compiles** | LLVM backend |
| 1.5 `impl S { task m(self) }` | ✅ | **Compiles** | |
| 1.5 Generic shapes `shape Pair<A,B>` | V4 | **Rejected** | |
| 1.6 `doctrine` declaration | ⚠️ | **Rejected** | `unexpected 'doctrine'` |
| 1.6 `impl D for S { }` | ⚠️ | **Compiles** — `D` unvalidated | |
| 1.6 Operator dispatch via `Add` | ⚠️ | **Rejected** | `operator '+' does not accept Vec2 and Vec2` |
| 1.6 `dyn Doctrine`, vtables | V4 | **Absent** | |
| 1.7 `if` / `else if` / `else` | ✅ | **Compiles** | |
| 1.7 `when` with literal arms and `_` | ⚠️ | **Compiles** — statement only | |
| 1.7 `when` with destructuring | V4 | **Absent** | |
| 1.7 `for each x in list` | ✅ | **Rejected** | `unexpected 'for each'` |
| 1.7 `repeat N times` / `repeat until` | ✅ | **Compiles** | |
| 1.7 `training arc ... max N sessions` | ⚠️ | **Compiles** | |
| 1.7 `training arc ... with growth` | V4 | **Rejected** | |
| 1.7 `break` / `continue` | ✅ | **Compiles** | |
| 1.8 Closures `\|x\| => expr` | ⚠️ | **Rejected** | `unexpected '\|'` |
| 1.8 Capture modes `copy` / `move` / `mut` | V4 | **Absent** | |
| 1.9 Pipe `\|>` | ✅ | **Compiles** — bare task names only | |
| 1.10 `?` propagation | ✅ | **Rejected** | `unexpected '?'` |
| 1.10 `check` over maybe / result | ✅ | **Rejected** | `unexpected 'check'` |
| 1.10 `or else` | ✅ | **Rejected** | `unexpected 'or else'` |
| 1.11 Generics `<T>`, bounds | ⚠️ | **Rejected** | `expected '(', found '<'`. `List<T>` is a hard-coded special case, not a mechanism |
| 1.12 `lend` / `lend mut` | ⚠️ | **Rejected** | `expected an identifier for parameter name, found 'lend'` |
| 1.13 `use module::{...}` | ⚠️ | **Stripped** — a build hint, not an import | |
| 1.13 `use module::*` | V4 | **Stripped** | |
| 1.13 `launch` visibility | ⚠️ | **Rejected** | `unexpected 'launch'` |
| 1.14 `variant` | V4 | **Rejected** | |
| 1.14 `alias` | V4 | **Rejected** | |
| 1.14 Root `fixed pilot` constants | ⚠️ | **Compiles** — and V3 also allows mutable root bindings and root statements, which the bible forbids | |
| 1.15 `[a, b, c]` literal | ⚠️ | **Compiles** — infers `List<T>` from its elements | |
| 1.15 `[expr; N]` repeat-fill | V4 | **Rejected** | |
| 1.15 No implicit tail return | ✅ | **Enforced** | |

## Section 2 — Advanced type system

Bible: 🔜 V4, entire section. V3: **entirely absent**, as documented.

`power<N>`, `prob[lo..hi]`, `causality<T>` and `mood` do not lex or parse.

## Section 3 — Concurrency

Bible: 🔜 V4, entire section. V3: **entirely absent**.

No `xm3`, `sortie`, `debrief`, `formation`, `BriefingRoom`, `wingman` or
`Comms`. None of those words are even keywords in V3's lexer. `||` lexes as a
single token but has no grammar rule.

There is no concurrency in V3 at all — not even `std::thread::spawn`.

## Section 4 — Borrow checker

Bible: ⚠️ Partial, with an extensive description of V4's Meiya checker.

V3 ships **Phase-1 only**, behind `--strict-borrow`:

| Rule | V3 |
|---|---|
| `pilot` immutable, `pilot mut` reassignable | Enforced under the flag |
| Single-owner moves for `word`, arrays, shapes | Enforced under the flag |
| `int` / `num` / `bool` are Copy | Enforced under the flag |
| Nominal member validation | **Always on**, flag or not |
| `lend` / `lend mut` parameters | Do not parse |
| Lifetimes `'a`, outlives bounds `'long: 'short` | Do not lex |
| `Shared<T>` / `Weak<T>` | Absent |
| `trust me ... on my honor as .level` | Does not parse |
| `direct_order [arch] { }` | Does not parse |

Without the flag, V3 does no ownership checking whatsoever.

Everything the bible's §4 describes at length — returned loans, provenance
memoisation, fixed-layout aggregate children, snapshot restore, invalidation
report fields — is V4 work in `src/compiler/v4/`. None of it exists in the
shipping compiler.

## Section 5 — Anime layer

| §5 feature | Bible | V3 |
|---|---|---|
| 5.1 `@annotation` | ⚠️ | **Parses, ignored.** One per statement, no arguments |
| 5.1 `@deprecated` enforcement | ⚠️ | Not enforced |
| 5.1 Caller prefixes `sadly`, `for science,`, `knowing this will hurt,` | ⚠️ | **Rejected** |
| 5.2 `foreshadow` / `payoff` | ✅ | **Rejected** — the auditor scans text only |
| 5.3 `route`, `check route`, `only on` | V4 | **Rejected** |
| 5.4 `PLUS ULTRA` `NAKAMA` `FINAL FORM` `TSUNDERE` | ⚠️ | **Compile**, with different position and semantics |
| 5.5 `deus_ex_machina` | ⚠️ | **Rejected** |
| 5.6 `training arc` | ⚠️ | **Compiles** |
| 5.6 `with growth` | V4 | **Rejected** |
| 5.7 `isekai { } bringing back { }` | ⚠️ | **Rejected** |
| 5.7 `eventually { }` | ⚠️ | **Compiles**, emitted inline — not deferred, not LIFO |
| 5.7 `eventually if cond { }` | ⚠️ | **Rejected** |

> [!warn]
> The bible marks §5.2 foreshadowing as ✅ Implemented and the
> `deus_ex_machina` 20-word minimum as enforced. Both are true of the **Python
> auditor**, which scans source text. Neither construct parses in the native V3
> compiler — a file using them audits cleanly and fails to build.

The four anime operators also diverge in form, not just in enforcement:

| Operator | Bible | V3 |
|---|---|---|
| `FINAL FORM` | postfix, `base FINAL FORM` → `base * base`, 5s build pause | **prefix**, `int` only, `x * x`, no pause |
| `PLUS ULTRA` | infix, `base PLUS ULTRA emotion` → `base * (1 + e²)` | **prefix**, `int` only, `x * 2` |
| `TSUNDERE` | postfix; `!x` for bool, `-x` for num | **prefix**, `int` only, `0 - x` |
| `NAKAMA` | infix, `a + b + (a * b * 0.1)` | infix, `int` only, `a + b` |

## Section 6 — Modules and Hangar

| Feature | Bible | V3 |
|---|---|---|
| `use module::{names}` | ⚠️ | Line is **replaced with a comment** before parsing |
| `use module::*` | V4 | Same — stripped |
| `launch` / `launch(package)` | ⚠️ | **Rejected** |
| Module-private visibility | ⚠️ | **No visibility system at all** |
| `hangar.toml` | ⚠️ | Works |
| `hangar init/add/remove/install/update` | ⚠️ | Work |
| `hangar search` | V4 | Absent |

> [!warn]
> V3 has **no module system**. Everything — your file, and every standard
> library file linked into the build — shares one flat global namespace. A
> `use` line only signals the build to link `std/math3d.fk`, `std/zip.fk`,
> `std/ui/window.fk` or the cockpit package. Every other module is already in
> scope without it.

## Section 7 — Standard library

| Bible module | V3 |
|---|---|
| `std::word` methods | Partial — as builtin `word` methods, plus `.repeated(n)`. `.substring` takes a **length**, not an end index; no `.split`, `.chars` |
| `std::word` `WordBuilder` | Present as `word_builder::*` over an `int` handle |
| `std::num` | Absent — `math::*` builtins plus `std_*` int tasks instead |
| `std::collections` `List<T>` | Partial — typed and indexable, but no `push`, `pop`, `sort` or iterators |
| `std::collections` `Map`/`Set`/`Lineup` | **Absent** |
| `std::iter` | **Absent** |
| `std::io` | `say` and `ask` only |
| `std::fs` | Partial — 7 builtins, no `copy`/`move`/`is_file`/`is_dir` |
| `std::net` | Partial — the older `tcp::` calls plus a `tcp::socket_*` family with listen, accept, timeouts and `ByteBuffer` transfer |
| `std::time` | `time::now_ms()` and `time::monotonic_ns()` |
| `std::math` | 8 `math::` builtins; no `log`, `exp`, `atan2`, `gcd`, `simd` |
| `std::random` | **Absent** |
| `std::process` | Partial — adds `pid()` and `set_env()`; `args()` deliberately rejected in favour of `args_count()` / `arg(i)` |
| `std::thread` | **Absent** |
| `std::bytes` | Present as the builtin `ByteBuffer` type, with `status()` instead of `result<T,E>` |
| `std::anime`, `std::narrative`, `std::test` | **Absent** |
| `std::mem`, `std::ffi` | **Absent** |
| `std::json`, `std::version`, `std::string`, `std::convert`, `std::algorithm` | **Present** as FREAK source — not in the bible's shape, but real and working |

Two `std/algorithm.fk` helpers are defective in the shipping compiler:
`array_sort_word` segfaults, `array_unique` returns an empty array. Both were
confirmed against the binary that verified this site.

## Section 8 — Lexer

The V3 lexer implements a **subset** of the bible's token table.

Present: the 47 single-word keywords, 6 bool literals, 10 multi-word keywords,
and the punctuation set.

Absent: `variant`, `alias`, `dyn`, `never`, `const`, all concurrency keywords,
`knowing`, `on my honor as`, `declare was`, `prob when`, `direct_order`,
lifetime tokens `'a`, numeric suffixes (`42u`, `3.14f`, `42t`, `999b`), and
`...` ellipsis.

The bible's §8.3 requires V4 keywords to be matched **case-sensitively** so
that `Pilot` and `Some` stay usable as identifiers. **V3 does the opposite** —
it lowercases before comparing, so `Pilot`, `Result` and `Max` are keywords and
cannot be names. This is the single largest practical divergence for someone
writing V3 code.

## Sections 9–17

| Section | Bible | V3 |
|---|---|---|
| §9 Parser AST nodes | ⚠️ | Core nodes only. No `ErrorNode` / `IncompleteNode`, no node ids, no incremental parsing |
| §10 Type checker | ⚠️ | Basic inference, arity and type checks, nominal member validation. None of the listed advanced rules |
| §11 Code generation | ⚠️ | LLVM and C backends work. No mood, variant, `dyn`, `Shared<T>` or classified codegen. LLVM emits LineTablesOnly DWARF |
| §12 Build modes | V4 | Absent — only `--opt=0..3` and backend choice |
| §13 Compiler CLI | ⚠️ | Most commands present; `-o`, `--voice=`, `--clearance=`, `--build-mode=`, and in-language `test` blocks absent |
| §14 Error voices | V4 | Absent — generic diagnostics, plus two signature borrow-checker lines |
| §15 Cheatsheet | ⚠️ | Describes the full language; roughly a fifth applies to V3 |
| §16 FFI | V4 | Only bare `extern task f(...) -> T`. No blocks, conventions, `link=`, layout attributes, raw pointers or `trust me` |
| §17 Compiler internals / IDE | V4 | Absent. Parse errors abort; no tolerant AST, no panic infrastructure, no LSP |

## Summary

Counting the bible's own feature inventory against compile evidence:

| | Compiles in V3 | Absent |
|---|---|---|
| §1 Syntax | ~20 of 45 sub-features | ~25 |
| §2 Advanced types | 0 | all |
| §3 Concurrency | 0 | all |
| §4 Borrow checker | 3 Phase-1 rules, opt-in | the rest |
| §5 Anime layer | 4 of 20 | 16 |
| §6 Modules | Hangar CLI only | the module system |
| §7 Stdlib | ~8 of 19 modules, reshaped | 11 |
| §16 FFI | 1 declaration form | all else |

> [!note]
> V3 is not standing still inside its version number. `List<T>`, `ByteBuffer`,
> `word_builder::*`, the `tcp::socket_*` family, `word.repeated(n)`,
> `time::monotonic_ns()`, `process::pid()` and `ui::set_clip` all landed after
> the first pass of this site was written, with `VERSION` unchanged at
> `0.14.1`. The compiler generation is frozen for *new semantics*; the builtin
> table clearly is not. Re-run the verification harness when you pull.

V3 is a small, sharp, genuinely self-hosting language: scalars, words, shapes,
methods, three loops, two branch forms, flat arrays and a C FFI. The bible
describes where FREAK is going. This site describes where it is.

For what to write instead of the missing features, see
[Not in V3](not-in-v3.html).
