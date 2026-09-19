# Executable documentation maintenance

Documentation describes demonstrated compiler behavior. A successful parser or
compiler exit alone does not prove a runnable example works.

## Version policy

- **V3 follows stable releases.** Verify the official release distribution,
  including its matching standard library and runtime. Record its tag, resolved
  compiler commit, binary SHA-256 and release archive SHA-256. Do not substitute
  a development binary with the same printed version number.
- **Future V4 docs follow explicitly labelled development snapshots.** Before
  publishing that lane, pin an immutable V4 compiler commit, use a separate
  example/expectation set and report, and label every page and manifest
  `generation: v4`, `channel: development`. Show the commit and verification date
  prominently. V3 evidence cannot certify V4, or vice versa.
- This repository currently implements the V3 lane only. No V4 examples,
  verification result, or publication claim is implied by this policy. Adding
  V4 requires an actual compiler adapter and its own CI job to pass these gates.

## Acceptance gate

1. Keep runnable programs in `examples/*.fk`, with reviewed expected output in
   `examples/expectations.json`. Never automatically accept new output as the
   expected answer simply to make a failing run green.
2. Compile **every** program in a fresh directory with the matching distribution.
   Run the produced executable with a timeout; require exit zero and matching
   output. Missing executables, crashes, timeouts and wrong output fail the run.
3. `verified.json` must cover the exact current sources and documentation/tooling
   input hash. A partial `--only` run must use a separate report and cannot pass
   the publication gate. Do not reuse old green results after changing inputs.
4. Build the site and import fragments only after the gate passes. Check search
   and the host site's rendering/navigation separately from compiler correctness.
5. Review and merge generated update PRs, then deploy the host site using its
   normal process. A failed run retains the last verified publication and needs
   investigation; it must not silently delete, skip or rewrite the failing case.

Raw inline `fk` fences are explanatory fragments or illustrative unsupported
syntax, not independently verified programs. The renderer labels them that way.
Prefer `{{example:name}}` or `{{example:name|source}}` for executable claims. When
maintaining a page, promote runnable inline snippets into the example set. A
future negative-example suite must assert the expected diagnostic, not accept
any compiler failure (including a crash) as proof of rejection.

## Refresh cadence and ownership

The `verified-docs.yml` workflow checks every PR, every push to `main`, daily,
and on demand. It resolves the latest stable release unless a maintainer selects
a specific stable V3 tag. A compiler without the V3 Maverick identity is rejected;
when release streams diverge, select the final V3 tag rather than feeding a V4
release to this lane. Future V4 updates must retain their separate snapshot job.

Successful trusted runs upload `docs-v3-verified` for the host site's sync job
and propose changes to the committed report/site on `chore/verified-v3-docs`.
Identical inputs and compiler provenance retain the previous publication report
after a fresh passing run, preventing daily timestamp-only PRs. The Actions run
is the record that the unchanged examples were checked again.

Repository maintainers own failed checks and update PRs. Require the `verify`
job through branch protection before merging; workflow code does not configure
branch protection. GitHub must also allow Actions to create pull requests, and
the repository variable `DOCS_UPDATE_PRS_ENABLED` must be `true`, for automatic
update PRs. That permission is currently disabled in both repositories; the
default is verification and downloadable artifacts only until a maintainer opts
in. The broad GitHub setting also permits workflow PR reviews; these workflows
never approve reviews. Scheduled runs start when this workflow is merged
to the default branch. They do not auto-merge or deploy.

```sh
python tools/refresh.py --release v0.14.2 --jobs 6
python -m unittest discover -s tests -v
# Optional host output:
python tools/build_docs.py --fragments ../freaklang.dev/apps/main-site/public/docs-v3
```

Prerequisites: Python 3.12+, Node.js, authenticated GitHub CLI, and the native
Clang/linker toolchain required by the selected compiler release. The downloaded
distribution and temporary build outputs stay under ignored `.work/` paths.
Colour-related terminal preference variables are removed for program execution
so the colour tutorial has deterministic ANSI output; other bytes are preserved.
