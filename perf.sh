#!/bin/sh

# Set default values for CNF_OUT_DIR and PERF_RESULTS_DIR if not provided
CNF_OUT_DIR="${2:-./stdouts/}"
PERF_RESULTS_DIR="${3:-./perf_results/}"

mkdir -p ${CNF_OUT_DIR} ${PERF_RESULTS_DIR}

if [ -z "$1" ]; then
    echo "Usage: $0 <CNF filename> [CNF log directory] [perf log directory]"
    exit 1
fi

CNF="$1"
BASENAME=$(basename "$CNF")
BIN="./bin/linux/miniC2D"


# Run the perf command and store logs in the respective directories
echo "[$(date)]===================Running $CNF===================="
perf record \
    --call-graph dwarf,16384 \
    --user-callchains \
    ${BIN} --vtree_method 4 --cnf ${CNF} 1> ${CNF_OUT_DIR}${BASENAME}.log
# perf record --call-graph fp ${BIN} --vtree_method 4 --cnf ${CNF} 1> ${CNF_OUT_DIR}${BASENAME}.log

echo "[$(date)]===================Generating $CNF perf log===================="
perf report -g --call-graph=folded,0.01 --stdio | c++filt > ${PERF_RESULTS_DIR}${BASENAME}-perf.log

echo "[$(date)]====================Done running $CNF====================="
