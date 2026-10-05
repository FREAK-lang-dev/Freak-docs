# Executable documentation maintenance

Documentation describes demonstrated compiler behavior. A successful parser or
compiler exit alone does not prove a runnable example works.

## Version policy

- **V3 follows stable releases.** Verify the official release distribution,
  including its matching standard library and runtime. Record its tag, resolved
  compiler commit, binary SHA-256 and release archive SHA-256. Do not substitute
  a development binary with the same printed version number.
- **V4 notes follow one explicitly labelled development snapshot.** The pin is
  an immutable Freak-lang commit in `v4-snapshot.txt`. V4 programs live in
  `examples-v4/` with their own expectations and their own report,
  `examples-v4/verified.json`, labelled `generation: v4`, `channel: development`.
  Every V4 card shows the commit, and every page footer shows the commit and its
  date. V3 evidence cannot certify V4, or vice versa; `evidence.validate` and
  `evidence.validate_v4` each reject the other's report.
- The V4 lane is implemented by `tools/verify_v4.py`, which builds with the
  pinned commit's own `src/compiler/v4/build_v4.py`. It covers the V4 notes in
  The Freak Book only. There are no standalone V4 documentation pages yet, and
  a V4 note is a statement about that one commit, never about a finished V4.
- A V4 expectation may record behaviour that is wrong by the specification (a
  construct accepted and ignored, a limit not enforced). That is deliberate:
  the note says so in words, and the check fails the day V4 fixes it, which is
  the signal to rewrite the note.

## Acceptance gate

1. Keep runnable programs in `examples/*.fk`, with reviewed expected output in
   `examples/expectations.json`. Never automatically accept new output as the
   expected answer simply to make a failing run green. An expectation may add
   `stdin` (the exact text fed to the program), `args` (its command-line
   arguments), `exit_code` (0 when omitted) and `strict_borrow` (the program
   must also build with `--strict-borrow`); all four are part of the claim and
   are recorded in the report.
2. Compile **every** program in a fresh directory with the matching distribution.
   Run the produced executable with a timeout; require the reviewed exit code
   (zero unless the expectation says otherwise) and matching output. Missing executables, crashes, timeouts and wrong output fail the run.
   Normalize CRLF and omit at most one customary final newline; extra trailing
   blank lines and standalone carriage returns remain significant.
3. `verified.json` must cover the exact current sources and documentation/tooling
   input hash. A partial `--only` run must use a separate report and cannot pass
   the publication gate. Do not reuse old green results after changing inputs.
4. Build the site and import fragments only after the gate passes. Check search
   and the host site's rendering/navigation separately from compiler correctness.
   Every content page must appear exactly once in NAV. PRs first validate the
   committed report and rebuild from it; stale evidence or differences from the
   committed site fail CI before the independent fresh compiler run. This keeps
   Vercel's committed static publication current without comparing Linux binary
   hashes or timings against a report generated on Windows.
5. Review and merge generated update PRs, then deploy the host site using its
   normal process. A failed run retains the last verified publication and needs
   investigation; it must not silently delete, skip or rewrite the failing case.

Raw inline `fk` fences are explanatory fragments or illustrative unsupported
syntax, not independently verified programs. The renderer labels them that way.
Prefer `{{example:name}}` or `{{example:name|source}}` for executable claims. When
maintaining a page, promote runnable inline snippets into the example set.

Programs the compiler must reject live in `diagnostics/v3/*.fk`, with the
reviewed text of the diagnostic in `diagnostics/v3/expectations.json`
(`contains`: every listed fragment must appear; `flags`: extra build flags such
as `--strict-borrow`). `verify.py` passes one only when the build ends in an
ordinary compiler rejection, produces no executable, and the diagnostic
contains every fragment. An accepted program, a crash, a timeout or a different
diagnostic fails the run. Show them with `{{diagnostic:name}}`. Results are part
of `examples/verified.json` and the programs are part of its input hash.

## Refresh cadence and ownership

The `verified-docs.yml` workflow checks every PR, every push to `main`, daily,
and on demand. Unattended runs use the stable V3 tag committed in `v3-release.txt`.
Advance that pin and regenerate the report/site together when adopting a newer
V3 release. Manual dispatch or `--release` can override it for evaluation (even
with `latest`), but PR publication evidence must match the committed pin.
A compiler without the V3 Maverick identity is rejected. Future V4 releases
cannot change the V3 selection; V4 retains its separate snapshot job.

Successful trusted runs upload `docs-v3-verified` for the host site's sync job
and propose changes to the committed report/site on `chore/verified-v3-docs`.
Identical inputs and compiler provenance retain the previous publication report
after a fresh passing run, preventing daily timestamp-only PRs. The Actions run
is the record that the unchanged examples were checked again.

Repository maintainers own failed checks and update PRs. Require both the
`verify` and `verify-v4` jobs through branch protection before merging; workflow code does not configure
branch protection. GitHub must also allow Actions to create pull requests, and
the repository variable `DOCS_UPDATE_PRS_ENABLED` must be `true`, for automatic
update PRs. That permission is currently disabled in both repositories; the
default is verification and downloadable artifacts only until a maintainer opts
in. The broad GitHub setting also permits workflow PR reviews; these workflows
never approve reviews. Scheduled runs start when this workflow is merged
to the default branch. They do not auto-merge or deploy.

```sh
python tools/refresh.py --release v0.14.2 --jobs 6
python tools/verify_v4.py --checkout ../Freak-lang   # checked out at v4-snapshot.txt
python -m unittest discover -s tests -v
# After committing regenerated files, check the exact static publication:
python tools/check_publication.py
# Optional host output:
python tools/build_docs.py --fragments ../freaklang.dev/apps/main-site/public/docs-v3
```

Prerequisites: Python 3.12+, Node.js, authenticated GitHub CLI, and the native
Clang/linker toolchain required by the selected compiler release. The downloaded
distribution and temporary build outputs stay under ignored `.work/` paths.
Colour-related terminal preference variables are removed for program execution
so the colour tutorial has deterministic ANSI output; other bytes are preserved.
