# Control flow

> Choose between paths with `if` and `when`, and repeat work with four kinds of loop.

A program that only ran its statements from top to bottom could do very
little. This chapter covers the statements that decide what runs next:

- `if`, `else if` and `else`
- `when`, for choosing by value
- `repeat ... times`, for a known number of passes
- `repeat until`, for looping on a condition
- `training arc`, a condition loop that is guaranteed to end
- `for each`, for visiting the elements of a list
- `break` and `continue`

## `if`

`if` runs a block when a condition is true.

{{example:book_if}}

The condition comes straight after `if`, without parentheses. The block is
always in braces, even when it holds a single statement:

{{diagnostic:book_if_needs_braces}}

An `if` can be followed by `else`, whose block runs when the condition is
false. In between you can put any number of `else if` branches. The conditions
are tested from the top, the first true one has its block run, and the rest are
skipped. In `status`, a fuel level of 40 fails the first test, passes the
second, and the remaining two branches are never looked at.

That order matters. Had the tests been written the other way round, with `fuel
> 0` first, every positive level would have been caught by it and reported as
bingo fuel.

### The condition must be a bool

Some languages treat zero as false and anything else as true. FREAK does not.
A condition has to be a `bool`, and nothing else is accepted in its place:

{{diagnostic:book_if_needs_bool}}

Say what you mean: `if fuel > 0`.

Comparisons cannot be chained the way they are in mathematics, either:

{{diagnostic:book_chained_comparison}}

The message makes sense once you see how the expression is read. `25 < fuel`
is worked out first and gives a bool. The compiler is then asked to compare
that bool with 75. Write the two comparisons separately and join them:
`if 25 < fuel and fuel < 75`.

### `if` is a statement

An `if` does something. It does not produce a value, so it cannot stand on the
right of an `=`:

{{diagnostic:book_if_is_not_a_value}}

There are two ways to get the same effect. Declare the pilot first and assign
to it in each branch:

```fk
    pilot mut state = ""
    if fuel > 25 {
        state = "cruising"
    } else {
        state = "bingo"
    }
```

Or put the decision in a task and give the answer back, as `status` does in
the first listing. The second way is usually cleaner, because the pilot that
receives the answer does not need to be `mut`.

## `when`

A chain of `else if` that compares one value against several possibilities is
better written as a `when`.

{{example:book_when}}

`when` takes a value, called the subject, and a list of *arms*. Each arm is a
literal value, an arrow, and one statement. The subject is compared with each
arm's value in turn, and the first arm that is equal has its statement run.
The arm written `_` matches anything. It is the catch-all.

The listing shows the rest of the rules.

An arm holds one statement. To run several, put them in a block, as the
`"ace"` arm does.

If no arm matches and there is no `_`, nothing happens, and the program
carries on after the `when`. The compiler does not insist that you cover every
case, so a missing arm fails silently. Unless you are certain the listed values
are the only ones possible, end with `_`.

Arms are tried in order. The last `when` in the listing puts `_` first, and so
its second arm can never run. The compiler does not warn about this. Keep the
catch-all at the bottom.

The subject can be an int, a word, a bool or a num.

### Arms are literals

An arm's value has to be written out as a literal. It cannot be a pilot or a
calculation:

{{diagnostic:book_when_needs_literal}}

When the values you are comparing against are not known until the program
runs, use `if` and `else if`.

The literal also has to be of the subject's type:

{{diagnostic:book_when_wrong_type}}

### `when` in a task that gives back

Like `if`, a `when` is a statement and has no value. Like `if`, it pairs well
with `give back`. In `order_for`, each arm gives back a word, and because the
`_` arm covers everything else, the compiler accepts that every path through
the task gives something back.

## `repeat ... times`

The simplest loop runs a block a set number of times.

{{example:book_repeat_times}}

The count is any int: a literal, a pilot, a calculation. It is worked out once,
before the first pass. The third loop in the listing changes `passes` inside
its own body, and still makes exactly the two passes it started with.

