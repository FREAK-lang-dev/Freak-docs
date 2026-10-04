# Tasks

> Define a piece of work once, give it a name, pass values in, and get a value back.

A task is FREAK's function. You have written one in nearly every program so
far, `main`, and Chapter 2 added a second. This chapter covers:

- declaring a task and calling it
- parameters, and how arguments are checked against them
- giving a value back, and the rule that every path must do so
- what happens to a value you pass in
- `main`, the exit code, and what the top level of a file is for
- the pipe operator

## Declaring and calling

A task declaration has a name, a list of parameters in parentheses, and a body
in braces.

{{example:book_tasks}}

`greet` takes nothing and gives nothing back. `report` takes two *parameters*.
Each parameter is a name followed by a colon and a type, and the types are
required: unlike a pilot, a parameter has no starting value for the compiler to
infer from.

You run a task by *calling* it: its name, then the values for its parameters
in parentheses. Those values are the *arguments*. `report("Valkyrie-1", 12)`
gives the word to `callsign` and the int to `sorties`. Arguments are matched to
parameters by position, first to first and second to second.

Inside the task, a parameter behaves like a pilot that was created with the
argument's value.

## Giving a value back

`add` and `area` have something the first two tasks lack: an arrow and a type
after the parameter list.

```fk
task add(a: int, b: int) -> int {
    give back a + b
}
```

`-> int` is the task's *return type*. It promises that the task produces an
int. `give back` keeps the promise: it evaluates the expression after it, ends
the task, and hands the value to the caller.

A call to such a task is itself a value. You can store it in a pilot, print
it, or use it as an argument to another call, as `add(add(1, 2), 3)` does.

A task with no arrow gives nothing back. Its return type is `void`, and you
may write that out as `-> void` if you prefer; the meaning is the same.

### `give back` ends the task

`give back` does not have to be the last line. Wherever it runs, the task ends
there.

{{example:book_give_back}}

`rank_for` reads from top to bottom as a series of questions. The first one
that is true gives its answer back and the rest are never reached. This style,
with the special cases dealt with first and the ordinary case last, is common
in FREAK code.

`announce` shows the same idea in a task that gives nothing back. A `give
back` with no value simply leaves. Here it is used to skip an empty message.

### Every path must give back

If a task promises a value, every way through its body has to end in a `give
back`. This task forgets the case where the condition is false:

{{diagnostic:book_missing_give_back}}

`may finish without giving back word` is exact. When `sorties` is 50 or more,
the task gives back a word. Otherwise it reaches the closing brace with nothing
to give. The compiler checks this by following the structure of the body: an
`if` with an `else` is enough when both branches give back, and an `if` alone
never is.

> [!warn]
> FREAK has no implicit return. In some languages the last expression in a
> function is its value. Not here: a value on a line by itself is worked out
> and thrown away. Only `give back` returns.

### The value must be of the promised type

{{diagnostic:book_wrong_return_type}}

And a task that promises nothing cannot give back something:

{{diagnostic:book_void_gives_value}}

For the same reason, there is nothing to store from a call to a `void` task:

{{diagnostic:book_store_void}}

### Ignoring a result

The reverse is allowed. You may call a task that gives back a value and not
use it. The call is then a statement of its own, and the value is dropped.

{{example:book_statements}}

## Arguments are checked

The compiler compares every call with the task's declaration. The number of
arguments must match:

{{diagnostic:book_wrong_arg_count}}

And each argument must have its parameter's type:

{{diagnostic:book_wrong_arg_type}}

The message counts arguments from 1. `argument 2 expects int, got word` means
the second argument should have been an int and was a word.

The one automatic conversion from Chapter 3 applies here too. In the first
listing, `area(3, 2.5)` passes the int `3` to a `num` parameter, and that is
accepted. The opposite, a num where an int is expected, is an error.

## A task gets its own copy

When you pass a number, a word or a bool to a task, the task receives a copy.
Changing the parameter inside the task changes the copy. The caller's pilot is
untouched.

{{example:book_by_value}}

This is why `refuel` has to give back the new level. There is no way for it to
reach into `main` and change `fuel`.

> [!note]
> Shapes and lists, the larger values introduced in Part II, behave
> differently: a task that receives one can change the caller's copy. Part III
> explains why, and what ownership has to do with it.

## Order does not matter

A task can be called from a point in the file above its declaration. The
compiler reads all the declarations first and only then checks the bodies.

{{example:book_order}}

`main` comes first here and calls two tasks declared below it. You are free to
put the important task at the top of a file and its helpers underneath.

The same listing shows a task calling itself. `factorial(5)` needs
`factorial(4)`, which needs `factorial(3)`, and so on down to 1, where the
first line stops the descent. A task that calls itself is *recursive*, and it
must always have a case that does not, or it never ends.

`is_even` and `is_odd` call each other. That works for the same reason that
calling a task declared later works.

## `main` and the exit code

