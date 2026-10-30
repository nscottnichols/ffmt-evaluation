CUDA, HIP and OpenMP launchers need the same target-selection rules without importing each other.

For example:

```text
FFMT_GPU_ARCH=sm_80 selects sm_80 without consulting nvidia-smi.
```

Isolate architecture discovery behind two small functions; prefer explicit environment overrides and retain existing fallback targets. Fallback targets support compilation without a device, but do not prove execution compatibility. Execution controls remain required.

Read in this order:

- [tools/device_arch.py](https://github.com/nscottnichols/ffmt/blob/160bd04b3657bf2d33167f342bb0b360429f3c0b/tools/device_arch.py)
- [test/conformance/test_device_arch.py](https://github.com/nscottnichols/ffmt/blob/160bd04b3657bf2d33167f342bb0b360429f3c0b/test/conformance/test_device_arch.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_device_arch.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 10; it remains draft until prerequisite human review.

Base: [`review-v2/tool-isolation`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-isolation); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