There is no loop counter. If the body needs to know which pass it is on, keep
a `pilot mut` beside the loop and increase it yourself, as the second loop
does. This is the standard way to count in V3.

A count of zero, or a negative count, means the body does not run at all.

The count must be an int. A num is refused even if its value is whole:

{{diagnostic:book_repeat_needs_int}}

## `repeat until`

When you do not know the number of passes in advance, loop on a condition.

{{example:book_repeat_until}}

Two things about `repeat until` are easy to get backwards.

**The loop runs while the condition is false.** `until` gives the condition for
*stopping*. `repeat until countdown == 0` keeps going as long as `countdown` is
not zero. If you are used to `while` loops, this is the opposite sense.

**The condition is tested before each pass, including the first.** If it is
already true, the body never runs. The second loop in the listing shows this:
`laps` is still zero afterwards.

For the loop to end, something in the body has to move the condition toward
true. In the third loop, `value` is halved on every pass, so sooner or later
it reaches 1.

### A loop with no end

Sometimes the natural place to stop is in the middle of the body. Then write a
condition that is never true, and leave with `break`:

{{example:book_loop_forever}}

`repeat until false` loops forever by itself. The `if` inside decides when to
stop. This is useful when the decision depends on something the body has just
done, and you saw it in Chapter 2, where the game loop was left from the
middle when the input ran out.

## `training arc`

A loop that depends on a condition can fail to end. If the body never makes
the condition true, the program hangs. FREAK has a loop that rules this out.

{{example:book_training_arc}}

A `training arc` is a `repeat until` with a limit. After `max` you give the
largest number of passes, called sessions, that the loop may make. The loop
ends when the condition becomes true or when the sessions are used up,
whichever happens first.

In the first loop the condition wins: `power` reaches 100 on the fifth session
and the loop stops with three sessions unused. In the second the limit wins:
the condition would need more than a thousand sessions and the loop is allowed
four.

Like `repeat until`, the condition is tested before each session. The limit
can be any int expression.

After a `training arc` you often want to know which of the two ended it. Test
the condition again:

{{example:book_collatz}}

`collatz_steps` follows a famous rule: halve an even number, triple an odd one
and add one, and count how many steps it takes to arrive at 1. Nobody has
proved that every starting number gets there, so a plain `repeat until n == 1`
would be a loop with no guarantee. The `training arc` gives it one. If a
thousand sessions pass without reaching 1, the loop ends anyway, the test after
it sees that `n` is not 1, and the task gives back -1 to say that it gave up.

Use a `training arc` whenever a loop's end depends on something you cannot
fully control: a search that might not converge, a retry that might never
succeed, input that might never be valid.

## `for each`

The last loop visits the elements of a list, one after another. Lists are the
subject of a chapter in Part II. For now it is enough to know that square
brackets around values separated by commas make one.

{{example:book_for_each}}

After `for each` comes a name, then `in`, then the list. On each pass the name
holds the next element. It exists only inside the body, like any pilot declared
in a block.

`for each` gives you the element and not its position. When you need both,
count alongside the loop, as the second loop in the listing does.

The thing after `in` has to be a list. A word is not a list of its letters:

{{diagnostic:book_for_each_word}}

## `break` and `continue`

Two statements change the course of any loop from inside its body.

{{example:book_break_continue}}

`break` ends the loop. Execution carries on with the first statement after it.

`continue` ends the current pass. In a `repeat ... times` loop the next pass
begins; in a `repeat until` or a `training arc` the condition is tested again;
in a `for each` the loop moves to the next element.

When loops are nested, `break` and `continue` act on the innermost loop that
contains them. The second half of the listing prints a triangle: the inner
loop is cut short by `break` when `column` passes `row`, and the outer loop
carries on to the next row. There is no way to break out of two loops at once.
If you need to, put the loops in a task and use `give back`, which leaves the
whole task from any depth.

