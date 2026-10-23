#!/bin/bash
# Rebuild the paper in a fresh directory without changing frozen evidence.
set -euo pipefail
ffmt_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export TEXMFHOME="$ffmt_root/software/local/texmf"
ffmt_install_tex=0
ffmt_requested_output=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --install-tex) ffmt_install_tex=1; shift ;;
    --output)
      if [ "$#" -lt 2 ]; then echo '--output requires a fresh directory' >&2; exit 2; fi
      ffmt_requested_output=$2; shift 2 ;;
    --help|-h)
      echo 'usage: tools/build_paper.sh [--install-tex] [--output FRESH_DIRECTORY]'
      exit 0 ;;
    *) echo 'usage: tools/build_paper.sh [--install-tex] [--output FRESH_DIRECTORY]' >&2; exit 2 ;;
  esac
done
if [ "$ffmt_install_tex" -eq 1 ]; then
  if [ ! -f "$TEXMFHOME/tlpkg/texlive.tlpdb" ]; then
    tlmgr --usermode --usertree "$TEXMFHOME" init-usertree
  fi
  tlmgr --usermode --usertree "$TEXMFHOME" install microtype amsmath booktabs tools geometry xcolor listings xurl hyperref
fi
command -v pdflatex >/dev/null
ffmt_output=$(python3 - "$ffmt_root" "$ffmt_requested_output" <<'PY'
import datetime
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
requested = sys.argv[2]
if requested:
    output = Path(requested).expanduser()
    if not output.is_absolute():
        output = root / output
else:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = root / "artifacts/paper-build" / stamp
output = output.resolve()
try:
    output.relative_to(root)
except ValueError:
    pass
else:
    try:
        output.relative_to((root / "artifacts").resolve())
    except ValueError:
        raise SystemExit("Paper output inside this repository must be under ignored artifacts/")
if output.exists() or output.is_symlink():
    raise SystemExit("Paper output must be a fresh directory: " + str(output))
output.mkdir(parents=True)
print(output)
PY
)
cp "$ffmt_root/docs/paper/ffmt.tex" "$ffmt_output/ffmt.tex"
python3 - "$ffmt_root" "$ffmt_output" <<'PY'
import hashlib
import json
from pathlib import Path
import sys
root, output = map(Path, sys.argv[1:])
names = ["docs/paper/ffmt.tex", "docs/results/qualification.json",
         "docs/results/benchmarks.json", "docs/results/coverage.json",
         "tools/paper_tables.py", "tools/build_paper.sh"]
data = dict(schema_version=1, evaluation_root=str(root), output=str(output),
            input_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names})
(output / "build-inputs.json").write_text(json.dumps(data, indent=2) + "\n")
PY
python3 "$ffmt_root/tools/paper_tables.py" --qualification "$ffmt_root/docs/results/qualification.json" \
  --benchmarks "$ffmt_root/docs/results/benchmarks.json" --coverage "$ffmt_root/docs/results/coverage.json" \
  --output "$ffmt_output/results.tex" --selection-output "$ffmt_output/paper-selection.json"
cd "$ffmt_output"
pdflatex -interaction=nonstopmode -halt-on-error ffmt.tex
pdflatex -interaction=nonstopmode -halt-on-error ffmt.tex
printf 'Rebuilt paper: %s/ffmt.pdf\n' "$ffmt_output"
