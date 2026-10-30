The historical blanket bool suppression can hide undefined behavior after the old formatting path has been replaced.

For example:

```text
EXTRA_CXXFLAGS=-fsanitize=address,undefined
# bool checks are active again
```

Remove only the obsolete -fno-sanitize=bool exception and its explanation; preserve the matrix and all commands. Dependency/toolchain bool defects now fail CI as well. A new suppression would need a demonstrated scoped reason.

Read in this order:

- [.github/workflows/host.yml](https://github.com/nscottnichols/ffmt/blob/584253ca2c158308def053f80e2537d34e052120/.github/workflows/host.yml) — matrix.env.EXTRA_CXXFLAGS
- [docs/contributing/SANITIZERS.md](https://github.com/nscottnichols/ffmt/blob/584253ca2c158308def053f80e2537d34e052120/docs/contributing/SANITIZERS.md)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 7 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT=-O0 'EXTRA_CXXFLAGS=-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer' test-host test-capabilities conformance-harness test-negative
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. Hosted workflow execution is not established by these local checks. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 7; it remains draft until prerequisite human review.

Base: [`review-v2/base-ci-sanitizers`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-ci-sanitizers); 2 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
