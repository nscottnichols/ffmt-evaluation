# Working manuscript

`ffmt.tex` revises the supplied outline for the implemented shared engine and
the captured JLSE experiments. It is a working paper, not a submitted artifact.
Qualification tables are generated from explicitly selected evidence; missing
measurements and failing configurations retain their status.

`outline-v2.tex` preserves the supplied 21 October source as historical input.
Its statements about the old two-path implementation and unexecuted tests are
not descriptions of the current implementation. Input SHA256:
`519add4175236b66b5c52300b6a7f00a0accec5bc4894a894eaea7911dcd73f0`.

Rebuild from the evaluation repository root using the captured compact evidence:

```sh
tools/build_paper.sh
```

This requires an existing TeX Live installation with `pdflatex`. If its optional
packages are missing, use `tools/build_paper.sh --install-tex`; packages install
into ignored `software/local/texmf`. The helper uses that directory as
`TEXMFHOME`. Each rebuild creates a fresh ignored
`artifacts/paper-build/<UTC-timestamp>/` directory and copies `ffmt.tex` there.
It regenerates `results.tex`, `paper-selection.json`, TeX logs and `ffmt.pdf`
inside that directory. `build-inputs.json` records hashes of the manuscript,
evidence inputs and build tools. The committed paper, generated tables and
selection ledger remain unchanged.

Use `tools/build_paper.sh --output /path/to/fresh-directory` to select another
destination. Existing destinations are rejected. Inside this repository,
destinations must be under ignored `artifacts/`; evidence and source directories
are protected. A destination elsewhere can be used for export or review.
The selection ledger identifies every displayed timing row and its header
fingerprint; the full benchmark JSON retains earlier snapshots.

The committed reading copy is `ffmt.pdf`. Raw logs, binaries and installations
remain under ignored artifacts/software directories. The JSON evidence retains
source hashes and command identities; numbers in this paper describe those
captured snapshots and their stated measurement conditions.

The paper source, generated tables, outline and reading PDF are preserved byte
for byte from the original campaign. Their historical source revisions and
commands are interpreted through [split provenance](../provenance/README.md).
Rebuilding the PDF is optional and may change PDF metadata; it does not justify
rerunning hardware measurements. The library itself has no TeX dependency.
