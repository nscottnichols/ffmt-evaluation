#!/bin/bash
set -euo pipefail
ffmt_evaluation=/vast/projects/datascience/nnichols/ffmt_project/ffmt-evaluation
source "$ffmt_evaluation/tools/jlse/environment.sh" "${FFMT_VALIDATION_SYSTEM:-rome}"
exec python3 "$ffmt_evaluation/artifacts/single-header-followup-20261030/validate_portable.py" "$@"