Be careful with `continue` in a loop that keeps its own counter. If the
counter is increased at the bottom of the body, `continue` skips the increase.
In the listing, `n += 1` is the first statement of the body for exactly this
reason.

## Putting it together

Here is a small program that uses a counted loop, a task that decides with
`if`, and the conversion from Chapter 3.

{{example:book_fizzbuzz}}

`label` tests the most specific case first. A multiple of 15 is also a
multiple of 3 and of 5, so if those tests came first, `FizzBuzz` would never be
given back. Order matters in a chain of tests, as it did at the start of this
chapter.

The task gives back a word in every case, so the number has to be converted
with `to_word()`. All four `give back` statements must agree on the type.

## In V4

At the pinned commit V4 runs `if`, `when` on ints, `repeat ... times`, `repeat
until`, `break` and `continue`. These two listings give the same results on
both compilers:

{{v4:loops}}

{{v4:when_int}}

It checks conditions as strictly as V3:

{{v4:if_needs_bool}}

The rest of this section is what does not match.

**A chain in which every branch gives back does not build.** This is the shape
of `status` in this chapter's first listing: an `if`, its `else if` branches
and an `else`, each ending in `give back`.

{{v4:else_if_give_back}}

The message comes from inside the compiler, and it is a defect in this commit,
not a rule of the language. Until it is fixed, let the last case follow the
chain instead of sitting in an `else`:

{{v4:else_if_trailing}}

**An arm after `_` is an error.** V3 accepts a `when` whose catch-all comes
first and never runs the arms below it. V4 refuses the program:

{{v4:when_default_first}}

The first line is the useful one. The second is the compiler tripping over the
same arm again.

**`for each` is understood and cannot be built yet.** V4 reads the loop and
checks it. The stage that generates code has no lists yet:

{{v4:for_each}}

**The session limit of a `training arc` is not enforced.**

{{v4:training_arc_cap}}

> [!warn]
> This is the serious one, because nothing reports it. V3 stops
> this loop after three sessions and gives 3. At the pinned commit V4 checks
> that the limit is a number and then builds an ordinary condition loop, which
> runs until `drills` exceeds 10. A `training arc` whose condition can never
> become true does not end in this V4 commit. That is the one situation the
> loop exists to prevent.

**V4 has `with growth`.** The specification lets a `training arc` heading end
with `with growth`, which asks the compiler to verify that the body really does
change the pilot named in the condition. V3 does not accept it. This V4 commit
does:

{{v4:with_growth}}

And it refuses a loop whose body cannot make progress:

{{v4:with_growth_stalled}}

The name in that message, Yuuko, is one of the voices the specification gives
to the compiler's diagnostics. Part VII covers them.

## Planned

> [!planned]
> In the specification, `when` is much more than a comparison with literals.
> Its arms are *patterns* that can take a value apart: match one variant of a
> type with several forms and name the fields inside it, in one step. The
> compiler is also to check that the arms cover every possibility. That depends
> on variants, which V3 does not have. Part VII covers both.

> [!planned]
> The specification lets `for each` deliver the position along with the
> element, written `for each (i, item) in list.enumerate()`. Until a compiler
> has it, count with a `pilot mut`.

## Summary

`if` chooses on a condition, which must be a bool. `else if` and `else` extend
it, and the first true branch wins. `when` chooses by comparing one value with
literal arms; put `_` last to catch everything else. Both are statements, not
values.

There are four loops. `repeat N times` runs a fixed number of passes, counted
once at the start. `repeat until` runs while its condition is false, testing
before each pass. `training arc` is the same with a compulsory limit on the
number of passes, so it always ends. `for each` visits each element of a list.

`break` leaves the innermost loop and `continue` skips to its next pass.

That completes the core of the language. With pilots, tasks and control flow
you can write any computation. What you cannot do yet is hold more than one
value at a time, or describe data of your own. Part II begins with the type you
have used most and understood least: the word.
