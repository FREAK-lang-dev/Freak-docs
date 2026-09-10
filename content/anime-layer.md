# Anime layer

> FREAK's signature feature set. Four pieces of it compile in V3; the rest is specified but unimplemented.

The bible's Section 5 describes a large narrative-flavoured layer: foreshadowing
debts, route types, honour-gated unsafe blocks, death-flag analysis, and
`deus_ex_machina` miracles. V3 implements a small slice of it.

## What compiles

| Construct | Status in V3 |
|---|---|
| `training arc until C max N sessions { }` | **Works** — a real bounded loop |
| `eventually { }` | **Parses and emits**, but inline, not deferred |
| `@annotation` | **Parses**, then ignored. One per statement, no arguments |
| `PLUS ULTRA`, `FINAL FORM`, `TSUNDERE`, `NAKAMA` | **Work**, with different semantics from the spec |

Everything else in Section 5 fails at the parser.

## training arc

The one anime construct that is genuinely useful and genuinely implemented. It
is a loop with a mandatory session cap, so it cannot spin forever.

{{example:training_arc}}

Full details in [Control flow](control-flow.html#training-arc).

## eventually

{{example:eventually}}

> [!warn]
> V3 emits the block **inline, at the point you wrote it**. It is not deferred
> to end of scope, it does not run in LIFO order with other `eventually`
> blocks, and it does not run on `give back`, `break` or `panic`. It is a
> labelled section, not `defer`.

`eventually if cond { }` does not parse: `expected '{', found 'if'`.

## Annotations

V3's parser recognises `@` followed by one identifier, discards it, and carries
on. No annotation has any semantic effect.

{{example:annotations}}

Three hard limits:

- **No arguments.** `@rival(meiya)` breaks — the parser consumes `@rival`, then
  tries to parse `(meiya)` as the next statement and reports `unknown binding
  'meiya'`. The same applies to `@experiment("...")`,
  `@classified("...")` and `@i_know_what_im_doing("...")`.
- **One per statement.** Stacking two annotations fails with `unexpected '@'`.
- **No validation.** Any identifier is accepted; unknown names are not warned
  about, and `@season_finale` is not checked for uniqueness.

So `@protagonist` grants no power level, `@nakige` requires no caller prefix,
`@deprecated` produces no warning, and `@classified` redacts nothing.

## The anime operators

Four operators work, with V3-specific meanings.

{{example:anime_operators}}

| Operator | V3 form | V3 lowering |
|---|---|---|
| `FINAL FORM x` | prefix, `int` | `x * x` |
| `PLUS ULTRA x` | prefix, `int` | `x * 2` |
| `TSUNDERE x` | prefix, `int` | `0 - x` |
| `a NAKAMA b` | infix, `int` | `a + b` |

The specification puts all three unary forms in postfix position, allows `num`
and `bool`, and defines emotional scaling formulas. V3 does none of that — see
[Operators](operators.html#the-anime-operators).

## What does not parse

Each of these lexes as a keyword and then fails in the parser with
*"this token cannot start an expression"*:

| Construct | Bible section |
|---|---|
| `foreshadow pilot x = ...` / `payoff x` | §5.2 |
| `route TrueRoute`, `check route`, `only on R from x` | §5.3 |
| `deus_ex_machina "20+ words" { }` | §5.5 |
| `isekai { } bringing back { }` | §5.7 |
| `trust me "reason" on my honor as .level { }` | §4.5 |
| `direct_order [arch] { asm }` | §4.5 |
| `sadly call()` | §5.1 |
| `for science, call()` | §5.1 |
| `knowing this will hurt, call()` | §5.1 |
| `training arc ... with growth` | §5.6 |
| `prob[0.3] chance { }`, `prob_when` | §2.2 |
| `declare x was v in timeline "t"` | §2.3 |
| `mood`, `.chill` and mood arithmetic | §2.4 |

> [!note]
> `knowing` is not even a keyword in V3's lexer — it parses as an ordinary
> identifier, and the error surfaces at the comma instead.

## The audit commands

The audit subcommands still exist and still work, because they are **text
scanners running outside the compiler**:

```sh
freak audit-science      # every `for science,` call site
freak audit-trust        # every `trust me` block and its honor level
freak audit-miracles     # every `deus_ex_machina` block
freak foreshadow-audit   # unpaid `foreshadow` bindings
```

They shell out to `python -m freakc`, so they need the Python bootstrap package
and the repository's audit inputs. They scan source text — which means they can
report on constructs the native V3 compiler cannot compile. A file full of
`foreshadow` declarations will audit cleanly and fail to build.

## Writing anime-flavoured V3 today

The layer you can actually use is narrow, but it is not nothing:

```fk
@protagonist
task engage(power: int) -> word {
    pilot mut charge: int = power

    training arc until charge >= 9000 max 12 sessions {
        charge = PLUS ULTRA charge
    }

    eventually {
        say "systems nominal"
    }

    if charge >= 9000 { give back "over nine thousand" }
    give back "insufficient"
}
```

Bounded loops, prefix power scaling, a cleanup section and decorative
annotations. Everything else is [V4](not-in-v3.html).
