# Pilots, values and types

> How to name a value, what kinds of value there are, and the strict rules that keep them from being confused with one another.

Chapter 2 used pilots, numbers, words and truth values without stopping to
explain them. This chapter goes back over each one. It covers:

- declaring pilots, and what `mut` and `fixed` do
- where a pilot can be seen, and for how long
- the words you cannot use as names
- the four basic types: `int`, `num`, `bool` and `word`
- why FREAK never converts between types unless you ask

## Pilots

A pilot is a name for a value. You create one with `pilot`, a name, an equals
sign, and the value it starts with.

{{example:book_pilots}}

Every pilot has a *type*, which says what kind of value it holds. The first
four pilots here hold a word, an int, a num and a bool.

You can let the compiler work the type out from the starting value, as
`callsign`, `fuel` and `cleared` do. Or you can write it after the name with a
colon, as `sorties: int` does. The two forms mean the same thing when they
agree. Writing the type is useful as a note to the reader, and as a check: if
the value is not of the type you wrote, the program does not build.

{{diagnostic:book_wrong_type}}

A pilot must be given a value when it is created. There is no way to declare
one now and fill it in later:

{{diagnostic:book_no_initial_value}}

The message is indirect. After `pilot fuel: int` the compiler expected `=` and
a value. It found the next line instead, and reports that.

### A pilot keeps its type

Once a pilot holds an int, it holds ints for as long as it exists. You can give
it a different int. You cannot give it a word.

{{diagnostic:book_assign_wrong_type}}

### Names

A name is made of letters, digits and underscores, and does not start with a
digit. Only the unaccented letters `a` to `z` and `A` to `Z` are allowed.

FREAK code follows two conventions. Ordinary pilots and tasks are written in
lowercase with underscores between words: `secret_number`, `sorties_flown`.
Values that are fixed for the whole program are written in capitals:
`MAX_SORTIES`.

## Changing a pilot

There are three ways to declare a pilot, and they differ in what you intend to
do with it afterwards.

| Declaration | Intent |
|---|---|
| `pilot x = 1` | An ordinary pilot |
| `pilot mut x = 1` | A pilot whose value will be changed |
| `fixed pilot x = 1` | A pilot whose value must never change |

Assignment uses `=`. For arithmetic on the pilot's own value there are
shorthand forms: `x += 5` means `x = x + 5`, and `-=`, `*=`, `/=` and `%=`
work the same way.

Now the part that needs care. How strictly these three forms are enforced
depends on how you build.

**By default, V3 does not enforce them for simple values.** A plain `pilot`
holding a number can be reassigned, and so can a `fixed pilot`. The words `mut`
and `fixed` are accepted and, for numbers, words and bools, ignored.

**With `--strict-borrow`, V3 enforces them.** That flag turns on V3's ownership
checker, which Part III is about. Under it, only a `pilot mut` may be
reassigned:

{{diagnostic:book_reassign_strict}}

The same message is given for assigning to a `fixed pilot`.

You turn it on by adding the flag to a build:

```sh
freak build main.fk --strict-borrow
```

So write the declarations as if they were always enforced. Use `pilot mut` for
anything you assign to again, `fixed pilot` for values that must not change,
and plain `pilot` for everything else. Your code then says what it means, and
the strict mode will have no complaint about its assignments. The strict mode
has a second set of rules, about values that are handed from one place to
another, and those are Part III's subject.

> [!note]
> One kind of value is checked even without the flag. A list must be declared
> `pilot mut` before you can add to it or change its elements. Part II covers
> lists.

## Scope

A pilot exists from the line that declares it to the end of the block it was
declared in. A block is whatever sits between a pair of braces: the body of a
task, of an `if`, of a loop.

{{example:book_scope}}

`wing` is created inside the `if` block and ends with it. Using it afterwards
is an error, and the compiler treats it like any other name it has never heard
of:

{{diagnostic:book_out_of_scope}}

### Shadowing

The example also declares a second `squadron` inside the block. This is
allowed. The inner pilot is a new one that happens to have the same name, and
while it exists it hides the outer one. When the block ends, the inner pilot is
gone and the name means the outer pilot again, whose value was never touched.

That only works across blocks. Declaring the same name twice in the *same*
block is an error:

{{diagnostic:book_duplicate_pilot}}

If you meant to change the existing pilot, drop the second `pilot` and assign.

## Pilots outside tasks

A pilot can be declared at the top level of a file, outside every task. It is
then visible in all of them.

{{example:book_constants}}

This is the right place for values the whole program agrees on: limits, names,
settings. Declare them `fixed pilot` and name them in capitals.

