System format implementations and moving oracle revisions can disagree about expected output.

For example:

```text
For a subnormal double, every portable test compares the same ffmt bytes with the same fmt revision on every compiler.
```

Pin the Make reference before introducing the independent oracle and new focused comparisons; retain an explicit external FMT_DIR override. Expected behavior follows this fixed fmt revision rather than the installed standard library; updating it requires an explicit compatibility review.

Read in this order:

- [Makefile](https://github.com/nscottnichols/ffmt/blob/4667a850a000fae69a7fd6a04888ee41df908c2d/Makefile) — FMT_REF
- [docs/contributing/ORACLE.md](https://github.com/nscottnichols/ffmt/blob/4667a850a000fae69a7fd6a04888ee41df908c2d/docs/contributing/ORACLE.md)
- [test/conformance/test_oracle_pin.py](https://github.com/nscottnichols/ffmt/blob/4667a850a000fae69a7fd6a04888ee41df908c2d/test/conformance/test_oracle_pin.py)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 6 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
python3 -m unittest discover -s test/conformance -p test_oracle_pin.py
make -j2 CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT=-O0 EXTRA_CXXFLAGS=-fsanitize=address,undefined test-host test-fast-math
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Ready for the first review wave.

Base: [`review-v2/ci-resource-bounds`](https://github.com/nscottnichols/ffmt/tree/review-v2/ci-resource-bounds); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
