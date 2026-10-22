# Portable library review stack

The portable library change is now seven dependent PRs, rooted directly at
upstream baseline `3fe258a87675c997667c899c2b0f0cad405aad5a`. Each PR targets the preceding
branch, so its review diff contains one scope. [review-stack.json](review-stack.json)
records the full commit IDs, bases, branches and PR links.

| Order | PR | Review scope | Head branch | Commit |
| --- | --- | --- | --- | --- |
| 1/7 | [#10](https://github.com/nscottnichols/ffmt/pull/10) | Add independent portable fmt conformance tooling | `review/conformance` | `3845e997e481` |
| 2/7 | [#11](https://github.com/nscottnichols/ffmt/pull/11) | Unify checked formatting and bounded device output | `review/core` | `2f7508c4fa2a` |
| 3/7 | [#12](https://github.com/nscottnichols/ffmt/pull/12) | Add named arguments, range formatting and forwarding | `review/ranges` | `3e5ae22ba1a3` |
| 4/7 | [#13](https://github.com/nscottnichols/ffmt/pull/13) | Add chrono, standard type and styling adapters | `review/families` | `7bccd77f4bf5` |
| 5/7 | [#14](https://github.com/nscottnichols/ffmt/pull/14) | Add checked typed printf formatting | `review/printf` | `745088a005da` |
| 6/7 | [#15](https://github.com/nscottnichols/ffmt/pull/15) | Add verified portable formatting benchmark primitives | `review/benchmarks` | `159fdf2a4ca1` |
| 7/7 | [#9](https://github.com/nscottnichols/ffmt/pull/9) | Package the library and document portable APIs and backends | `library-portable` | `aeff04361472` |

PR #9 remains the top PR, now focused on packaging and documentation. Its
previous complete portable implementation is retained at
`archive/library-portable-20261022`, targeting `4b8cf257fc68c5b20c0c493e34d1d90269e76fd9`.
The final stack commit is `aeff043614725d58d383c8add086f548d77d05eb`. Both commits have the exact tree
`f3cc9d33e0443dc9f1e1a1941c19843401988b19`: this restructure changes history and review
boundaries without changing any final tracked file.

## Preserve evaluation identities

The evaluation source and runner pins in
[platforms/library.json](../../platforms/library.json) remain `4b8cf257fc68c5b20c0c493e34d1d90269e76fd9`.
The original [split ledger](split.json), [split validation](validation.json),
qualified source snapshots and captured campaign evidence retain their existing
commit IDs, hashes, failures, commands and measurement provenance. Those records
describe the original split; this supplemental mapping describes its review
reorganization. No hardware campaign is repeated for an unchanged final tree.

Fetch the retained portable snapshot explicitly if it is not present locally:

```sh
git -C ../ffmt fetch origin \
  refs/tags/archive/library-portable-20261022:refs/tags/archive/library-portable-20261022
git -C ../ffmt rev-parse 'archive/library-portable-20261022^{commit}'
git -C ../ffmt diff --exit-code archive/library-portable-20261022 aeff043614725d58d383c8add086f548d77d05eb
```

Use the historical snapshot for existing evaluation pins. A new evaluation can
explicitly select the final stack commit; its distinct commit identity remains
visible in receipts despite identical source bytes.

## Validation

CPU-only validation covers all seven immutable prefixes. The first six prefixes
pass their selected checks, including the harness, core/family/range/printf
regressions, negative-compile controls, C++23 adapters and a verified host-memory
benchmark smoke. The final prefix passes all **15 CTest entries**, including the
full host conformance corpus, plus installation.

The [original attempt](review-stack-validation/manifest.json) retains its overall
`failure` status: its generated package consumer incorrectly included internal
`ffmt/core.hpp` directly. A [consumer-only follow-up](review-stack-validation/consumer-followup/manifest.json)
using documented public `ffmt/base.hpp` configures, builds and runs successfully
against the same installed prefix. All 17 installed header hashes match the
unchanged final stack commit. The correction changes only the validation fixture;
no library source, history, full suite or hardware campaign was repeated.

Legacy and focused Make checks use Clang 22 with ASan/UBSan and explicit
`HOST_OPT=-O0`. Negative subprocesses inherit sanitizer flags but run at the
compiler's default optimization because Make does not forward `HOST_OPT` to the
negative driver. The final CMake build uses Release and enables C++23 tests.
No optional extension-type or C++23 skip was reported on this compiler.

The original [submission record](review-stack-validation/submission.json),
[validation scripts](review-stack-validation/validate.py), captured source hashes,
exact commands and completed Cobalt logs remain available. The captured validation
index names the local final assembly branch `review/integration`; PR #9 publishes
that same commit as `library-portable`.

Original raw logs and child manifests are bundled losslessly in
[raw-logs.tar.gz](review-stack-validation/raw-logs.tar.gz).
[captured-files.json](review-stack-validation/captured-files.json) records each
original path, archive member, byte count and decompressed SHA-256, plus the
archive hash. Every member was decompressed and verified before removing the
redundant captured log directory; original ignored raw evidence remains untouched.
Small follow-up logs are [stored directly](review-stack-validation/consumer-followup/captured-files.json).
To inspect original logs without modifying the evidence repository:

```sh
mkdir -p /tmp/ffmt-review-stack-logs
tar -xzf docs/provenance/review-stack-validation/raw-logs.tar.gz \
  -C /tmp/ffmt-review-stack-logs
```

The [supplemental ledger](review-stack.json) distinguishes both attempts and
records capture hashes. The previous split validation and historical hardware
qualification remain unchanged.

## Merge in dependency order

Review and merge **#10 → #11 → #12 → #13 → #14 → #15 → #9**. After a
dependency lands, retarget the next PR to `main`. Retain each dependency branch
until its dependents have been retargeted.

Merge commits preserve the recorded stack heads. If a PR is squashed or
rebased, restack the remaining branches and update this supplemental mapping;
retain the old commits and do not rewrite original qualification evidence.
