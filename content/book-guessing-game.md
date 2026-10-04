# A guessing game

> Build a complete program, one small step at a time: it picks a number, you guess, it tells you higher or lower.

This chapter does not explain features in order. It builds something, and
introduces each feature at the moment the program needs it. You will use
pilots, input, conversion from text to numbers, comparison, and loops. The
chapters after this one explain each of them thoroughly; here the aim is to see
them working together.

The game is a classic. The program picks a secret number from 1 to 100. You
type a guess. The program answers "too low" or "too high", and you guess again
until you find it. A finished session looks like this:

```text
Guess the number! It is between 1 and 100.
Your guess: 50
Too high.
Your guess: abc
'abc' is not a whole number. Try again.
Your guess: 25
Too low.
Your guess: 37
Too low.
Your guess: 42
You got it in 4 guesses!
```

## Setting up

Create a project for the game and move into it:

```sh
freak init guess
cd guess
```

Open `main.fk` and delete what is there. Each step below replaces the file's
contents. Run each one with `freak run main.fk` and see it work before going
on.

## Step 1: asking for a guess

Start with the part that talks to the player: print a greeting, ask for a
guess, and repeat it back.

{{example:book_guess_input}}

There are two new things here.

```fk
    pilot guess = ask("Your guess: ")
```

`pilot` creates a named value. FREAK calls it a pilot, where other languages
say variable. The name is `guess`, and the value comes from the right of the
`=` sign.

`ask` prints its prompt, waits for the player to type a line and press Enter,
and gives back what was typed. The prompt is not followed by a new line, so the
player types on the same line as the question. What comes back is a *word*,
FREAK's type for text. So `guess` holds a word.

```fk
    say "You guessed: {guess}"
```

Inside a word, a name in braces is replaced by that pilot's value. This is
called interpolation, and it is the usual way to mix values into output.

Look at the boxes under the listing. *Typed at the prompts* is the input the
program was given when this book checked it. *Program output* is what the
program itself printed. On your screen you would see `Your guess: 50` and then
`You guessed: 50` on the next line. In the output box they run together,
because the `50` and the Enter that followed it were typed by the player. They
were never printed by the program, so they are not in its output.

## Step 2: from a word to a number

The player typed `50`, but the program has the word `"50"`: two characters, a
five and a zero. You cannot compare a word with a number. FREAK will not
convert between them unless you ask, so ask.

{{example:book_guess_parse}}

Two method calls are chained on the first new line:

```fk
    pilot guess = text.trim().parse_int()
```

A dot after a value calls a *method*, an operation that belongs to that type of
value. `text.trim()` gives back the word with spaces removed from both ends, in
case the player typed ` 50 `. Then `.parse_int()` reads that word as a whole
number. FREAK's type for whole numbers is `int`, so `guess` is now an `int`.

You never wrote a type. FREAK works out that `text` is a word and `guess` is an
int from the values they are given. The types are still there and still
checked. They are inferred.

### When the player does not type a number

The check ran this step with the input `fifty`, which is not a number, and the
program said so. This is the part that deserves attention:

```fk
    if parse_status() != 0 {
        parse_clear_status()
        say "'{text}' is not a whole number."
    } else {
```

`parse_int` always gives back an int. If the word is not a number, it gives
back `0`, and it records that the parse failed. `parse_status()` reports that
record: `0` means no parse has failed, `1` means a word was not a number, and
`2` means it was a number too large to hold. `!=` means "is not equal to".

So the pattern is: parse, then ask at once whether it worked. The record stays
set until you clear it, which is what `parse_clear_status()` is for. If you
forget to clear it, the next successful parse will still look like a failure.

> [!warn]
> There is a shorter method, `to_int()`, which also converts a word to an int.
> It is lenient: it reads as many digits as it finds at the start of the word,
> so `"12abc"` becomes `12`, and it gives back `0` when there are none. It
> records nothing, so you cannot tell `"0"` from `"zero"`. Use `parse_int()`
> for anything a person typed.

`if` runs the first block when its condition is true and the `else` block
otherwise. Chapter 5 covers it properly.

### Interpolation takes names

In the `else` block, the program doubles the guess before printing it:

