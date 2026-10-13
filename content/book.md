# The Freak Book

> Learn FREAK from the first program to the compiler's insides, with every listing compiled and run before it was printed.

This is a book you read in order. It starts by installing the compiler and
printing one line, and it ends inside the compiler that printed it. Along the
way it teaches the language that ships today, shows where the next compiler
already behaves differently, and marks clearly the parts of FREAK that exist
only on paper so far.

If you want to look something up instead, the reference pages in the sidebar
are organised by topic. This book is organised by what you need to know next.

{{verified-summary}}

{{v4-snapshot}}

## Three kinds of statement

FREAK has two compilers and one specification, and they do not agree yet. The
book never blurs them.

| Mark | Means | Checked against |
|---|---|---|
| Ordinary text and listings | It works in **V3**, the compiler you can install | The released V3 compiler: each listing was built, run, and its output compared |
| **In V4** sections and boxes | The next compiler, **V4**, behaves this way | One pinned development commit of V4, named on every page |
| **Planned** boxes | The specification describes it; no compiler runs it yet | The specification only. Treat it as a plan, not a promise |

[The introduction](book-introduction.html) explains each of these, and how the
checking works.

## Part I: First sortie

Everything you need to write small, complete programs.

- [Introduction](book-introduction.html): what FREAK is, the two compilers, and how to read this book
- [1. Getting started](book-getting-started.html): installing, checking the installation, your first program, your first project
- [2. A guessing game](book-guessing-game.html): a whole program built one step at a time
- [3. Pilots, values and types](book-pilots-and-types.html): names, numbers, truth values, and the rules that connect them
- [4. Tasks](book-tasks.html): defining work, passing values in, giving values back
- [5. Control flow](book-control-flow.html): choosing with `if` and `when`, repeating with counting, conditional and list loops

## Still to be written

The remaining parts are planned and listed here so you can see where the book
is going. Their chapters appear in the sidebar as they are finished.

| Part | Chapters |
|---|---|
| II. Working with data | Words · Shapes · Methods and `impl` · Lists · Legacy arrays · Bytes |
| III. Ownership | What ownership is · The strict borrow checker in V3 · Meiya, the V4 borrow checker |
| IV. Building programs | Failure without `result` · Program structure · A tour of the standard library · Input, output and the terminal · Networking · Hangar · Calling C |
| V. Projects | A command-line tool · A squadron roster · A line server |
| VI. The anime layer | Narrative syntax you can run · The audit suite |
| VII. The language ahead | Optional and fallible values · Variants and patterns · Doctrines and generics · Closures and iterators · Collections · Borrowing in full · Concurrency · The advanced types · Modules and visibility · Build modes, voices and tests |
| VIII. Inside the compilers | How V3 works · How V4 works · Reading diagnostics · Contributing |
| Appendices | Reserved words · Operators · Command line · Types and conversions · Grammar · Glossary · V3 to V4 differences · Feature status · How this book is checked |
