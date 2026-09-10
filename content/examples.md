# Verified examples

> Every program on this site, compiled and executed by a real V3 binary.

{{verified-summary}}

Each card below shows the exact source file under `examples/`, a badge for
whether it compiled and ran, and the program's captured output. Reproduce the
whole set with:

```sh
python tools/verify.py --freak /path/to/freak
python tools/build_docs.py
```

The harness copies each example into a clean temporary directory, runs
`freak build` with the default LLVM backend, executes the resulting binary, and
records stdout verbatim. A failure is recorded with its diagnostics rather than
hidden.

## Basics

{{example:hello}}
{{example:variables}}
{{example:inference}}
{{example:reserved_words}}
{{example:toplevel}}

## Tasks

{{example:tasks}}
{{example:recursion}}
{{example:pipe}}

## Control flow

{{example:control_if}}
{{example:control_when}}
{{example:control_loops}}
{{example:training_arc}}
{{example:bounded_search}}

## Operators

{{example:operators}}
{{example:anime_operators}}

## Words

{{example:strings}}
{{example:interpolation}}
{{example:word_builder}}

## Shapes

{{example:shapes}}
{{example:impl_methods}}
{{example:nested_shapes}}
{{example:operator_overload}}

## Lists & arrays

{{example:lists}}
{{example:arrays}}
{{example:array_literal}}

## Standard library

{{example:stdlib_string}}
{{example:stdlib_math}}
{{example:stdlib_convert}}
{{example:stdlib_json}}
{{example:stdlib_version}}

## Console

{{example:colour}}
{{example:ansi_codes}}

## System

{{example:files}}
{{example:bytebuffer}}
{{example:process_time}}
{{example:extern}}

## Anime layer

{{example:eventually}}
{{example:annotations}}

## Tutorials

{{example:tut_greet}}
{{example:tut_cli}}
{{example:tut_roster}}

## Project structure

{{example:module_pattern}}

## Complete programs

{{example:fizzbuzz}}
{{example:wordcount}}
