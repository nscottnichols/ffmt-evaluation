# Review-stack CPU validation

`validate.py` consumes an assembly index containing full immutable ffmt commits.
It does not create branches, alter the source, submit jobs, or remove evidence.
A separate detached checkout and build directory is retained for each stage and
compiler, preventing Clang/GCC object reuse.

Before submitting, verify the index and the clean pinned fmt checkout:

```sh
python3 tools/review_stack/validate.py /absolute/assembly-index.json --preflight
```

Run compilation on an allocated x86 CPU node. Use `FFMT_REVIEW_SYSTEM=rome`,
`cpl` or `skylake` so the existing environment setup isolates its OS runtime
symlink under that system's ignored software directory. Cobalt must open a `/home` working
directory before `/vast` is mounted:

```sh
qsub --mode script -q rome_7742 -n 1 -t 240 --cwd /home/nnichols \
  --env FFMT_REVIEW_SYSTEM=rome \
  /bin/bash /absolute/ffmt-evaluation/tools/review_stack/validate-cobalt.sh \
  /absolute/assembly-index.json --repo /absolute/ffmt
```

Each index stage supplies `id`, `commit`, `base_commit`, `dependencies`, `suites`
and optional `validation_commands`. Suite entries name the `build/cap_NAME` Make
target and retain their source/standard/flags/reference metadata. Set `optional: true`
only for compiler/standard-library capabilities whose unavailable result is
exit 77; other suites are mandatory. Commands are
argument arrays; `{source}`, `{fmt_dir}`, `{output}`, `{cxx}`, `{repo}`, `{revision}`
and `{python}` placeholders are expanded without invoking a shell. `--stage ID`
can select affected stages for a fresh correction run while retaining the failed
attempt. It does not overwrite or amend an earlier result.

Clang 22 runs at `-O0` with strict ASan/UBSan; GCC 13 provides a separate `-O2`
check. Each introduced capability builds and executes separately. For optional suites, exit 77 is
recorded as an explicit unsupported skip, never as conformance. Exit 77 from a
mandatory suite fails validation. Separate source
files probe inclusion of `base.hpp` and `detail/checked.hpp`. Migration and final
integration read every explicit Make suite registration (including its `FFMT_OPTIONAL_NAME`
marker) and run all registered capabilities and historical host compatibility
tests; final integration runs
CMake, CTest, installation and a consumer using the installed package.

A fresh manifest retains the index and runner copies, exact commands,
non-secret environment selections, source revisions and file hashes, compiler
identities, raw log paths/hashes, binary hashes, failures, skips and timing.
Portable source-generation tests do not establish accelerator execution. These
CPU checks qualify the review intermediates; preserved hardware campaign
measurements retain their original revisions and source hashes.

## Assemble and publish

`assemble.py` takes a plan of explicitly exported stage inputs. A stage names its
prerequisites, source directory, removals, optional context-checked patches,
extra suite variants and validation argv. Tests are registered explicitly with
their implementation. Handwritten C++ templates and scripts remain ordinary
source. No network write occurs during assembly:

```sh
python3 tools/review_stack/assemble.py /absolute/plan.json \
  --repo /absolute/ffmt --worktree /absolute/scratch \
  --index /absolute/stage-index.json --apply
```

Multi-parent bases require clean Git merges. A local cache preserves qualified
commit IDs when the base and candidate tree are unchanged, and keeps later
records after a failed partial attempt. The cache is an orchestrator-owned local
input, not an untrusted artifact; cached merge bases retain their original clean
merge provenance. The index records every stage input hash, immutable tree and
base. Compare exported source blobs with committed blobs before freezing a run.
The library does not require these stage inputs or evaluation scripts to build.

For independent CPU batches, use disjoint `--stage` selections with the same
frozen full index. `FFMT_REVIEW_SYSTEM=cpl` or `skylake` selects an isolated
`software/<system>/install/host-runtime` environment; the default is `rome`.
Pass that non-secret setting through Cobalt `--env`. Reuse only exact passed
stage/commit rows. Keep failures and cancelled jobs with their original statuses.

After every published head has passing evidence, `render.py` combines stage
notes and immutable results into review bodies and a publication manifest:

```sh
python3 tools/review_stack/render.py /absolute/stage-index.json \
  --evidence /absolute/validation/manifest.json --output /absolute/bodies
# Repeat --evidence for independent batches and preserved passing prefixes.
python3 tools/review_stack/publish.py /absolute/bodies/publication.json \
  --repo /absolute/ffmt
```

Review the bodies and manifest, push the exact qualified head and base refs, then
add `--apply` to publish. The publisher verifies body hashes, local commits and
remote full SHAs before writing PRs. It resumes existing matching PRs, rejects
unexpected base/readiness changes, never merges, and never advances a draft wave
automatically. Only wave 1 is initially ready. The single
[overview](../../docs/provenance/reviewer-stack-v2.md) holds the full graph and
snapshot mapping; each PR keeps a short base/provenance footer.

## Preserve completed attempts

`capture.py` copies completed validation and frozen scheduler receipts into
reviewable provenance. Finalize scheduler output in the submission directory
first. The helper rejects active manifests and existing destinations; a queued
cancellation needs its explicit cancellation receipt.

```sh
python3 tools/review_stack/capture.py \
  --validation /absolute/completed-validation \
  --submission /absolute/frozen-submission \
  --output docs/provenance/reviewer-stack-v2/attempts/new-attempt
python3 tools/review_stack/capture.py \
  --output docs/provenance/reviewer-stack-v2/attempts/new-attempt --verify
python3 -m unittest discover -s tools/review_stack -p test_capture.py
```

Manifests, indices and handwritten scripts remain visible. Repeat
`--input LABEL=PATH` to preserve additional handwritten fixtures, stage exports,
planning helpers or audits visibly. Only raw output and generated probes/cases
go into `raw-logs.tar.gz`; the per-file inventory records original paths, byte
counts, storage locations and SHA-256. Source worktrees, compiler products and
CMake builds are excluded. Original evidence, installations and pins are never
rewritten. Input-only captures are identified separately from validation, and
failed or cancelled attempts retain those outcomes.
