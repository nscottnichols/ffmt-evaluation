Kokkos stdout can succeed while numeric conversion or bounded output counts in accelerator memory are wrong.

For example:

```text
host mirror -> deep_copy(device_input) -> parallel_for(format_record)
-> create_mirror_view_and_copy(HostSpace, device_output) -> serialize
```

Require the requested DefaultExecutionSpace, deep-copy input through a host mirror, format into a device View with parallel_for, and copy a HostSpace mirror back before serialization and finalization. Runtime execution remains hardware-dependent; source-generation and host record tests validate structure but do not establish accelerator execution.

Read in this order:

- [tools/backend_kokkos.py](https://github.com/nscottnichols/ffmt/blob/50540f30832e14ee0a67ee5bfbed173ecb694c83/tools/backend_kokkos.py) — numeric_launcher
- [test/conformance/numeric_memory.cpp.in](https://github.com/nscottnichols/ffmt/blob/50540f30832e14ee0a67ee5bfbed173ecb694c83/test/conformance/numeric_memory.cpp.in)
- [test/conformance/test_memory_kokkos.py](https://github.com/nscottnichols/ffmt/blob/50540f30832e14ee0a67ee5bfbed173ecb694c83/test/conformance/test_memory_kokkos.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 7 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_memory_kokkos.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. These portable tests inspect adapter generation and launch contracts; they do not qualify accelerator execution. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 11; it remains draft until prerequisite human review.

Base: [`review-v2/base-tool-memory-kokkos`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-tool-memory-kokkos); 2 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
