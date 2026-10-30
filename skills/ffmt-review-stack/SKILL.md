---
name: ffmt-review-stack
description: Assemble and review the ffmt library PR graph, validate intermediate commits, and publish staged review waves while preserving evaluation identities. Use for ffmt stack maintenance, not campaign execution.
---

# Reviewer-oriented ffmt changes

Work in the library fork, rooted at original main `3fe258a87675c997667c899c2b0f0cad405aad5a`.
The evaluation repository owns this workflow, publication records and validation
captures. It must not become a dependency of the portable library.

Each stage should ask a C++ reviewer one concrete question. Introduce its tests,
API notes and required build registration with its implementation. A test must
not import an unrelated feature to reuse a helper. Keep true sibling features
on their common prerequisite. Merge-only assembly bases can collect accepted
sibling heads for integration tests; record their parents and verify they add no
handwritten changes.

Before publishing a stage, compile its intermediate tree and run its affected
checks. Use an independent agent to assess both scope/readability and actual
buildability, with the diff and commands available. Fix findings before marking
the stage ready. Publish only a manageable initial wave as ready; later complete,
validated waves remain draft until the preceding wave has human review.

PR descriptions should include a problem and small before/after example, the
design and material tradeoffs, a short implementation/test reading order, and
actual validation commands/results/limitations. Keep dependencies and provenance
in a short footer pointing to one overview. The coverage-policy change must say
plainly that blocking regression detection becomes reporting and explain what
automatic protection is lost.

Separate mechanical movement, semantic changes and obsolete-code deletion.
Preserve original commit objects through archive refs before replacing branches.
Compare final sources against retained snapshots, classify changes, and keep the
historical evaluation source/runner pins unchanged. Source hashes changing due to
movement do not relabel old measurements as new qualification. Run new hardware
campaigns only when a relevant behavior/backend change warrants them.

Handwritten headers, tests, scripts and C++ templates remain visible in review.
Do not call them generated or hide them with Linguist attributes. Losslessly
archived raw output may be treated as generated evidence; retain per-file hashes,
failure records and exact commands. Preserve local installations and raw captures.

Stage inputs live in isolated ignored worktrees. The orchestrator owns git refs,
commits, pushes and PR edits. Use `GOMAXPROCS=2` with `gh` on JLSE. Use allocated
CPU nodes for compiler validation; see the separate JLSE skill for Cobalt details.