A top-level pilot can also be changed by the tasks that see it:

{{example:book_shared_pilot}}

Use that sparingly. A value that any task may change is hard to reason about,
because to know what it holds you have to know everything that ran before.
Passing values into tasks and giving results back, the subject of Chapter 4,
keeps programs easier to follow.

## Reserved words

Some words belong to the language and cannot be used as names. In most
languages that list is short and obvious. In FREAK it is longer than you would
guess, because it includes words the language has reserved for features that
are not built yet.

These 54 words are reserved in V3:

```text
pilot   fixed    task       say      shape    impl      doctrine
launch  use      as         in       lend     mut       move
copy    break    continue   if       else     when      repeat
times   until    done       for      each     check     result
got     nobody   some       ok       err      sessions  max
foreshadow  payoff   route   sadly   deus_ex_machina    isekai
eventually  and      or      not     nakama   tsundere  extern

true    false    yes    no    hai    iie
```

Several of them are words you will reach for naturally: `max`, `result`, `ok`,
`check`, `done`, `times`, `in`, `use`, `copy`, `move`, `route`, `launch`. This
book's own examples ran into it. A task that starts a sortie wanted to be
called `launch`:

{{diagnostic:book_reserved_task_name}}

When you see `expected an identifier ... found` followed by a word you thought
was a perfectly good name, this is why. Pick another: `limit` for `max`,
`outcome` for `result`, `ready` for `ok`, `scramble` for `launch`.

### Words that are not reserved

In one respect the list is shorter than you might guess. Several words the
language uses constantly are missing from it: `give`, `back`, `training`,
`arc`, `ask`, and the type names `int`, `num`, `bool` and `word`. V3 recognises
those by where they appear, so it accepts them as names too:

{{example:book_contextual_words}}

That listing builds, and `give back give` is reason enough never to write it.
There is a trap as well. V3 joins `give` and `back` into one keyword wherever
the two words follow each other, even across the end of a line:

{{diagnostic:book_give_back_trap}}

Line 4 ends with the pilot `give` and line 5 starts with the pilot `back`, and
the compiler reads the pair as `give back`. Treat every word the language uses
as reserved, whether or not the compiler insists.

### Capital letters do not help

V3 reserves these words in every combination of capital and small letters.
`Max`, `MAX` and `max` are all refused as names:

{{diagnostic:book_keyword_name}}

> [!warn]
> The reservation covers every spelling, but a single-word *keyword* works
> only in lowercase. `Pilot x = 1` is not a declaration and `If` does not start
> a condition; both are syntax errors. The truth literals are the dangerous
> exception, because a capitalised one is accepted and silently means false.

{{example:book_keyword_case}}

The two-word keywords are treated differently. V3 accepts `give back`, `for
each` and `training arc` in any letter case:

{{example:book_two_word_case}}

Do not rely on that. Write every keyword in lowercase and none of this touches
you.

## The basic types

V3 has four types of simple value.

| Type | Holds | Example values |
|---|---|---|
| `int` | A whole number | `0`, `42`, `-7` |
| `num` | A number with a fractional part | `2.5`, `0.75`, `-3.0` |
| `bool` | A truth value | `true`, `false` |
| `word` | Text | `"Valkyrie-1"`, `""` |

There is a fifth name, `void`, for a task that gives nothing back. It is not a
type of value: you cannot have a `void` pilot. Chapter 4 covers it.

Beyond these, V3 has lists, an older kind of array, a byte buffer, and the
shapes you define yourself. Those are Part II.

### `int`

An `int` is a whole number stored in 64 bits, with a sign. It ranges from
-9,223,372,036,854,775,808 to 9,223,372,036,854,775,807. A number written
without a decimal point is an int.

{{example:book_int}}

Four things in that listing are worth stating as rules.

**Dividing two ints gives an int.** The fractional part is dropped, so `7 / 2`
is `3`. The result is rounded toward zero, which matters for negative numbers:
`-7 / 2` is `-3`, where rounding downward would give `-4`.

**`%` gives the remainder** of that division, and takes the sign of the left
side: `-7 % 2` is `-1`.

**Multiplication, division and remainder are done before addition and
subtraction.** Parentheses change the order.

**Arithmetic that goes past the largest int wraps around** to the smallest,
with no error and no warning. The same happens to a number literal that is too
large to fit. If your numbers can become that large, it is up to you to check
before they do.

