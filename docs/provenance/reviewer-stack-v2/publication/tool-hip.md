HIP and chipStar share a launch API but need different compiler flag choices; a failed launch must not be mistaken for a formatting mismatch.

For example:

```text
--route hip uses hipcc with the selected ROCm offload architecture.
--route chipstar uses the externally selected HIP runtime.
Both check hipLaunchKernelGGL, the last launch error and device synchronization.
```

Use one handwritten HIP runtime adapter for the two compiler routes. Keep architecture selection on the native HIP route, and retain device properties and launch failures as separate evidence. The caller supplies the appropriate hipcc/runtime environment. Portable tests check source generation and flag overrides; they do not execute a HIP or chipStar kernel.

Read in this order:

- [tools/backend_hip.py](https://github.com/nscottnichols/ffmt/blob/f50afd9c6852f5d60d9eabdb45ff094281bab2b6/tools/backend_hip.py)
- [test/conformance/test_adapter_hip.py](https://github.com/nscottnichols/ffmt/blob/f50afd9c6852f5d60d9eabdb45ff094281bab2b6/test/conformance/test_adapter_hip.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_adapter_hip.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. These portable tests inspect adapter generation and launch contracts; they do not qualify accelerator execution. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 10; it remains draft until prerequisite human review.

Base: [`review-v2/tool-adapter-support`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-adapter-support); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
