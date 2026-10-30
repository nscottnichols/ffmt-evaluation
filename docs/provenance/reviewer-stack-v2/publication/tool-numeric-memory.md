Printf transport can hide whether floating-point conversion and bounded output accounting produced the correct memory bytes.

For example:

```text
A record for a subnormal double checks the input encoding, output bytes, written/required counts and error status against independent fmt.
```

Use explicit binary framing and a fixed seed. Keep numeric operations in a conventionally formatted handwritten C++ template that is hashed with runner inputs. The default corpus has 4096 seeded float encodings, 4096 seeded double encodings, and 24 boundary/special encodings. This is representative sampling, not exhaustive floating-point proof. The portable smoke command reduces the seed count to 32 per type and executes host memory only.

Read in this order:

- [test/conformance/numeric_memory.cpp.in](https://github.com/nscottnichols/ffmt/blob/d729ba7b56c07ec711eb9a24e9e91553f661a69a/test/conformance/numeric_memory.cpp.in)
- [tools/numeric_memory.py](https://github.com/nscottnichols/ffmt/blob/d729ba7b56c07ec711eb9a24e9e91553f661a69a/tools/numeric_memory.py) — parse_records
- [tools/conformance.py](https://github.com/nscottnichols/ffmt/blob/d729ba7b56c07ec711eb9a24e9e91553f661a69a/tools/conformance.py) — memory_suite
- [test/conformance/test_numeric_memory.py](https://github.com/nscottnichols/ffmt/blob/d729ba7b56c07ec711eb9a24e9e91553f661a69a/test/conformance/test_numeric_memory.py)
- [test/conformance/test_auxiliary_evidence.py](https://github.com/nscottnichols/ffmt/blob/d729ba7b56c07ec711eb9a24e9e91553f661a69a/test/conformance/test_auxiliary_evidence.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 8 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
python3 -m unittest discover -s test/conformance -p test_numeric_memory.py
python3 tools/conformance.py --route host-buffer --opt 2 --numeric-samples 32 --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 11; it remains draft until prerequisite human review.

Base: [`review-v2/migration`](https://github.com/nscottnichols/ffmt/tree/review-v2/migration); 2 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
