#!/bin/bash
set -euo pipefail
source /vast/projects/datascience/nnichols/ffmt_project/ffmt-evaluation/tools/jlse/environment.sh skylake
export LC_ALL=C GOMAXPROCS=2
exec python3 /vast/projects/datascience/nnichols/ffmt_project/ffmt-evaluation/artifacts/single-header-followup/backend-20261030T213049Z/run.py