```fk
        pilot doubled = guess * 2
        say "Twice your guess is {doubled}."
```

It would be shorter to write `{guess * 2}` inside the word. That does not work.
Braces interpolate a *name*: a pilot, or as Part II will show, a field of one.
They never interpolate a calculation or a call. If what is inside the braces is
not a name, the braces and their contents are printed exactly as written, with
no error. Work the value out first, give it a name, and interpolate the name.

> [!planned]
> The specification gives conversion a different shape. `"42".to_int()` would
> give back a `maybe<int>`, a value that is either a number or nothing. You
> would get the number out with `check` or `or else`, both of which make you
> say what happens when there is none. The status record is how V3 manages
> without that type. Part VII describes the planned design.

## Step 3: a secret number

The game needs a number the player cannot predict. Most languages have a
random-number library. V3 does not have one yet, so this program takes its
unpredictability from the clock.

{{example:book_guess_secret}}

`time::monotonic_ns()` gives back the number of nanoseconds on a clock that
only moves forward. The two colons separate a *namespace* from a name:
`time` is a group of built-in operations to do with clocks, and `monotonic_ns`
is one of them. You will meet `process::` shortly.

The value is large, and at the moment a person starts a program its low digits
are as good as random. Not every system's clock ticks in single nanoseconds,
though, and on one that does not, the last few digits are always zero. So the
task divides by 1000 first, which leaves microseconds, and takes its digits
from there.

`%` is the remainder operator. `micros % 100` is what is left after dividing by
100, which is always from 0 to 99. Adding 1 moves that to the range 1 to 100.

This is the first task of your own that gives something back. Its first line
says so:

```fk
task secret_number() -> int {
```

`-> int` declares that the task gives back an int, and `give back` is the
statement that does it. `main` calls the task by writing its name with
parentheses and keeps the answer in a pilot.

The listing cannot print the secret, since a different number each run could
not be checked against a fixed expected output. It checks that the number is in
range instead. `and` joins two conditions and is true when both are.

> [!warn]
> A clock is fine for a game and wrong for anything that must not be guessed.
> Do not use this technique for passwords, tokens or keys.

> [!planned]
> The specification includes a `std::random` module, with
> `random::rand_int_range(lo, hi)` for a whole number in a range and
> `random::secure()` for randomness from the operating system. Neither
> compiler has it yet.

## Step 4: comparing the guess

Now put a secret and a guess side by side. To keep this step easy to check, the
secret is fixed at 42 for the moment.

{{example:book_guess_compare}}

`<` and `>` compare two numbers. An `if` can be followed by any number of
`else if` branches and one final `else`. The conditions are tried from the top,
and the first true one wins. If the guess is neither lower nor higher than the
secret, only one possibility is left, so the last branch needs no condition.

Both `guess` and `secret` are ints. Had you forgotten to parse the guess and
tried to compare the word `text` with `secret`, the compiler would have refused
to build the program. Chapter 3 shows what it says.

## Step 5: guessing until it is right

One guess is not much of a game. The program has to keep asking. That needs a
loop, and a way to stop.

Here is the complete program. Read it once, and then go through the notes
below.

{{example:book_guess}}

### The loop

```fk
    pilot mut solved = false

    repeat until solved {
```

`repeat until` runs its block again and again, and stops when the condition
becomes true. The condition here is a pilot, `solved`, which starts out
`false`. `true` and `false` are values of the type `bool`.

When the player finds the number, the last branch of the comparison sets
`solved = true`. The loop tests the condition before each pass, finds it true,
and stops.

### `mut`

`solved` and `attempts` are declared with `pilot mut`. `mut` marks a pilot
whose value will change after it is created. `secret` never changes, so it is a
plain `pilot`.

`attempts += 1` is short for `attempts = attempts + 1`.

Chapter 3 explains exactly how strictly `mut` is enforced. For now, the habit
to form is simple: if you are going to assign to it again, write `mut`.

### `continue` and `break`

Two statements change the course of a loop from inside.

`continue` abandons the rest of the current pass and goes back to the top of
the loop. The program uses it after a guess that is not a number: there is
nothing to compare, so it asks again. Because `continue` comes before
`attempts += 1`, a mistyped guess is not counted.

