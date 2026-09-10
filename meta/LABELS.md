# FREAK label taxonomy

Issue and PR labels for the **FREAK-lang-dev** organisation.

Source of truth: [`labels.json`](labels.json). Apply with
[`tools/sync_labels.py`](../tools/sync_labels.py).

---

## Shape of it

Every label is `namespace/value`, except a handful of standalone flags. That
buys three things: GitHub's label picker autocompletes by namespace, filters
read naturally (`is:open label:gen/v4 label:area/mir`), and the vocabulary
stays closed — if a label does not fit an existing namespace, that is a signal
to discuss rather than invent.

One hue per namespace, drawn from the FREAK CLI banner gradient in
`src/cli/version.fk`, so the board is colour-legible at a glance.

| Namespace | Answers | Hue |
|---|---|---|
| `gen/` | Which compiler generation? | purple |
| `stratum/` | Where in the V4 plan? | indigo |
| `area/` | Which subsystem? | cyan |
| `kind/` | What sort of work? | green |
| `bible/` | How does it relate to the spec? | pink |
| `status/` | Where is it in the workflow? | amber → grey |
| `prio/` | How urgent? | red |
| `backend/`, `platform/`, `editor/` | Which target? | magenta, slate |

## The minimum on any issue

```
one kind/     always
one area/     unless it is genuinely cross-cutting
one gen/      whenever it touches the compiler
one status/   from triage onward
```

Priority, `bible/`, `stratum/`, `backend/` and `platform/` are added when they
say something. Do not label for the sake of labelling.

---

## `gen/` — compiler generation

**The most important axis in this org**, because it encodes policy, not just
location. `src/compiler/v3/README.md` is explicit: V3 accepts correctness,
diagnostics, ownership, pathological performance, ABI integrity,
reproducibility and release validation. New syntax, new semantics and new
type-system concepts go to V4.

| Label | Meaning |
|---|---|
| `gen/v3` | Shipping self-hosted compiler. Maintenance only |
| `gen/v4` | Maverick / 00-Unit. Destination for all new semantics |
| `gen/lite` | V1 Python bootstrap (`freakc/`) or the V2 `self_hosted/` milestone |
| `gen/all` | Spans generations, or is generation-independent |

So `gen/v3` + `kind/feature` is a contradiction worth catching in triage: the
answer is almost always to relabel it `gen/v4`.

## `stratum/` — the V4 plan

`src/compiler/v4/README.md` sequences V4 by dependency strata, deliberately not
by bible chapter. Labelling the stratum makes "is this unblocked yet?"
answerable from the board.

| Label | Gate |
|---|---|
| `stratum/1-semantic-core` | Value shapes, variants, aliases, tuples, generics |
| `stratum/2-borrowck` | Meiya — only once semantic forms stop moving |
| `stratum/3-ffi-systems` | ABI, layout, raw pointers, LLVM carriage |
| `stratum/4-concurrency` | `xm3`, `sortie`, `formation`, `briefing room`, `wingman` |
| `stratum/5-advanced` | `mood`, `prob`, `power`, `causality`, narrative strictness |

The anti-rewrite rule in that README — do not start stratum 2 while stratum 1
is still moving — is enforceable if the labels are honest.

## `area/` — subsystem

Compiler pipeline: `area/lexer`, `area/parser`, `area/hir`, `area/types`,
`area/mir`, `area/borrowck`, `area/codegen`, `area/runtime`, `area/query`,
`area/snapshot`, `area/lsp`.

Product surface: `area/cli`, `area/hangar`, `area/stdlib`, `area/ffi`,
`area/ui`, `area/anime-layer`, `area/packaging`, `area/editors`, `area/docs`,
`area/tests`, `area/ci`.

These map to real directories and V4 crates, so an issue's label points at the
code. `area/codegen` pairs with `backend/llvm` or `backend/c` when the split
matters.

## `kind/` — nature of the work

`kind/bug`, `kind/feature`, `kind/conformance`, `kind/diagnostics`,
`kind/perf`, `kind/refactor`, `kind/docs`, `kind/test`, `kind/build`,
`kind/security`, `kind/question`, `kind/tracking`.

Two are FREAK-specific and worth using deliberately:

- **`kind/conformance`** — the implementation and `freak-full-bible.md`
  disagree. This is a standing activity here (`freak audit-conformance`,
  `freak-conformance-audit.md`, the §0.2 status table), not an occasional bug
  class.
- **`kind/diagnostics`** — error wording, spans and eventually voice routing.
  The bible devotes a whole section (§14) to it, so it earns its own label.

## `bible/` — relationship to the specification

Mirrors the bible's own legend, plus two the bible cannot express about itself.