Every program reports a number to the operating system when it ends, its *exit
code*. By convention zero means success and anything else means some kind of
failure. Scripts and other programs use it to decide what to do next.

When `main` has no return type, the exit code is zero. When `main` is declared
`-> int`, the int it gives back is the exit code:

{{example:book_exit_code}}

On Linux and macOS you can see the code of the last command with `echo $?`. An
exit code is a small number. On Linux and macOS only values from 0 to 255
survive the journey to the operating system, so use it for a status, not for a
result.

## The top level is for declarations

Chapter 1 mentioned that a file with no `main` runs the statements at its top
level. Once a file has a `main`, that stops. The program starts at `main`, and
a statement written outside every task is not run at all:

{{example:book_toplevel_main}}

The top-level pilot still works, because a pilot is a declaration. The
top-level `say` is a statement, and it was silently skipped.

The rule to take from this: in a program with a `main`, put only declarations
at the top level. That means tasks, pilots, and the shapes of Part II.

Tasks themselves can only be declared at the top level. A task inside a task
is an error:

{{diagnostic:book_nested_task}}

## One namespace

All the tasks in a program share one set of names. Two tasks cannot have the
same name, even with different parameters.

That set includes more than your own file. Chapter 1 showed that the standard
library is placed in front of your program before it is compiled. Its tasks
are in the same set of names as yours, and you cannot declare a task with a
name it already uses:

{{diagnostic:book_task_name_taken}}

`string_reverse` is a standard-library task. The message does not say where
the other declaration is, which makes this confusing the first time. If a task
name you have certainly used only once is reported as conflicting, the
standard library has it. Choose a more specific name.

The names of the operations built into the compiler, such as `ask`, are
protected in the same way, with the message `conflicts with a compiler
builtin`.

## The pipe operator

Nested calls are read from the inside out, which is the opposite of the order
in which they happen. The pipe operator, `|>`, lets you write a chain of calls
in the order they run.

{{example:book_pipe}}

`x |> f()` means `f(x)`: the value on the left becomes the first argument of
the call on the right. If the call has arguments of its own, the piped value
goes in front of them, so `5 |> offset(3)` means `offset(5, 3)`. Pipes chain
from left to right. The first two lines of `main` compute the same thing; the
second says it in the order it happens.

The right side has to be a task named plainly, with its remaining arguments
if it has any. You cannot pipe into a method.

## In V4

Tasks are the part of the language where V4 is closest to V3. Declaration,
calls, `give back`, recursion and calling a task declared later all work at
the pinned commit.

{{v4:recursion}}

{{v4:declared_later}}

There is one condition, which Chapter 1 met in `main`. Every task has to
declare what it gives back. A task with no arrow, V3's way of writing a task
that gives nothing back, does not build:

{{v4:task_without_type}}

Written with `-> void`, the same program builds and runs:

{{v4:task_void}}

Like V3, V4 checks the number and types of arguments and that every path gives
back. It words its findings differently:

{{v4:missing_return}}

{{v4:wrong_arg_count}}

{{v4:wrong_arg_type}}

The argument check is looser than V3's in one respect. Chapter 3 showed this
commit accepting a num for an int parameter and dropping the fraction.

V4 has two things V3 lacks. A call may name its arguments, and then their
order is free:

{{v4:named_arguments}}

Named arguments make a call with several parameters of the same type much
harder to get wrong. In V3, arguments are positional only.

And a task whose body is a single expression can be written with `=>` in place
of braces and `give back`:

{{v4:arrow_task}}

V4 is also missing one thing V3 has:

{{v4:pipe_ignored}}

> [!warn]
> This is a wrong answer, not an error. At the pinned commit V4 reads the pipe
> operators and then leaves them out of the program it builds, so the result
> is the value on the far left. Do not use `|>` with this V4 commit.

## Planned

> [!planned]
> The specification writes the arrow form without a return type, leaving it to
> be inferred: `task square(x: num) => x * x`. The pinned V4 commit builds the
> arrow form only when the type is written out. The specification also allows
> a body with no braces at all, ended by the word `done`, and neither compiler
> builds that.

> [!planned]
> Three larger features are specified around tasks and are not in V3:
> generic tasks, which work for more than one type; closures, which are tasks
> written inline as values; and visibility, which controls whether a task can
> be used from another file. Each has a chapter in Part VII.

## Summary

A task is declared with `task`, a name, typed parameters, and a body. A call
passes arguments by position, and the compiler checks their number and types.

A task that gives a value back declares its type after `->` and uses `give
back`, which ends the task immediately. Every path through such a task must
reach a `give back`; there is no implicit return. A task without an arrow is
`void`.

Numbers, words and bools are copied into a task. Tasks may be declared in any
order and may call themselves. `main` is where the program starts, and an int
it gives back is the exit code. In a program with a `main`, top-level
statements are not run. All tasks, including the standard library's, share one
set of names.

[Chapter 5](book-control-flow.html) completes the core of the language: making
decisions, and repeating work.