> [!warn]
> Dividing an int by zero is not checked either. Depending on the machine and
> on how the zero got there, the operating system stops the program on the
> spot or the program carries on with a meaningless value. Neither produces a
> FREAK message. Test the divisor before you divide by anything that could be
> zero.

Ints are written in decimal only. There is no hexadecimal form, no separator
for grouping digits, and no exponent. The compiler does not say so directly.
It reads `0xFF` as the number `0` followed by a name, and reports `unknown
binding 'xFF'`. If you see an unknown binding that looks like the tail of a
number, this is the cause.

### `num`

A `num` is a floating-point number, stored in 64 bits. A number written with a
decimal point is a num. At least one digit must come before the point: `0.5`,
never `.5`.

{{example:book_num}}

`say` prints a num with up to ten significant digits, and leaves off a
fractional part that is zero. So `5.0` prints as `5`, and one third prints as
`0.3333333333`. Very large and very small values are printed in scientific
notation: `1.23456789e+11` is 1.23456789 times ten to the eleventh.

Ten digits is what is *printed*. The value itself is kept more precisely than
that, and this is why `0.1 + 0.2` prints as `0.3` and still is not equal to
`0.3`. Neither 0.1 nor 0.2 can be stored exactly in binary, and their sum
differs from the stored 0.3 somewhere past the sixteenth digit. This is true
of floating-point numbers in every language. The rule that follows from it:
do not test nums for exact equality. Test whether they are close enough.

When an operation has an int on one side and a num on the other, the int is
treated as a num and the result is a num. That is why `7 / 2.0` is `3.5`.

The remainder operator is for ints only:

{{diagnostic:book_remainder_num}}

### `bool`

A `bool` is one of two values, `true` or `false`. Comparisons produce bools,
and `if` and the loops consume them.

{{example:book_bool}}

The comparison operators are `==` (equal), `!=` (not equal), `<`, `>`, `<=`
and `>=`. Bools combine with three operators written as words:

| Operator | True when |
|---|---|
| `a and b` | both are true |
| `a or b` | at least one is true |
| `not a` | `a` is false |

`not` is applied first, then `and`, then `or`. When in doubt, use parentheses;
the reader will thank you even where the compiler did not need them.

`and` and `or` evaluate their right side only when they have to. In the
listing, `announce("fuel", false) and ...` already knows the answer is false
after its left side, so the right side never runs and `checking weapons` is
never printed. This is called short-circuit evaluation, and you can rely on it.

FREAK has three spellings for each truth value: `true`, `yes` and `hai` all
mean true, and `false`, `no` and `iie` all mean false. They are the same two
values. `say` prints `true` or `false` whichever you wrote.

### `word`

A `word` is a piece of text of any length, written in double quotes. It is
what other languages call a string.

{{example:book_words_intro}}

That is enough about words to read the next two chapters. Words have a chapter
of their own in Part II, which covers their methods, the exact rules of
interpolation, and how to take them apart.

## Types do not mix by themselves

FREAK will not guess what you mean when two types meet. Joining a word and a
number is an error:

{{diagnostic:book_word_plus_int}}

So is comparing them:

{{diagnostic:book_compare_int_word}}

Read the messages closely, because you will see this form often. `operator
'+' does not accept word and int` names the operator and the types it found on
its left and right. The fix is always the same: convert one side so that both
are the same type.

A num cannot be stored in an int pilot either, because that would lose the
fractional part without your asking:

{{diagnostic:book_num_into_int}}

There is exactly one conversion FREAK performs for you. Where a num is
expected, an int is accepted and converted, since no information is lost. You
saw it in `7 / 2.0`, and it also applies when you give an int to a pilot or a
task parameter declared as `num`.

## Converting between types

Every other conversion is written out as a method call on the value.

{{example:book_conversions}}

| From | To | Write | Notes |
|---|---|---|---|
| `int` | `num` | `n.to_num()` | Also happens by itself where a num is expected |
| `int` | `word` | `n.to_word()` | |
| `num` | `int` | `x.to_int()` | Drops the fraction: `3.75` becomes `3`, `-3.75` becomes `-3` |
| `num` | `word` | `x.to_word()` | Formatted the way `say` prints it |
| `bool` | `word` | `b.to_word()` | `"true"` or `"false"` |
| `word` | `int` | `w.parse_int()` | Checked; see Chapter 2 |
| `word` | `num` | `w.parse_num()` | Checked the same way |
| `word` | `int` | `w.to_int()` | Unchecked: reads the digits at the start of the word, and gives `0` if there are none |
| `word` | `num` | `w.to_num()` | Unchecked in the same way |

