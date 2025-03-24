import os
from datetime import datetime
import subprocess
import sys

from config import (
    ALL_FUNCTIONS,
    CNF_DIR,
    CNF_OUT_DIR,
    FUNCTION_PERCENTS_DIR,
    PERF_RESULTS_DIR,
)


def log(*args, sep=" ", end="\n", file=sys.stdout, flush=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}]", *args, sep=sep, end=end, file=file, flush=flush)


def init_dirs():
    os.makedirs(CNF_OUT_DIR, exist_ok=True)
    os.makedirs(PERF_RESULTS_DIR, exist_ok=True)
    os.makedirs(FUNCTION_PERCENTS_DIR, exist_ok=True)


def get_perf_filename(cnf_path: str):
    basename = os.path.basename(cnf_path)
    return f"{PERF_RESULTS_DIR}{basename}-perf.log"


def get_function_percents_filename(cnf_path: str):
    basename = os.path.basename(cnf_path)
    return f"{FUNCTION_PERCENTS_DIR}{basename}.json"


def get_cnf_out_filename(cnf_path: str):
    basename = os.path.basename(cnf_path)
    return f"{CNF_OUT_DIR}{basename}.log"


def get_cnf_paths(cnf_dir):
    cnfs = [os.path.join(cnf_dir, f) for f in os.listdir(cnf_dir) if f.endswith(".cnf")]

    def _skip_condition(cnf):
        fn_pcts_filename = get_function_percents_filename(cnf)
        return os.path.exists(fn_pcts_filename)

    # remove CNFs that have already been processed
    cnfs = [f for f in cnfs if not _skip_condition(f)]

    return cnfs


def get_function_names():
    function_names = []
    with open(ALL_FUNCTIONS, "r") as f:
        for line in f.readlines():
            line = line.split(maxsplit=1)[0]
            function_names.append(line)

    return set(function_names)


def run_miniC2D(cnf_path: str):
    log(f"Running miniC2D on {cnf_path}")

    # NOTE: using default vtree method (0) requires special libraries for
    # hypergraph partitioning. We use min-fill elimination order (4) instead.
    process = subprocess.Popen(
        ["./perf.sh", cnf_path, CNF_OUT_DIR, PERF_RESULTS_DIR],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    process.wait()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    log(f"Finished running miniC2D on {cnf_path}")

    # remove any .nnf files
    # for storage purposes
    for f in os.listdir(CNF_DIR):
        if f.endswith(".nnf"):
            os.remove(os.path.join(CNF_DIR, f))


def get_total_time(cnf_path: str):
    cnf_out_path = get_cnf_out_filename(cnf_path)

    with open(cnf_out_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("Total Time"):
                return float(line.rsplit(maxsplit=1)[1].replace("s", ""))

    return None
