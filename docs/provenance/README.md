# Repository split and source provenance

The library and its JLSE evaluation now have separate repositories. The
replacement library change starts directly at upstream baseline
`3fe258a87675c997667c899c2b0f0cad405aad5a`; the earlier mixed PR stack is
retained for provenance and must not be merged into the library. The companion
[ffmt-evaluation repository](https://github.com/nscottnichols/ffmt-evaluation)
owns profiles, scheduler/provisioning scripts, campaign orchestration, captured
evidence, analysis, the paper, milestones and the JLSE skill. Portable library
headers, build integration, tests, CI, benchmark primitives and API/backend
documentation remain in [ffmt](https://github.com/nscottnichols/ffmt).

[split.json](split.json) records all seven original PR tips, their replacement
targets, the original source snapshots, source hashes and preserved file hashes.
The replacement library change is now a [seven-part review stack](review-stack.md),
from [PR10](https://github.com/nscottnichols/ffmt/pull/10) through the focused
[PR9](https://github.com/nscottnichols/ffmt/pull/9). The evaluation change remains
[evaluation PR1](https://github.com/nscottnichols/ffmt-evaluation/pull/1).
The original split ledger identifies the first portable library commit, initial
companion import and validated evaluation implementation. The supplemental
[review-stack ledger](review-stack.json) maps the unchanged final library tree
to its new review commits and retains the original library pin through an archive
tag. Historical PR numbers in frozen reports and the paper describe the original
campaign; consult these ledgers for the corresponding review changes.

## Retained snapshots

These tags are in the library fork. All old PR tips and recorded ffmt/runner
commits remain reachable from `archive/jlse-campaign-20261022`, which targets
`52da08a40ec414528ee002163992d77259c54776`. The archived commit contains the
original mixed stack; retaining a tag does not add it to the replacement
library branch's merge ancestry.

| Tag | Original commit | Captured scope |
| --- | --- | --- |
| `qualified/20261022-baseline` | `3fe258a87675c997667c899c2b0f0cad405aad5a` | Original baseline, with the earlier 40-case stdout corpus |
| `qualified/20261022-primary` | `21f9f5ef4b5fbbc173dcd2fc274f94d30d26f8c8` | Main 54-case stdout and 8,216-record memory campaign; selected failures remain included |
| `qualified/20261022-postfix` | `98dba67cdb2dc4686cc512736ad92fdeaebeb63a` | Focused later backend checks, portability checks and shortest-memory measurements |
| `qualified/20261022-final` | `0c2cb764d8ee436bc0221e88cefe417dcbb8d678` | Final counted-view host checks, build integration and host source coverage |
| `archive/library-portable-20261022` | `4b8cf257fc68c5b20c0c493e34d1d90269e76fd9` | Original portable repository split, preserved for unchanged evaluation source/runner pins and split-validation provenance |

The independent fmt oracle remains
`0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f`. It belongs to the
[fmt repository](https://github.com/fmtlib/fmt), not to the ffmt archive.

Fetch retained refs explicitly when an existing clone has not downloaded them:

```sh
git -C ../ffmt fetch origin \
  refs/tags/archive/jlse-campaign-20261022:refs/tags/archive/jlse-campaign-20261022 \
  refs/tags/archive/library-portable-20261022:refs/tags/archive/library-portable-20261022 \
  'refs/tags/qualified/20261022-*:refs/tags/qualified/20261022-*'
git -C ../ffmt show qualified/20261022-primary:include/ffmt/core.hpp
```

To inspect a complete old tree, create a separate detached worktree. Do not
check an old snapshot over a checkout containing local changes or installations.

```sh
git -C ../ffmt worktree add --detach ../ffmt-qualified-primary \
  qualified/20261022-primary
```

The replacement library's 17 headers and `test/conformance/cases.py` are byte
identical to final snapshot `0c2cb76`. The canonical header-map SHA-256 is
`14438e1c9faf6bf2e170e13b371c12a87df42d3f1b5ce597abc22bcbc30ab817`;
the corpus SHA-256 is
`b50ecda885148c5fef472f44593781140dc1bfdd9d1700d1d109a78141c54342`.
The primary and postfix snapshots remain distinct: primary differs from final
in `core.hpp`, `detail/floating.hpp` and `detail/transport.hpp`; postfix differs
in `core.hpp`. Earlier `WORKTREE` measurements retain their captured hash maps
and original identity notes. They are not assigned the replacement commit ID.

This split changes runner and repository paths. Historical hardware runs
qualify their recorded source snapshots and measurement conditions. They do
not qualify changed runner code. Portable checks and an evaluation smoke test
validate the repository boundary; unchanged library headers and corpus do not
justify repeating hardware campaigns.

## Verify preserved bytes locally

The verifier requires Python's standard library and local source files. Its
default check works without Git history, compilers, a scheduler or network
access:

```sh
python3 tools/verify_provenance.py --ffmt-checkout ../ffmt
```

This verifies the frozen JSON exports, baseline/qualification reports, paper
source/PDF/outline, independent reproducers, historical profile/dependency
copies, and final header/corpus equivalence. Mutable README files, migration
guides, milestones and the skill are intentionally outside the byte-preserved
file list. Original profile/dependency bytes are retained as
[original-profiles.json](original-profiles.json) and
[original-dependencies.json](original-dependencies.json), so future operational
configuration changes need not alter the historical locks.

With the archive tags present locally, also verify ref targets, all original
PR/recorded-commit ancestry, and every archived snapshot's header bytes:

```sh
python3 tools/verify_provenance.py --ffmt-checkout ../ffmt \
  --check-source-refs
```

Use `--original-checkout /path/to/archived-ffmt` when another local clone has
the archive refs. Use `--check-raw-inputs` to hash the selected raw manifests when
the retained ignored `artifacts/` directory is available. A fresh Git clone
contains the compact evidence and ledger; it does not contain raw installations
or raw campaign logs.

## Existing workspace and historical commands

The existing local installation and evidence directories remain at their
original paths under `/vast/projects/datascience/nnichols/ffmt_project/ffmt/`.
Ignored symlinks named `artifacts`, `software` and `third_party` in the companion
checkout point to those same directories. No installation or captured raw
evidence is copied, deleted or rebuilt by the split. The original repository and its local worktrees remain available. The primary
`../ffmt` checkout now uses the clean library branch. Historical script paths
are capture locations; recover old scripts through the archive tag in a
separate worktree rather than expecting them in the current library tree.
Untracked paper checkpoints moved to this repository's `docs/paper/.ipynb_checkpoints/`;
remaining TeX build logs are preserved under ignored
`artifacts/split/original-paper-build/`.

Historical command arrays, failures, byte payloads, source hashes, compiler and
runtime identities, durations and measurement provenance are unchanged. A
historical relative `artifacts/...` path resolves through the evaluation
checkout's retained link; an absolute path containing the old `/ffmt/` checkout
continues to mean that original path. Current guides describe the new commands
without rewriting captured evidence.

New evaluations consume an existing portable ffmt checkout explicitly:

```sh
python3 tools/conformance.py --ffmt-checkout ../ffmt \
  --revision HEAD --profile local --route host-buffer --opt 2
```

To evaluate a retained old library snapshot with the current portable runner,
select the two source locations separately:

```sh
python3 tools/conformance.py --ffmt-checkout ../ffmt \
  --source-root ../ffmt --revision qualified/20261022-primary \
  --profile local --route host-buffer --opt 2
```

Without an existing checkout, supply a full 40-character immutable source
`--revision`. The modern runner is independently pinned in
`platforms/library.json`; `--runner-revision` overrides that pin.
`--ffmt-repository` selects the source repository. The adapter stores its
pinned checkout under ignored `software/local/`.
New launcher receipts distinguish evaluation, runner and library-source
commits and dirty state, preserve the command, and record launcher/config and
result-manifest hashes.

The independent AMD/NVIDIA callback controls and two preexisting compiler
controls belong to evaluation. The latter already existed under
`implementation_limitation/` in upstream baseline history; the replacement
library removes them from its tree without rewriting existing upstream
ancestry. Library regressions that exercise ffmt directly remain portable
tests in the library repository.

## Split validation

[validation.json](validation.json) records the CPU-only validation at library
commit `4b8cf257fc68c5b20c0c493e34d1d90269e76fd9`, including commands and log hashes.
All 15 Clang Release CTest entries pass. The installed consumer configures and
runs with library tests disabled, Python discovery disabled and an unavailable
fmt path. GCC13 Make suites pass with ASan/UBSan at `-O0`; native BitInt remains
an explicit optional skip in that compiler. Negative subprocesses use their
recorded compiler-default optimization.

The evaluation smoke uses the clean portable runner against archived source
`0c2cb76`: two exact stdout cases and 24 numeric boundary records pass. Its
receipt preserves the original source identity, separate runner commit and
launcher hashes. The allocated run's ten offline evaluation tests are recorded
as captured; subsequent build-check/exporter regressions bring the final offline
suite to 13 passing tests, recorded separately in the same validation file.
No GPU campaign was repeated.

The paper helper builds into fresh ignored output and preserves the historical
paper, generated tables and selection ledger. A successful eight-page rebuild
and unchanged-evidence verification were also checked after the split.
