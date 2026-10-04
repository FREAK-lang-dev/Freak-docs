# Introduction

> What FREAK is, why there are two compilers, and how this book tells you which statements have been checked.

Welcome to *The Freak Book*. FREAK is a compiled, statically typed programming
language. You write a `.fk` file, the compiler checks it and turns it into a
native program, and that program runs on its own with nothing else installed.

It is also a language with a sense of humour about itself. A variable is a
`pilot`. A function is a `task`. A function does not return, it will
`give back`. The names come from mecha anime and visual novels, and the
compiler signs off every build with a quotation. Underneath the vocabulary is
an ordinary, strict language: types are checked before anything runs, there is
no hidden conversion between a number and a piece of text, and a task that
promises a value has to deliver one on every path.

This book teaches that language from the beginning.

## Who this book is for

You should be comfortable in a terminal: changing directory, running a command,
editing a text file. It helps to have written a little code in any language,
because the book does not stop to explain what a variable or a loop is for. It
does explain exactly how FREAK's versions of them behave, including the places
where they differ from what you may expect.

You do not need to know C, LLVM, or anything about compilers. The last part of
the book explains how the compilers work, for readers who want that.

## One language, two compilers, one specification

Three things carry the name FREAK, and it matters which one you are talking to.

**V3** is the compiler you can install. It is written in FREAK and compiles
itself. Every release so far, including the current one, is V3. When this book
says something works, it means it works in V3.

**V4** is the next compiler, being built beside V3 in the same repository. Its
project name is Maverick. It is a new design. V3 compiles a program from start
to finish in one go. V4 is built from separate stages that each record what
they learned, so that an editor can ask questions about your code while you
type. V4 has no release yet. It already compiles and runs small programs, and
it already differs from V3 in ways you will meet in the first chapter.

**The specification** is a document in the compiler repository,
`freak-full-bible.md`, which everyone calls the bible. It describes the whole
language as it is meant to be. Neither compiler implements all of it. V3
implements a small core. V4 understands much more of it than it can run yet.

> [!note]
> The released V3 compiler prints the name Maverick too: `freak --version`
> answers `freak 0.14.2 (Maverick)`. That overlap is historical. In this book
> "V3" always means the compiler you install, and "V4" always means the new one
> under development.

## How the book marks what is real

A book about a language that is still being built could easily describe three
different languages at once without telling you. This one separates them, in
the same way on every page.

### Ordinary text is V3, and it has been run

Outside the sections and boxes described below, everything you read describes
the released V3 compiler. Listings are not typed into the page. Each one is a
real file that was compiled with the released compiler and run, and whose
output was compared with what the book says it prints. A listing looks like
this:

{{example:book_hello}}

The file name, the two badges and the output all come from that run. If a
later release changes what the program prints, this page fails its check and
has to be corrected before it can be published again.

The same applies to mistakes. Much of learning a language is learning what its
compiler says when you get something wrong, so the book shows real rejections.
A program that must not compile is checked too: the compiler has to refuse it,
for the reason the book gives. What you see is the whole message it printed.

{{diagnostic:book_unknown_pilot}}

Now and then you will see a short fragment of code with a line above it saying
*Illustrative snippet; not independently verified.* Those are there to show a
shape or name a piece of syntax. They are not claims that a complete program
runs.

### "In V4" sections are one commit of V4

V4 changes quickly. A sentence about it is only true of the commit it was
checked against, so the book pins exactly one and says which. Each chapter
keeps what it has to say about V4 together, under a heading *In V4* near its
end. A V4 listing carries the pinned commit in its badge:

{{v4:hello}}

When V4 rejects a program, the listing shows the diagnostic V4 printed. When V4
has not caught up with V3 yet, the section says so plainly. Read every V4
statement as "at this commit", never as "in the finished V4".

> [!maverick]
> Now and then a V4 difference is worth a mention in the middle of a chapter.
> It appears in a box like this one, and is backed by a V4 listing in the same
> chapter.

### "Planned" boxes are the specification

> [!planned]
> A box like this one describes something the bible specifies and no compiler
> runs today. It tells you where the language is heading. Nothing in a Planned
> box has been executed, and details can change before it is built.

## What you can rely on

The book's examples were checked on Linux x64. FREAK also publishes builds for
Linux arm64, macOS on Apple silicon, and Windows x64. File names and
installation paths differ between them, and the book points out the differences
it knows about. It does not claim to have run every listing on every platform.

Two things the checks cannot tell you: whether an explanation is clear, and
whether a design is good. Where V3 does something surprising, the book says so
and shows it, instead of presenting it as intended or pretending it is not
there.

## How to read it

Read Part I in order. Chapter 1 installs the compiler and runs a first program.
Chapter 2 builds a small game from start to finish, using things the later
chapters then explain properly. Chapters 3, 4 and 5 cover values, tasks and
control flow, which is enough to write real programs.

After that the parts are more independent. [The contents page](book.html) lists
them all.

Type the examples in yourself. Change them. Break them on purpose and read what
the compiler says. The diagnostics in this book were collected the same way.

## The vocabulary

FREAK renames a handful of everyday programming terms. You will absorb them
quickly, and this table is here for the first few chapters.

| FREAK says | You may know it as | Explained in |
|---|---|---|
| `pilot` | a variable | Chapter 3 |
| `fixed pilot` | a constant | Chapter 3 |
| `task` | a function | Chapter 4 |
| `give back` | `return` | Chapter 4 |
| `say` | print a line | Chapter 1 |
| `ask` | read a line of input | Chapter 2 |
| `word` | a string | Chapter 3, and Part II |
| `num` | a floating-point number | Chapter 3 |
| `int` | an integer | Chapter 3 |
| `when` | `switch` or `match` | Chapter 5 |
| `training arc` | a loop that must end | Chapter 5 |
| `shape` | a struct or record | Part II |
| Hangar | the package manager | Chapter 1, and Part IV |
| the bible | the language specification | this page |

## A word on how FREAK is made

The compiler repository states it openly, and so will this book: parts of
FREAK, including code, diagnostics, tests and documentation, were produced with
AI coding assistance, working with human maintainers who reviewed and directed
the work and take responsibility for it. This book was written the same way.
That is one reason every listing in it is executed rather than trusted.

Turn to [Chapter 1](book-getting-started.html) to install the compiler.
