import sys
import os
import subprocess
import re
import json
from datetime import datetime

CNF_OUT_DIR = "./stdouts/"
PERF_RESULTS_DIR = "./perf_results/"
CNF_DIR = "./cnfs/"
ALL_FUNCTIONS = "./ctags.txt"
FUNCTION_PERCENTS_DIR = "./function_percents/"


def log(*args, sep=" ", end="\n", file=sys.stdout, flush=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}]", *args, sep=sep, end=end, file=file, flush=flush)


def get_perf_filename(cnf_path: str):
    basename = os.path.basename(cnf_path)
    return f"{PERF_RESULTS_DIR}{basename}-perf.log"


def get_function_percents_filename(cnf_path: str):
    basename = os.path.basename(cnf_path)
    return f"{FUNCTION_PERCENTS_DIR}{basename}.json"


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


def run_miniC2D(cnf_path: str) -> str:
    """Run miniC2D and capture its stdout."""
    output = []
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


def match_main_line(line):
    children_pct_pattern = r"\s*(?P<children_pct>\d+\.\d+)%"
    self_pct_pattern = r"\s+(?P<self_pct>\d+\.\d+)%"
    command_pattern = r"\s+(?P<command>\S+)"
    sharedobject_pattern = r"\s+(?P<sharedobject>\S+)"
    symbol_pattern = r"\s+\[\.\]\s+(?P<symbol>\S+)"
    pattern = (
        "^"
        + children_pct_pattern
        + self_pct_pattern
        + command_pattern
        + sharedobject_pattern
        + symbol_pattern
        + "$"
    )

    match = re.match(pattern, line)
    if match:
        res = match.groupdict()
        res["children_pct"] = float(res["children_pct"])
        res["self_pct"] = float(res["self_pct"])
        return res
    else:
        return None


def get_function_percents(perf_filename: str):
    target_functions = get_function_names()
    fn_pcts = {}
    for fn in target_functions:
        fn_pcts[fn] = 0

    with open(perf_filename, "r") as f:
        lines = f.readlines()
        skip_section = False
        current_fn = None
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) == 0:
                break
            if line[0] == "#":
                continue
            res = match_main_line(line)
            if res:
                current_fn = res["symbol"]
                if current_fn not in target_functions:
                    skip_section = True
                    continue
                skip_section = False
            else:
                if skip_section:
                    continue
                pct, callstack = line.split(maxsplit=1)
                pct = float(pct.replace("%", ""))
                callstack = callstack.split(";")
                for fn in reversed(callstack):
                    if fn in target_functions:
                        if fn == current_fn:
                            fn_pcts[current_fn] += pct
                        break
    total_fn_pcts = sum(fn_pcts.values())
    log(f"Total function percents: {total_fn_pcts}")
    if total_fn_pcts > 100:
        for fn, pct in fn_pcts.items():
            norm_pct = pct / total_fn_pcts * 100
            fn_pcts[fn] = norm_pct
    fn_pcts = sorted(fn_pcts.items(), key=lambda x: x[1], reverse=True)
    fn_pcts = {fn: pct for fn, pct in fn_pcts}

    return fn_pcts


def main():
    cnfs = get_cnf_paths(CNF_DIR)
    log(f"Found {len(cnfs)} CNFs to process: {cnfs}\n")

    for cnf_path in cnfs:
        run_miniC2D(cnf_path)
        perf_filename = get_perf_filename(cnf_path)
        function_percents = get_function_percents(perf_filename)

        # save function percents
        function_percents_filename = get_function_percents_filename(cnf_path)
        with open(function_percents_filename, "w") as f:
            json.dump(function_percents, f, indent=4)


if __name__ == "__main__":
    main()
