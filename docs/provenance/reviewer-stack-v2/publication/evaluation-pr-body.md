JLSE provisioning, campaign records and paper artifacts currently travel with library development. Move that research work to this companion repository so `ffmt` builds and runs portable tests independently, while historical results remain tied to the exact source that produced them.

For example, `python3 tools/verify_provenance.py --ffmt-checkout ../ffmt --library-revision 4b8cf257fc68c5b20c0c493e34d1d90269e76fd9 --check-source-refs` verifies the original split through local Git objects even when the working checkout contains the newer review stack. It changes neither the checkout nor the qualification pins.

Evaluation accepts an existing checkout or an explicit immutable source revision, with a separately pinned runner. Receipts distinguish source, harness, evaluator, commands and hashes. Preserve original evidence, failures, paper artifacts, qualified/archive refs and ignored installations; add supplemental mappings and captures rather than rewriting historical records. This keeps old results reproducible at the cost of retaining historical runner dependencies. Changed library sources require fresh relevant qualification; old measurements do not qualify the new tree.

Read in this order:

- `README.md`, `platforms/library.json` and `tools/lib.py`: external source/runner selection and unchanged default pins.
- `tools/run.py`, `tools/report.py` and `test/`: execution, failures, export and offline regressions.
- `docs/provenance/README.md` and `tools/verify_provenance.py`: historical byte and ref verification.
- `docs/provenance/reviewer-stack-v2.md`: the single active library graph and old-to-new mapping, with exact captured attempts.
- `tools/review_stack/README.md` and `skills/ffmt-review-stack/SKILL.md`: reproducible intermediate assembly, CPU qualification and deliberate publication waves. Handwritten inputs remain visible.

Validation: `python3 -m unittest discover -s test -v` passes all 17 offline tests; `python3 -m unittest discover -s tools/review_stack -p test_capture.py -v` passes both capture safety tests. The verifier command above checks 25 preserved evidence files, two historical configurations, 17 historical headers/corpus, five refs and 19 original commits. Exact passing CPU evidence covers all 64 published library heads and the final collection; the collection passes both compiler registries, legacy checks, 36/36 CTest entries, installation and an independent installed consumer. Its evaluation smoke passes using the preserved clean source/runner pin and exact fmt pin. Raw commands, failures, optional skips and scheduler receipts are retained. These CPU checks establish neither exhaustive fmt compatibility nor fresh accelerator qualification; no GPU/Arm campaign was repeated.

---
Base: `main`. [Library review graph, evidence and snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md). This PR and all library PRs remain unmerged.
