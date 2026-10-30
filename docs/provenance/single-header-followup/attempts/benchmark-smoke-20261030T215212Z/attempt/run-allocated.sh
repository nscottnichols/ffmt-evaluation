#!/bin/bash
set -euo pipefail
source /vast/projects/datascience/nnichols/ffmt_project/ffmt-evaluation/tools/jlse/environment.sh cpl
export COBALT_JOBID=1012529
exec python3 /vast/projects/datascience/nnichols/ffmt_project/ffmt-evaluation/artifacts/single-header-followup/benchmark-smoke-20261030T215212Z/run.py
