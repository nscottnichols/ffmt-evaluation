#!/bin/bash
set -euo pipefail
ffmt_stack_directory=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if [ -z "${COBALT_JOBID:-}" ]; then
  echo "Consumer validation requires a Cobalt compute allocation." >&2
  exit 2
fi
if [ -f /etc/profile.d/modules.sh ]; then source /etc/profile.d/modules.sh; fi
if type module >/dev/null 2>&1; then
  module use /soft/modulefiles
  module load gcc/13.3.0
  module load llvm/release-22.1.8
  module load cmake/3.28.3
fi
export FFMT_STACK_CXX=${FFMT_STACK_CXX:-/soft/compilers/llvm/release-22.1.8/bin/clang++}
export LD_LIBRARY_PATH=/vast/projects/datascience/nnichols/ffmt_project/ffmt/software/rome/install/host-runtime/lib:${LD_LIBRARY_PATH:-}
export LC_ALL=C GOMAXPROCS=2
exec python3 "$ffmt_stack_directory/consumer.py" "$@"