In practice you need the word conversions less often than this table suggests.
`say` prints ints, nums and bools directly, and interpolation puts any of them
inside a word. Reach for `to_word()` when you are building a word with `+`.

## In V4

V4 agrees with V3 on the basics, and the following all hold at the pinned
commit: ints and nums are 64 bits, int division drops the fraction, and mixed
arithmetic produces a num.

{{v4:int_and_num}}

Int arithmetic wraps at the limits, as in V3:

{{v4:overflow_wraps}}

V4 also refuses a bool in an int pilot, and a duplicate name in one block:

{{v4:wrong_type}}

{{v4:duplicate_local}}

The rest of this section is what differs.

**Keywords are reserved in lowercase only.** V4 matches a keyword by its exact
lowercase spelling. The capitalised names that V3 refuses are ordinary names in
V4:

{{v4:keyword_case}}

The truth literals are the exception, and here V4 corrects V3. A capitalised
truth literal is still a truth literal, so it cannot be a name, and it means
what it says:

{{v4:truth_literal_case}}

V3 fails the first two tests, because it reads `TRUE` and `Yes` as false, and
gives 4 for this program where V4 gives 7.

**Every pilot can be reassigned, and `mut` is not accepted.** Chapter 2 showed
`pilot mut` being rejected. Assignment to a plain pilot works:

{{v4:reassign}}

That much agrees with the specification's section on pilots, which says they
can be reassigned by default. The same section says a `fixed pilot` cannot be,
and this commit does not enforce that yet:

{{v4:fixed_reassigned}}

**A num is accepted where an int is required.** V3 refuses to store a num in an
int pilot, to assign one, or to pass one to an int parameter. This commit
accepts all three and drops the fraction without a message:

{{v4:num_into_int}}

**The conversion methods are missing.** `to_num()`, `to_int()` and the others
in this chapter's table are not there yet:

{{v4:conversion_methods}}

**Pilots cannot be declared outside a task.** A plain top-level pilot is a
syntax error. The specification allows only declarations and constants at the
top level:

{{v4:toplevel_pilot}}

A top-level `fixed pilot` is such a constant. This commit reads it and cannot
build it yet:

{{v4:toplevel_fixed}}

**A hexadecimal literal is misread silently.** V3 reports `0xFF` as an unknown
binding. This commit takes the leading `0` as the value and carries on:

{{v4:hex_literal}}

**A misspelled name is not reported well yet.** V4 notices that something is
wrong only when it tries to generate code, and says so in terms of types
instead of naming the pilot:

{{v4:unknown_name}}

**An inner block cannot shadow.** A second `pilot` with the same name inside a
nested block is reported as a duplicate, where V3 allows it:

{{v4:shadow_inner}}

**V4 has more basic types.** The specification defines several that V3 lacks,
and this commit already builds programs that use four of them. Three have a
literal suffix, and a `char` is written in single quotes:

{{v4:numeric_types}}

`uint` is an unsigned 64-bit whole number, `tiny` is a single byte, `float` is
an explicitly named 64-bit float, and `char` is a single character. A fifth
type, `float32`, is accepted too.

## Planned

> [!planned]
> The specification defines `big`, a whole number of any size, which cannot
> overflow, with literals written like `999b`. V3 does not have it, and the
> pinned V4 commit recognises the type and cannot build it yet.

{{v4:big_type}}

> [!planned]
> The specification describes `num` as the default numeric type, with whole
> literals narrowing to `int` where an int is required. V3 does it the other
> way round: a literal without a decimal point is an `int`.

> [!planned]
> Two ways of grouping values without declaring a shape are specified and not
> in V3: tuples, written `(42, "hello")`, and fixed-size arrays, written
> `[int; 4]`.

## Summary

A pilot is a named value with a type that never changes. The type is inferred
from the starting value or written after a colon. Declare a pilot `mut` if you
will reassign it and `fixed` if it must not change; V3 enforces this under
`--strict-borrow`, and always for lists.

A pilot lives until the end of its block. An inner block may shadow an outer
name; the same block may not declare a name twice. Fifty-four words are
reserved in any letter case, and single-word keywords work only in lowercase.

There are four basic types. `int` is a 64-bit whole number whose division
truncates and whose arithmetic wraps. `num` is a 64-bit floating-point number,
printed to ten significant digits. `bool` is true or false, combined with
`and`, `or` and `not`. `word` is text.

Types never mix on their own, with one exception: an int becomes a num where a
num is expected. Everything else is converted by calling a method.

[Chapter 4](book-tasks.html) is about tasks: how to define them, pass values
in, and give values back.
