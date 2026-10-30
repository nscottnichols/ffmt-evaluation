Discovering test source files with a wildcard can silently omit a declared test when its file is missing.

For example:

```text
A registration naming test/conformance/test_output.cpp is a required Make prerequisite; deleting that source fails the build rather than shrinking the test suite.
```

Each capability adds a small explicit registration. A shared Make fragment provides compiler, reference-library, C++ standard and optional-extension handling. Registrations are additional build metadata, but independent feature branches add separate files and do not edit one combined test source or suite list.

Read in this order:

- [mk/portable-tests.mk](https://github.com/nscottnichols/ffmt/blob/d1e8f0e8e1eba7c47829d1d410362f8cc73041d1/mk/portable-tests.mk)
- [docs/contributing/TESTS.md](https://github.com/nscottnichols/ffmt/blob/d1e8f0e8e1eba7c47829d1d410362f8cc73041d1/docs/contributing/TESTS.md)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes and affected C++ Make suites used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded checks passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, and `OUT` is a fresh evidence directory):

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
python3 -m unittest discover -s test/conformance -p test_build_registration.py
```

The immutable evidence retains the complete argv, flags, header probes, raw logs, source hashes and results. ASan/UBSan applies to the affected C++ Make suites and header probes above. Standalone differential, benchmark, CMake and compiler-rejection commands use their separately recorded flags; this does not claim sanitizer coverage for every command. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Ready for the first review wave.

Base: [`review-v2/oracle-pin`](https://github.com/nscottnichols/ffmt/tree/review-v2/oracle-pin); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
