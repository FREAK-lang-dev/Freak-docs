# Grammar

> The complete V3 grammar, transcribed from `src/compiler/v3/lexer.fk` and `parser.fk`.

This is the whole language. If a construct is not derivable from these rules, it
does not parse.

## Lexical structure

```text
program-text  = { token | whitespace | comment }

comment       = "--" { any-char-except-newline }
whitespace    = " " | "\t" | "\r" | "\n"

token         = number | word-literal | identifier | keyword
              | bool-literal | punctuation

number        = digit { digit | "." }
                -- more than one "." is a lex error
                -- no sign, no exponent, no suffix

word-literal  = '"' { char | escape } '"'
escape        = "\\n" | "\\r" | "\\t" | "\\" any | "\\x" hex hex
                -- "\x00" is rejected

identifier    = ( letter | "_" ) { letter | digit | "_" }
                -- letters are ASCII A-Z a-z only
```

Identifiers are classified against the keyword table **case-insensitively**: an
identifier whose lowercase form is a keyword becomes that keyword token.

```text
bool-literal  = "true" | "false" | "yes" | "no" | "hai" | "iie"

punctuation   = "==" | "!=" | "<=" | ">=" | "+=" | "-=" | "*=" | "/="
              | "%=" | "->" | "=>" | "**" | "|>" | "||" | "::"
              | "=" | "+" | "-" | "*" | "/" | "%" | "<" | ">" | "!"
              | ":" | "|" | "@" | "?" | "{" | "}" | "(" | ")"
              | "[" | "]" | "," | "."
```

`**`, `=>`, `||`, `?` and `!` are produced by the lexer but have **no grammar
rule** — reaching one is a parse error.

### Multi-word keywords

Lexed greedily: on seeing the first word, the lexer looks ahead for the second
and merges them.

```text
"give back"  "or else"    "trust me"   "for each"   "for science"
"training arc"   "bringing back"   "only on"   "PLUS ULTRA"   "FINAL FORM"
```

### Keyword table

```text
pilot fixed task say shape impl doctrine launch use as in lend mut move
copy break continue if else when repeat times until done for each check
result got nobody some ok err sessions max foreshadow payoff route sadly
deus_ex_machina isekai eventually and or not nakama tsundere extern
```

