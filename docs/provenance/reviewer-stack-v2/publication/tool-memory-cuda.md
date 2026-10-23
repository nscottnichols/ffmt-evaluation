CUDA stdout can succeed while numeric conversion or bounded output counts in accelerator memory are wrong.

For example:

```text
cudaMemcpyHostToDevice -> memory_kernel -> cudaDeviceSynchronize
-> cudaMemcpyDeviceToHost -> serialize(input, output)
```

Allocate CUDA input/output buffers, copy input encodings, zero output, launch memory_kernel, check errors/synchronize, and copy framed results back. The numeric formatting body remains the shared handwritten template. Runtime execution remains hardware-dependent; source-generation and host record tests validate structure but do not establish accelerator execution.

Read in this order:

- [tools/backend_cuda.py](https://github.com/nscottnichols/ffmt/blob/17288fc322f07956b78999bf438f10b7f3a4086b/tools/backend_cuda.py) — numeric_launcher
- [test/conformance/numeric_memory.cpp.in](https://github.com/nscottnichols/ffmt/blob/17288fc322f07956b78999bf438f10b7f3a4086b/test/conformance/numeric_memory.cpp.in)
- [test/conformance/test_memory_cuda.py](https://github.com/nscottnichols/ffmt/blob/17288fc322f07956b78999bf438f10b7f3a4086b/test/conformance/test_memory_cuda.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 7 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_memory_cuda.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. These portable tests inspect adapter generation and launch contracts; they do not qualify accelerator execution. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 11; it remains draft until prerequisite human review.

Base: [`review-v2/base-tool-memory-cuda`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-tool-memory-cuda); 2 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
