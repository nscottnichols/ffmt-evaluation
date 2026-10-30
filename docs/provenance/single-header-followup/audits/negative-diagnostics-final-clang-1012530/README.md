# Frozen validation capture

Status: `inputs_only`; Cobalt job `None`.

Visible files retain manifests, indices, scheduler receipts and handwritten inputs. `raw-logs.tar.gz` contains byte-preserved raw output and generated probes/cases, using paths relative to the listed original roots. `capture.json` inventories every captured file with its original absolute path, byte count, SHA-256 and storage location. Compiler products, source worktrees and CMake builds are excluded. The original ignored files remain untouched. Failure and cancellation are preserved as such.

Verify with `python3 tools/review_stack/capture.py --output /vast/projects/datascience/nnichols/ffmt_project/ffmt-evaluation/docs/provenance/single-header-followup/audits/negative-diagnostics-final-clang-1012530 --verify`.
