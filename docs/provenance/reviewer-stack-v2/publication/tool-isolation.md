A combined switch can fail although individual cases succeed, and retrying without saving it erases the failure.

For example:

```text
When a two-case binary crashes, save its source hash and diagnostic before retrying one-case binaries.
```

Require a positive execution control, recursively split failed build batches, and isolate remaining cases after runtime failures. Save each checkpoint atomically. Retries increase compile time and isolated passes do not erase batch failures. A failed control produces not_run outcomes, not a formatting judgment.

Read in this order:

- [tools/conformance.py](https://github.com/nscottnichols/ffmt/blob/1d0552f3961a9a7cecf415b444c258e218f60e86/tools/conformance.py) — configuration
- [test/conformance/test_runner.py](https://github.com/nscottnichols/ffmt/blob/1d0552f3961a9a7cecf415b444c258e218f60e86/test/conformance/test_runner.py)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 6 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
python3 -m unittest discover -s test/conformance -p test_runner.py
python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --shard-size 2 --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 5; it remains draft until prerequisite human review.

Base: [`review-v2/base-tool-isolation`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-tool-isolation); 2 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
