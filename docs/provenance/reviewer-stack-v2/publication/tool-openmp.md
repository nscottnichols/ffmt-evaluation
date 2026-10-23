OpenMP target regions can silently run on the initial host device, allowing a host result to masquerade as accelerator conformance.

For example:

```text
--route omp-cuda / omp-hip use Clang NVPTX / AMDGPU offload flags.
--route omp-spirv uses icpx -fiopenmp -fopenmp-targets=spir64.
An initial-device control returns 77 before any output case is judged.
```

Share one target-region launcher across the three compiler routes, require omp_is_initial_device() to be false, record the device number, and keep route-specific flags beside the launcher. Host fallback becomes a failed execution control, not a formatting pass. Portable tests inspect source generation and flags; they do not establish an available OpenMP device runtime.

Read in this order:

- [tools/backend_openmp.py](https://github.com/nscottnichols/ffmt/blob/93f6cb1ff2af9a3d0488dfd73a38c3e2eb8f1cfc/tools/backend_openmp.py)
- [test/conformance/test_adapter_openmp.py](https://github.com/nscottnichols/ffmt/blob/93f6cb1ff2af9a3d0488dfd73a38c3e2eb8f1cfc/test/conformance/test_adapter_openmp.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_adapter_openmp.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. These portable tests inspect adapter generation and launch contracts; they do not qualify accelerator execution. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 10; it remains draft until prerequisite human review.

Base: [`review-v2/tool-adapter-support`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-adapter-support); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
