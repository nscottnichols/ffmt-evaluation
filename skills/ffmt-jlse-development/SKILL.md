---
name: ffmt-jlse-development
description: Run and analyze ffmt evaluation campaigns on JLSE Cobalt resources using the companion evaluation repository and an explicit external library source. Use for JLSE evaluation, provisioning, measurements, paper or evidence work; not ordinary portable library changes or unrelated clusters.
---

# ffmt evaluation on JLSE

The evaluation checkout is `/vast/projects/datascience/nnichols/ffmt_project/ffmt-evaluation`.
The library is a separate repository at `../ffmt`. Read `README.md`,
`docs/MILESTONES.md` and `docs/provenance/README.md` in the evaluation checkout.
The user's latest scope takes precedence over this historical campaign ledger.

Keep headers, portable tests, build integration, portable CI, benchmark primitives
and API/backend documentation in the library. Keep site profiles, provisioning,
scheduler policy, campaign orchestration, captured results, analysis, manuscripts
and independent compiler/runtime reproducers here. Do not add campaign files to
a library PR or merge the archived pre-split stack into the clean library branch.

Use an explicit ffmt checkout or full pinned source revision. The evaluation
launcher identifies the source and portable runner separately; preserve both
identities and fixture hashes. Read `tools/conformance.py --help`,
`tools/benchmark.py --help` and `tools/jlse/README.md` before changing invocations.
A WORKTREE run is development evidence, whose captured header hashes must match
an immutable source before being used in a release claim.

Use `platforms/profiles.json`, `platforms/dependencies.json` and `tools/jlse/`.
JLSE uses Cobalt (`qsub --mode script -q QUEUE -n 1 -t MINUTES --cwd /home/nnichols /bin/bash SCRIPT ARGS`).
Read `qsub --help` if changing arguments. Obtain an allocation before compute-node
execution. Keep installations in ignored `software/<system-id>/{downloads,src,build,install}`
and raw results in ignored `artifacts/`. Existing workspace symlinks preserve
the original installations and absolute paths; do not move or rebuild them casually.

The pinned fmt oracle is independent host code. Preserve exact bytes and complete
expectations. Failed controls, compiler crashes, skips and unavailable hardware
are never passing conformance. Record actual devices, commands and errors;
prevent host fallback. Keep fallback device names visible even when a queue
profile retains its primary system's name. Distinguish memory, stdout,
compile-only resource probes and hardware execution.

Historical evidence and commands remain immutable. `tools/verify_provenance.py`
checks the split mapping and retained file/header hashes. New results go to fresh
paths. Do not relabel old source revisions as the new library commit. The archive
and qualified tags in `docs/provenance/split.json` retain the original snapshots.
Do not repeat unchanged hardware campaigns solely because paths or commit IDs changed.

Workers own assigned files and report interfaces, commands and exact validation.
The orchestrator owns branch changes, commits, pushes and PR integration. Do not
reset another worker's changes. Library and evaluation PRs target their respective
working forks. Set `GOMAXPROCS=2` for GitHub CLI calls on JLSE. Record only selected
non-secret environment fields; never credential values.