| Label | Meaning |
|---|---|
| `bible/implemented` | Works end to end (the bible's ✅) |
| `bible/partial` | Parsed or recognised, guarantee incomplete (⚠️) |
| `bible/v4` | Specified, not in the shipping compiler (🔜) |
| `bible/divergence` | The implementation **contradicts** the spec rather than lagging it |
| `bible/spec-bug` | The **bible itself** is wrong, ambiguous, or self-contradictory |

The last two matter more than they sound. Real examples already in the tree:

- *Divergence*: §8.3 requires case-**sensitive** keywords so `Pilot` and `Some`
  stay usable as identifiers. V3 lowercases before comparing, so they are
  reserved. Not a missing feature — the opposite behaviour.
- *Divergence*: `FINAL FORM` is postfix and takes `num` in the spec; in V3 it
  is prefix and `int`-only.
- *Spec bug*: §1.1 says bindings are "mutable by default" while §4 says plain
  `pilot` is immutable and `mut` opts in. Both cannot hold.

Without these two labels, all three get filed as `kind/bug` and the
distinction — *fix the code* versus *fix the document* — is lost.

An optional `bible-sections` set (`bible/s1-syntax` … `bible/s17-internals`) is
defined in `labels.json` but assigned to no repo. Turn it on for `Freak-lang`
if per-section conformance tracking becomes worth 17 more labels.

## `status/`, `prio/`, and flags

`status/needs-triage`, `needs-repro`, `confirmed`, `blocked`, `in-progress`,
`needs-review`, `stale`, `duplicate`, `wontfix`.

`prio/critical`, `prio/high`, `prio/normal`, `prio/low`.

Standalone: `breaking-change`, `regression`, `release`, plus GitHub's
`good first issue` and `help wanted`, which are kept as-is.

---

## Worked examples

Against the issues open in `Freak-lang` today:

| Issue | Labels |
|---|---|
| #103 Document terminal color output and establish a supported color API | `kind/docs` `kind/feature` `area/stdlib` `gen/v3` `bible/divergence` |
| #105 Document the end-to-end Hangar package authoring workflow | `kind/docs` `area/hangar` `gen/v3` `bible/divergence` |
| #106 Establish a canonical documentation authority and freshness contract | `kind/docs` `kind/tracking` `area/docs` `gen/all` |
| #104 Add a lightweight enum-style surface for finite named values | `kind/feature` `gen/v4` `stratum/1-semantic-core` `area/types` `bible/v4` |
| #101 Guard all post-build MIR consumers | `kind/bug` `gen/v4` `area/mir` `stratum/1-semantic-core` |
| #97 Fix V4 Windows runtime link contract | `kind/bug` `gen/v4` `area/runtime` `platform/windows` `backend/llvm` |
| #95 Bootstrap V4 differential conformance campaign | `kind/conformance` `kind/tracking` `gen/v4` `area/tests` |
| #94 Lower V4 local annotations from semantic HIR facts | `kind/refactor` `gen/v4` `area/hir` `stratum/1-semantic-core` |
| #87 Track owned format_num temporaries in the FREAK Lite emitter | `kind/bug` `gen/lite` `area/codegen` `backend/c` |

Note #103 and #105 carry `bible/divergence`: both describe behaviour the spec
promises and the compiler does not deliver — a colour API that does not exist,
and a Hangar workflow whose install step the build never reads. Filing them as
plain `documentation` loses that.

## Useful queries the taxonomy unlocks

```text
is:open label:gen/v3 label:kind/feature        scope violations to re-triage
is:open label:gen/v4 label:stratum/1-semantic-core   what gates stratum 2
is:open label:bible/divergence                 where code and spec actively disagree
is:open label:bible/spec-bug                   where the bible needs editing
is:open label:area/mir label:gen/v4            everything touching MIR
is:open label:kind/bug label:platform/windows  the Windows-only bug list
is:open -label:status/needs-triage sort:created-asc   triaged backlog, oldest first
```

---

## Applying it

```sh
export GITHUB_TOKEN=...                                  # `repo` scope

python tools/sync_labels.py                              # plan, all repos
python tools/sync_labels.py --repo FREAK-lang-dev/Freak-lang
python tools/sync_labels.py --apply                      # create and update
python tools/sync_labels.py --apply --prune              # also retire stock labels
```

Read-only unless you pass `--apply`. Idempotent: it creates what is missing and
fixes drifted colours and descriptions, and leaves anything it does not
recognise alone rather than deleting it.

`--prune` only removes the seven GitHub stock labels listed under `retire`, and
**refuses to remove one still applied to an open issue** unless you add
`--force-prune`. Deleting a label strips it from every issue that carries it
and cannot be undone, so relabel first. Today that means `documentation` on
#103/#105/#106 and `enhancement` on #103/#104/#106 need moving before a prune.

New repos: GitHub's org-level *Repository defaults → Labels* applies only at
creation time, so run the sync against anything created afterwards.

## Per-repo assignment

| Repo | Sets | Labels |
|---|---|---|
| `Freak-lang` | core + compiler | 71 |
| `Freak-docs`, `FreakDocs`, `FREAK-Website` | core + docs | 42 |
| `freak-editors`, `tree-sitter-freak` | core + editors | 40 |
| `freak-apps`, `.github` | core | 34 |

## Two things to decide first

1. **`Freak-docs` and `FreakDocs` are both live**, and their issues mirror each
   other — `FreakDocs` #1/#2/#3 restate `Freak-lang` #103/#105/#106. Whichever
   is canonical, the other should be archived before labelling both, or the
   taxonomy will just make the duplication tidier. Issue #106 is arguably about
   exactly this.
2. **`.github` is empty.** Community health files there (issue templates,
   `CONTRIBUTING.md`) apply org-wide, and templates can pre-apply labels —
   which is how `status/needs-triage` ends up on new issues automatically. Worth
   doing at the same time.
