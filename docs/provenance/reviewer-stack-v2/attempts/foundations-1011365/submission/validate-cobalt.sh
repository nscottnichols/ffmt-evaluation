#!/bin/bash
# Submit only after validate.py INDEX --preflight passes. Cobalt opens its cwd
# before mounting /vast, so submit with --cwd /home/nnichols and an absolute script.
# qsub --mode script -q rome_7742 -n 1 -t 240 --cwd /home/nnichols \
#   /bin/bash /ABS/EVALUATION/tools/review_stack/validate-cobalt.sh /ABS/INDEX.json
set -euo pipefail
if [ -z "${COBALT_JOBID:-}" ]; then
  echo "Review-stack compilation requires a Cobalt compute allocation." >&2
  exit 2
fi
ffmt_review_tools=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ffmt_review_evaluation=$(cd "$ffmt_review_tools/../.." && pwd)
# Source the existing Rome setup; retain all local installations and raw evidence.
source "$ffmt_review_evaluation/tools/jlse/environment.sh" rome
export FFMT_STACK_CLANG=${FFMT_STACK_CLANG:-/soft/compilers/llvm/release-22.1.8/bin/clang++}
export FFMT_STACK_GCC=${FFMT_STACK_GCC:-/soft/compilers/gcc/13.3.0/x86_64-suse-linux/bin/g++}
export FFMT_VALIDATION_WRAPPER="$ffmt_review_tools/validate-cobalt.sh"
export LC_ALL=C GOMAXPROCS=2
exec python3 "$ffmt_review_tools/validate.py" "$@"
