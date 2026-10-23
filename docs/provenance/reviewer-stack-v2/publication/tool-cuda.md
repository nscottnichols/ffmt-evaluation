CUDA source compilation needs compiler-specific language and architecture flags, and successful compilation alone cannot establish that a kernel executed.

For example:

```text
--route cuda selects Clang CUDA; --route nvcc selects NVIDIA nvcc.
Both launch one execute_case(index) kernel, check launch/synchronization errors,
and require FFMT_DEVICE metadata before comparing stdout bytes.
```

Keep both CUDA compiler routes in one handwritten runtime adapter. Probe device availability, record the selected device, launch one thread, and synchronize before the process exits. The common fixture stays free of fmt device code. These Python tests inspect the generated source and flags; a CUDA device/runtime is still required to establish execution.

Read in this order:

- [tools/backend_cuda.py](https://github.com/nscottnichols/ffmt/blob/fe65f6fcdc7443a587986283387848303809eb1c/tools/backend_cuda.py)
- [test/conformance/test_adapter_cuda.py](https://github.com/nscottnichols/ffmt/blob/fe65f6fcdc7443a587986283387848303809eb1c/test/conformance/test_adapter_cuda.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_adapter_cuda.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. These portable tests inspect adapter generation and launch contracts; they do not qualify accelerator execution. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 10; it remains draft until prerequisite human review.

Base: [`review-v2/tool-adapter-support`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-adapter-support); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