`break` leaves the loop at once. The program uses it when the player gives no
guess at all. That happens when the player presses Enter on an empty line, and
also when the input ends, for instance because the program was fed from a file
that ran out. Without this check, a program reading from an exhausted input
would ask forever.

After the loop, `solved` tells the two ways of leaving apart. It is true only
if the player actually found the number.

### A secret you can choose

Look again at `secret_number`:

```fk
task secret_number() -> int {
    if process::args_count() > 1 {
        pilot chosen = process::arg(1).parse_int()
        if parse_status() == 0 { give back chosen }
        parse_clear_status()            -- not a number: fall back to the clock
    }
    pilot micros = time::monotonic_ns() / 1000
    give back micros % 100 + 1
}
```

A program can be started with arguments, extra words after its name on the
command line. `process::args_count()` says how many there are, and
`process::arg(1)` is the first one. Argument 0 is the program's own name, which
is why the count has to be greater than 1 for there to be a real argument.

If an argument is given and it is a number, the task gives it back
immediately. A `give back` ends the task on the spot, so the lines after it
run only when there was no usable argument.

Notice that the argument is parsed with the same care as the player's guesses.
The parse is checked at once, and a failure is cleared. Without those two
lines, starting the game with an argument that is not a number would leave the
failure recorded, and the player's first perfectly good guess would be reported
as not a number.

This is not a cheat mode for its own sake. A program whose behaviour depends on
the clock cannot be tested, because you cannot say in advance what it should
print. Giving the secret from outside makes the game repeatable. The listing
above was checked exactly that way: started with the argument `42`, and fed
five lines of input.

## Playing it

`freak run` takes no arguments for your program; it reports an extra word as
an unknown flag. To play with a chosen secret, build once and run the program
yourself:

```sh
freak build main.fk
./main 42
```

To play properly, leave the argument off:

```sh
./main
```

Try the edges. Type a word instead of a number. Type a number with spaces
around it. Press Enter on an empty line. The program has an answer for each.

## In V4

At the commit this book is pinned to, V4 cannot build this game, for two
reasons. It does not know `ask`, and reports it the way it reports any name it
cannot place:

{{v4:ask}}

And it cannot yet hold a word in a pilot, so there would be nowhere to keep a
guess:

{{v4:word_pilot}}

What V4 does have is everything the game *decides* with: ints, comparison,
tasks, and loops.

So here is the game's logic with the conversation removed. The program plays
against itself. It guesses the middle of the range, uses the verdict to halve
the range, and counts its guesses. With nothing to print the count with, it
gives the count back from `main`, where it becomes the exit code.

{{v4:guess_logic}}

Seven guesses to find 42: it tries 50, 25, 37, 43, 40, 41 and then 42.

Two details differ from the V3 listing. `main` declares `-> int`, as Chapter 1
explained. And the pilots that change are declared without `mut`. At this
commit V4 does not accept `pilot mut`, and lets every pilot be reassigned:

{{v4:pilot_mut}}

V3 in its default mode builds this V4 listing as it stands. V3's strict mode
does not. It wants `mut` on a pilot that changes, and this V4 commit rejects
the word. It also objects to the way `guess` is passed to a task, for a reason
that belongs to Part III. So this is the first program that cannot be written
one way for both.

The specification does not settle the matter. Its section on pilots says they
can be reassigned by default and that `fixed pilot` is the form that cannot.
Its notes on the borrow checker describe V3's rule, where only a `pilot mut`
can. Chapter 3 shows what each compiler does today.

## Summary

You built a complete interactive program. Along the way you used:

- `pilot` to name a value, and `pilot mut` for one that changes
- `ask` to read a line, and `say` with `{name}` interpolation to print
- methods on words: `trim()` and `parse_int()`, with `parse_status()` to learn whether the parse worked
- the types `word`, `int` and `bool`, which you wrote down only once, as a task's return type
- `if`, `else if` and `else` to choose
- `repeat until` to loop, with `continue` and `break` to steer
- a task that gives back a value, built-in operations in the `time::` and `process::` namespaces, and command-line arguments to make the program testable

Each of these was introduced quickly. The next three chapters go back over
them with care. [Chapter 3](book-pilots-and-types.html) starts with pilots and
the types of the values they hold.
