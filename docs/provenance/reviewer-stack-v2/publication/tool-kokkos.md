A Kokkos installation can select a different DefaultExecutionSpace from the route requested by a test, producing a misleading backend result.

For example:

```text
--route kokkos-cuda requires DefaultExecutionSpace::name() == "Cuda".
A Serial installation returns 77 before formatting, rather than being reported
as a successful CUDA comparison.
```

Wrap the existing base compiler adapter with Kokkos includes/link flags, require the requested execution space, run one parallel_for, and fence before finalization. Advertise an accelerator wrapper only when its base adapter is present. Kokkos must be installed externally with the requested execution space. Source-generation tests cover the guard, launch and lifecycle, while runtime/device availability remains unqualified here.

Read in this order:

- [tools/backend_kokkos.py](https://github.com/nscottnichols/ffmt/blob/8c25ab61e046087f5330127cd479befcadbe8cb4/tools/backend_kokkos.py)
- [test/conformance/test_adapter_kokkos.py](https://github.com/nscottnichols/ffmt/blob/8c25ab61e046087f5330127cd479befcadbe8cb4/test/conformance/test_adapter_kokkos.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_adapter_kokkos.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. These portable tests inspect adapter generation and launch contracts; they do not qualify accelerator execution. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 10; it remains draft until prerequisite human review.

Base: [`review-v2/tool-isolation`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-isolation); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
