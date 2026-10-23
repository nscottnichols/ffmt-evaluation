SYCL implementations may select different devices, and asynchronous kernel errors need to be observed before stdout comparison.

For example:

```text
--route sycl uses icpx -fsycl; --route acpp uses AdaptiveCpp generic targets.
The launcher requests sycl::gpu_selector_v, records the device name/fp64 support,
and waits with wait_and_throw() before judging output.
```

Keep Intel SYCL and AdaptiveCpp compiler flags in one handwritten SYCL adapter. A mandatory GPU selector and explicit exception-aware wait prevent CPU fallback or pending errors from looking like a formatting pass. The caller supplies a working SYCL GPU runtime. Python tests check selection, launch/wait structure and flag overrides; accelerator execution is not qualified here.

Read in this order:

- [tools/backend_sycl.py](https://github.com/nscottnichols/ffmt/blob/d7aecfab035ffe7ff0963149ae7f25745cc0b365/tools/backend_sycl.py)
- [test/conformance/test_adapter_sycl.py](https://github.com/nscottnichols/ffmt/blob/d7aecfab035ffe7ff0963149ae7f25745cc0b365/test/conformance/test_adapter_sycl.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_adapter_sycl.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. These portable tests inspect adapter generation and launch contracts; they do not qualify accelerator execution. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 10; it remains draft until prerequisite human review.

Base: [`review-v2/tool-isolation`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-isolation); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
