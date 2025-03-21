#!/bin/sh

# Set default values for CNF_OUT_DIR and PERF_RESULTS_DIR if not provided
CNF_OUT_DIR="${2:-./stdouts/}"
PERF_RESULTS_DIR="${3:-./perf_results/}"

if [ -z "$1" ]; then
    echo "Usage: $0 <CNF filename> [CNF log directory] [perf log directory]"
    exit 1
fi

CNF="$1"
BASENAME=$(basename "$CNF")
BIN="./bin/linux/miniC2D"

echo "===================Running $CNF===================="

# Run the perf command and store logs in the respective directories
perf record --call-graph dwarf,8192 -F 1000 --aio=2 ${BIN} --vtree_method 4 --cnf ${CNF} 1> ${CNF_OUT_DIR}${BASENAME}.log
perf report --call-graph=folded,0.01 --stdio | c++filt > ${PERF_RESULTS_DIR}${BASENAME}-perf.log
