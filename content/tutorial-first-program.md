# Tutorial 1: Your first program

> Build and run a FREAK program from nothing, then grow it into something with a shape and a method. About 15 minutes.

This assumes you have a working `freak` on your PATH. If not, do
[Getting started](getting-started.html) first — you need to build the compiler
from source, because V3 is self-hosted.

## Step 1 — Say something

Create `greet.fk`:

```fk
task main() -> void {
    say "Valkyries, launch"
}
```

Run it:

```sh
freak run greet.fk
```

Two things are already worth noticing. `say` needs no import — it is a compiler
builtin, always in scope. And `main` is optional: statements written at the top
level of a file run in order, so this would work too:

```fk
say "Valkyries, launch"
```

Use `main` anyway. It gives you somewhere to put local bindings.

## Step 2 — Bindings

`pilot` introduces a binding. Add a couple:

```fk
task main() -> void {
    pilot callsign: word = "Valkyrie-1"
    pilot sorties: int = 12

    say callsign
    say word_from_int(sorties)
}
```

The annotation is optional — `pilot sorties = 12` infers `int`. Note
`word_from_int`: `say` accepts `int` directly, but the moment you want to glue
a number onto a word you must convert it, because `+` will not mix types.

There are five types worth knowing at this stage: `int`, `num` (float), `word`
(string), `bool`, and `void`. Full list in
[Bindings & types](language-basics.html).

> [!warn]
> **Do not name anything `Pilot`.** V3 matches keywords case-insensitively, so
> `Pilot`, `PILOT` and `pilot` are the same token, and none can be an
> identifier. The same trap catches `Result`, `Max`, `Check`, `Route`, `Move`,
> `Copy`, `Some`, `Ok`, `Err` and `Done`. Pick a synonym — this tutorial uses
> `Aviator`.

## Step 3 — Interpolation

Instead of converting and concatenating, put the value in the string:

```fk
task main() -> void {
    pilot callsign: word = "Valkyrie-1"
    pilot sorties: int = 12

    say "{callsign} has flown {sorties} sorties"
}
```

`{path}` substitutes a binding. A *path* is an identifier plus optional
`.field` hops — `callsign`, `unit.name`, `self.frame.thrust`.

> [!warn]
> Interpolation substitutes paths, **never calls**. `"{rank()}"` prints those
> characters literally rather than calling anything. Compute into a binding
> first — this is the single most common surprise in V3.

## Step 4 — A task of your own

`task` declares a function; `give back` returns from it.

```fk
task rank_for(sorties: int) -> word {
    if sorties >= 50 { give back "veteran" }
    if sorties >= 10 { give back "regular" }
    give back "rookie"
}

task main() -> void {
    say rank_for(12)
}
```

There is **no implicit return**. A block-bodied task that returns a value needs
`give back` on every path — a bare expression at the end is evaluated and
discarded. The arrow shorthand `=> expr` from the specification does not parse
in V3.

Order does not matter: every task is indexed before any body is checked, so
`main` can call a task declared below it.

## Step 5 — A shape

`shape` is V3's record type, and the only user-defined type there is.

```fk
shape Aviator {
    name: word
    sorties: int
}

task main() -> void {
    pilot takeru: Aviator = Aviator { name: "Shirogane Takeru", sorties: 12 }
    say takeru.name
    say word_from_int(takeru.sorties)
}
```

Every field must be supplied by name at construction. Fields are readable and
assignable, and they chain: `unit.frame.thrust`.

## Step 6 — Methods

`impl` attaches tasks to a shape. Whether the first parameter is `self` decides
how you call it.

```fk
impl Aviator {
    -- No self: an associated method, called Aviator::recruit(...)
    task recruit(name: word) -> Aviator {
        give back Aviator { name: name, sorties: 0 }
    }

    -- With self: an instance method, called value.rank()
    task rank(self) -> word {
        if self.sorties >= 50 { give back "veteran" }
        give back "rookie"
    }
}
```

Write `self` bare, never `self: Aviator` — the compiler fills in the owning
shape.

## Step 7 — Loops

Three forms, no `for each`:

```fk
repeat 12 times { takeru.sorties += 1 }     -- counted
repeat until done { work() }                 -- condition, tested first
training arc until ready max 8 sessions { }  -- bounded, cannot spin forever
```

To reassign a binding you must declare it `pilot mut`. Without `--strict-borrow`
the compiler will not enforce that, but write it anyway — it documents intent
and the checker will demand it once you turn the flag on.

## The finished program

Everything above, assembled:

{{example:tut_greet}}

## Where to go next

- [Tutorial 2](tutorial-cli-tool.html) — a real command-line tool with files and colour
- [Tutorial 3](tutorial-data.html) — lists, and modelling data properly
- [Control flow](control-flow.html) — the loop and branch forms in detail
- [Not in V3](not-in-v3.html) — what to write instead of the features the specification promises
