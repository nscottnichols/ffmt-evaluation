# ffmt evaluation

This companion repository contains the JLSE evaluation of
[ffmt](https://github.com/nscottnichols/ffmt): system profiles, pinned dependency
recipes, Cobalt launchers, analysis tools, captured evidence, independent
compiler/runtime reproducers, the manuscript and the development skill.
Library headers, portable tests, CI and benchmark primitives belong to ffmt.
ffmt builds and tests without this repository.

Start with the [evidence guide](docs/results/README.md),
[observed gaps](docs/results/gaps.md), [manuscript](docs/paper/ffmt.pdf), and
[provenance and migration record](docs/provenance/README.md). Historical evidence
retains its original source hashes, commands, paths and failures; the split does
not establish a new hardware qualification.

## Select ffmt explicitly

Use an existing checkout containing the portable runners. The source repository
defaults to that checkout. `--revision WORKTREE` captures its current headers;
an immutable revision captures headers with `git archive`.

```sh
export FFMT_CHECKOUT=/path/to/ffmt
python3 tools/conformance.py --revision WORKTREE --profile local \
  --route host-buffer --opt 2 --case literal --numeric-samples 0 --no-negative
```

Alternatively, bootstrap a checkout with a full immutable commit. Mutable branch
names are rejected for bootstrap. The runner pin must contain the portable
external-source interface introduced by the repository split.

```sh
python3 tools/conformance.py --revision 4b8cf257fc68c5b20c0c493e34d1d90269e76fd9 \
  --profile local --route host-buffer --opt 2 --case literal --no-memory --no-negative
```

The runner is independently pinned in [platforms/library.json](platforms/library.json).
`--runner-revision FULL_COMMIT` overrides that pin. `--revision` selects the
library headers, so historical code can use the current pinned harness.
`--ffmt-repository URL` selects the repository for bootstrap. Cached checkouts
live under ignored `software/local/ffmt-checkouts/`; an existing checkout avoids
cloning. The fmt oracle must be available under `third_party/fmt` at exactly
`0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f`, or selected with `--fmt-dir`.

For a historical snapshot, keep a current runner checkout and select the source
repository separately. Retained archive refs provide the old commit objects.

```sh
python3 tools/conformance.py --ffmt-checkout /path/to/current-ffmt \
  --source-root /path/to/ffmt-with-archive-refs \
  --revision 21f9f5ef4b5fbbc173dcd2fc274f94d30d26f8c8 \
  --profile local --route host-buffer --opt 2 --case literal --no-memory --no-negative
```

The portable runner records the library commit and header hashes separately from
its own checkout, fixtures and tool hashes. Evaluation receipts in
`artifacts/launchers/` add the evaluation commit, exact command, profile hash,
discovery hash when present, exit status and hash of the resulting manifest.
They never rewrite the runner manifest. Existing captured evidence is unchanged.

## JLSE and storage

[JLSE usage](tools/jlse/README.md) describes allocation, provisioning and backend
selection. Nonlocal conformance and benchmark launches require an active Cobalt
allocation. Submission resolves the selected ffmt revision before queueing;
evaluation HEAD is never used as a library revision.

```sh
python3 tools/jlse/submit.py head rome --ffmt-checkout /path/to/ffmt --dry-run
python3 tools/jlse/submit.py head rome --ffmt-checkout /path/to/ffmt \
  --extra --route host-buffer --opt 2
```

Installations belong to ignored
`software/<profile>/{downloads,src,build,install}` directories. Raw logs and
binaries belong to ignored `artifacts/`; fmt belongs to ignored `third_party/`.
The current workspace preserves the original directories through ignored
symlinks. No installation or raw evidence needs to be moved or regenerated.
Fresh clones can use ordinary directories or symlinks to existing storage.

## Validate and publish analysis

These offline checks need Python's standard library and Git, with no scheduler,
compiler or accelerator dependency:

```sh
python3 -m unittest discover -s test -v
python3 tools/conformance.py --ffmt-checkout /path/to/ffmt --dry-run --case literal
```

`tools/report.py`, `tools/benchmark_report.py`, and `tools/paper_tables.py`
reproduce compact exports from explicitly selected captured manifests.
`tools/build_paper.sh` generates tables and a PDF in a fresh ignored output
directory, preserving the historical paper and selection ledger.
Independent compiler/runtime reproducers live in [test/regressions](test/regressions/README.md)
and [implementation_limitation](implementation_limitation/). Their failures are
evidence of the recorded environment; they are not library conformance passes.

The [JLSE development skill](skills/ffmt-jlse-development/SKILL.md) provides
orchestration and worker guidance for this evaluation repository.

The [split validation](docs/provenance/validation.json) records passing standalone
library checks and an evaluation smoke against an archived source revision.
The former mixed PR stack is closed as superseded by the
[portable library review stack](docs/provenance/review-stack.md) and
[evaluation PR1](https://github.com/nscottnichols/ffmt-evaluation/pull/1).
The library stack starts at [PR10](https://github.com/nscottnichols/ffmt/pull/10)
and ends at the focused [PR9](https://github.com/nscottnichols/ffmt/pull/9).
Evaluation pins and historical evidence remain unchanged.
