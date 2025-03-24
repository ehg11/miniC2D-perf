import json
import re

from config import CNF_DIR
from utils import (
    get_cnf_paths,
    get_function_percents_filename,
    get_perf_filename,
    get_total_time,
    init_dirs,
    log,
    run_miniC2D,
)


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


def get_miniC2D_fn_pcts(perf_filename: str):
    main_lines = []
    with open(perf_filename, "r") as f:
        for line in f.readlines():
            line = line.strip()
            res = match_main_line(line)
            if res:
                main_lines.append(res)

    fn_pcts = {
        ml["symbol"]: ml["self_pct"]
        for ml in main_lines
        if ml["sharedobject"] == "miniC2D"
    }
    fn_pcts = sorted(fn_pcts.items(), key=lambda x: x[1], reverse=True)
    fn_pcts = {k: v for k, v in fn_pcts}

    total_self_pct = sum(fn_pcts.values())
    total_self_pct_all = sum(ml["self_pct"] for ml in main_lines)
    log(f"Total self pct: {total_self_pct}/{total_self_pct_all}")

    return fn_pcts


def main():
    init_dirs()
    cnfs = get_cnf_paths(CNF_DIR)
    log(f"Found {len(cnfs)} CNFs to process: {cnfs}\n")

    for i, cnf_path in enumerate(cnfs):
        log(f"Processing CNF {i+1}/{len(cnfs)}: {cnf_path}")
        run_miniC2D(cnf_path)
        perf_filename = get_perf_filename(cnf_path)
        fn_pcts = get_miniC2D_fn_pcts(perf_filename)

        total_time = get_total_time(cnf_path)
        fn_pcts["_total_time"] = total_time

        fn_pcts_filename = get_function_percents_filename(cnf_path)
        with open(fn_pcts_filename, "w") as f:
            json.dump(fn_pcts, f, indent=4)


if __name__ == "__main__":
    main()