Many of these are reserved without having a grammar rule — see
[the reserved list](language-basics.html#the-full-reserved-list).

## Program

```text
program    = { statement }
```

There is no distinction between top-level and nested statements: the same
`statement` rule is used everywhere. A `task`, `shape` or `impl` is syntactically
just a statement, so it may legally appear nested inside another block.

## Statements

```text
statement  = [ annotation ] statement-body

annotation = "@" identifier            -- exactly one, no arguments

statement-body =
      say-stmt | shape-decl | impl-decl | eventually-stmt
    | fixed-decl | pilot-decl | give-back | break-stmt | continue-stmt
    | if-stmt | repeat-stmt | training-arc | when-stmt
    | extern-decl | task-decl | block | assign-or-expr

say-stmt      = "say" expression

fixed-decl    = "fixed" "pilot" identifier [ ":" type ] "=" expression
pilot-decl    = "pilot" [ "mut" ] identifier [ ":" type ] "=" expression

give-back     = "give back" [ expression ]
break-stmt    = "break"
continue-stmt = "continue"

if-stmt       = "if" expression block [ "else" ( if-stmt | block ) ]

repeat-stmt   = "repeat" "until" expression block
              | "repeat" expression "times" block

training-arc  = "training arc" "until" expression
                "max" expression "sessions" block

when-stmt     = "when" expression "{" { when-arm } "}"
when-arm      = ( "_" | expression ) "->" statement

eventually-stmt = "eventually" block

block         = "{" { statement } "}"

assign-or-expr = expression [ assign-op expression ]
assign-op      = "=" | "+=" | "-=" | "*=" | "/=" | "%="
```

Every type position — `pilot-decl`, `fixed-decl`, shape fields, parameters,
return types, `extern` signatures — goes through one rule:

```text
type        = identifier
            | "List" "<" identifier ">"
```

> [!note]
> `List<T>` is the language's only generic form, and it is a hard-coded special
> case in `parser_take_type` rather than a general mechanism: the element must
> be a plain identifier, so `List<List<int>>` is rejected. That single rule is
> why `maybe<T>`, `result<T,E>`, `Map<K,V>`, fixed arrays, tuples and raw
> pointers have no syntax.

## Declarations

```text
shape-decl  = "shape" identifier "{" { field } "}"
field       = identifier ":" type [ "," ]

impl-decl   = "impl" identifier [ "for" identifier ] "{" { impl-method } "}"
impl-method = "task" identifier "(" params ")" [ "->" type ] block

task-decl   = "task" identifier "(" params ")" [ "->" type ] block

extern-decl = "extern" "task" identifier "(" ext-params ")" "->" type

params      = [ param { "," param } ]
param       = "self" | identifier ":" type
ext-params  = [ identifier ":" type { "," identifier ":" type } ]
```

In `impl D for S`, `S` owns the methods and `D` is recorded as provenance only —
it is never validated. A method's mangled global name is `S_method`.

`self` is written bare; the compiler substitutes the owning shape's type.

## Expressions

Loosest to tightest:

```text
expression  = and-expr { "or" and-expr }
and-expr    = cmp-expr { "and" cmp-expr }
cmp-expr    = add-expr { ( "==" | "!=" | "<" | ">" | "<=" | ">=" ) add-expr }
add-expr    = mul-expr { ( "+" | "-" | "NAKAMA" ) mul-expr }
mul-expr    = unary { ( "*" | "/" | "%" ) unary }

unary       = ( "not" | "-" | "PLUS ULTRA" | "FINAL FORM" | "TSUNDERE" ) unary
            | postfix

postfix     = primary { postfix-op }
postfix-op  = "." identifier [ "(" args ")" ]
            | "[" expression "]"
            | "|>" identifier [ "(" args ")" ]

primary     = number
            | word-literal
            | bool-literal
            | identifier [ "::" identifier ] [ ctor-args | "(" args ")" ]
            | "(" expression ")"
            | "[" [ expression { "," expression } ] "]"

ctor-args   = "{" [ field-init { "," field-init } ] "}"
field-init  = identifier ":" expression

args        = [ expression { "," expression } ]
```

`ctor-args` is only taken when the identifier is an **already-registered shape
name**, which is why a shape must be declared before it is constructed in token
order.

`x |> f(a)` desugars to `f(x, a)`; the pipe target must be a bare identifier.

## String interpolation

Interpolation is resolved by the parser after lexing, over the literal's text.

```text
interp-path = identifier { "." identifier }
```

A `{...}` whose body matches `interp-path`, where every segment is a valid
identifier and not a keyword, becomes an interpolated expression. Anything else
— including `{1 + 2}` and `{f()}` — stays literal text, braces included. An
unmatched `{` is literal.

The resolved path must have type `word`, `int`, `num` or `bool`.

## Error recovery

The parser reports a diagnostic, skips one token, and continues. After 100
syntax errors it stops:

```text
error: too many errors, giving up (>100 syntax errors in <file>)
```

There are no `ErrorNode` or `IncompleteNode` tolerant-AST nodes — those are V4.
Codegen is skipped whenever any frontend diagnostic fired.

## Reading the real thing

The authoritative sources, in the order they are concatenated:

| File | Role |
|---|---|
| `src/compiler/v3/globals.fk` | Identity, compiler state, token and AST tables |
| `src/compiler/v3/helpers.fk` | Arrays, diagnostics, AST allocation, emit helpers |
| `src/compiler/v3/lexer.fk` | Tokenisation |
| `src/compiler/v3/parser.fk` | Recursive descent into parallel AST arrays |
| `src/compiler/v3/checker.fk` | Type checks and the opt-in Phase-1 borrow checker |
| `src/compiler/v3/emit_c.fk` | Streaming C lowering |
| `src/compiler/v3/emit_llvm.fk` | Streaming LLVM IR lowering |
| `src/compiler/v3/main.fk` | Standalone `freakc` entry point |

The whole compiler is one flattened translation unit with globally unique
symbols; the file split is a maintenance convention, not a module system.
