#!/usr/bin/env python

import json
import re
from collections import defaultdict
from pathlib import Path

EVAL_DIR = Path("experiments/scoping/data/scoping-scoping-minecraft-12-09-2025-eval")

ALGO_NAMES = {
    "scoping-experiments-fd": "FD",
    "scoping-experiments-FCM": "FCM",
}

SIZES = [1, 2, 5, 10, 12, 15, 20, 25]
SHOW_VARIABLES = True

# Manually collected data for F (= FC) configuration, indexed by size
F_DATA = {size: data for size, data in zip(SIZES, [
    {"variables": 13,  "facts": 26,  "operators": 16},
    {"variables": 24,  "facts": 48,  "operators": 48},
    {"variables": 64,  "facts": 127, "operators": 410},
    {"variables": 126, "facts": 251, "operators": 2777},
    {"variables": 150, "facts": 300, "operators": 4578},
    {"variables": 184, "facts": 369, "operators": 8776},
    {"variables": 243, "facts": 485, "operators": 20449},
    {"variables": 304, "facts": 609, "operators": 40101},
])}


def extract_size(run):
    """Extract N (number of agents) from problem path."""
    problem = run.get("problem", "")
    # Match minecraft_hunger_agents-N_seed-XXX.pddl
    match = re.search(r"agents-(\d+)_seed", problem)
    if match:
        return int(match.group(1))
    return None


def arithmetic_mean(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def load_and_aggregate(eval_dir):
    properties_file = eval_dir / "properties"
    with open(properties_file) as f:
        data = json.load(f)

    # Group runs by (size, algorithm)
    grouped = defaultdict(lambda: defaultdict(list))

    for run_id, run in data.items():
        if not isinstance(run, dict):
            continue

        algo = run.get("algorithm")
        if algo not in ALGO_NAMES:
            continue

        size = extract_size(run)
        if size is None or size not in SIZES:
            continue

        algo_name = ALGO_NAMES[algo]

        grouped[(size, algo_name)]["coverage"].append(run.get("coverage"))
        grouped[(size, algo_name)]["operators"].append(run.get("translator_operators"))
        grouped[(size, algo_name)]["facts"].append(run.get("translator_facts"))
        grouped[(size, algo_name)]["variables"].append(run.get("translator_variables"))
        grouped[(size, algo_name)]["pruning_time"].append(
            run.get("translator_time_scoping")
        )
        grouped[(size, algo_name)]["total_time"].append(run.get("total_time"))

    # Aggregate
    results = {}
    for (size, algo), attrs in grouped.items():
        results[(size, algo)] = {
            "coverage": sum(attrs["coverage"]),
            "operators": arithmetic_mean(attrs["operators"]),
            "facts": arithmetic_mean(attrs["facts"]),
            "variables": arithmetic_mean(attrs["variables"]),
            "pruning_time": arithmetic_mean(attrs["pruning_time"]),
            "total_time": arithmetic_mean(attrs["total_time"]),
        }

    return results


def format_value(val, decimals=2):
    if val is None:
        return "-"
    if isinstance(val, int):
        return f"{val:,}"
    if isinstance(val, float):
        if val >= 1000:
            return f"{val:,.0f}"
        return f"{val:.{decimals}f}"
    return str(val)


def generate_latex(results):
    # Build column groups: (header, ncols, sub_headers, row_fn)
    FD_FC_FCM = [r"{FD}", r"{F$^\dagger$}", r"{FCM}"]
    groups = [
        ("Coverage", 3, FD_FC_FCM,
         lambda fd, f, fcm: [format_value(fd.get("coverage")), format_value(fd.get("coverage")), format_value(fcm.get("coverage"))]),
        ("Actions", 3, FD_FC_FCM,
         lambda fd, f, fcm: [format_value(fd.get("operators"), 0), format_value(f.get("operators"), 0), format_value(fcm.get("operators"), 0)]),
        ("Facts", 3, FD_FC_FCM,
         lambda fd, f, fcm: [format_value(fd.get("facts"), 0), format_value(f.get("facts"), 0), format_value(fcm.get("facts"), 0)]),
    ]
    if SHOW_VARIABLES:
        groups.append(
            ("Variables", 3, FD_FC_FCM,
             lambda fd, f, fcm: [format_value(fd.get("variables"), 0), format_value(f.get("variables"), 0), format_value(fcm.get("variables"), 0)]),
        )
    groups += [
        ("Prune (s)", 1, ["{FCM}"],
         lambda fd, f, fcm: [format_value(fcm.get("pruning_time"))]),
        ("Total (s)", 2, ["{FD}", "{FCM}"],
         lambda fd, f, fcm: [format_value(fd.get("total_time")), format_value(fcm.get("total_time"))]),
    ]

    ncols = sum(g[1] for g in groups)
    col_spec = "r " + " ".join("r" * g[1] for g in groups)

    # Build header rows
    top_headers = []
    cmidrules = []
    sub_headers = []
    col = 2  # 1-indexed, column 1 is size
    for header, nc, subs, _ in groups:
        if nc == 1:
            top_headers.append(r"\textbf{" + header + "}")
        else:
            top_headers.append(r"\multicolumn{" + str(nc) + r"}{c}{\textbf{" + header + "}}")
        cmidrules.append(r"\cmidrule(lr){" + f"{col}-{col + nc - 1}" + "}")
        sub_headers.extend(subs)
        col += nc

    I = "    "  # 4-space indent unit

    lines = []
    lines.append(r"\begin{minipage}[t]{0.68\textwidth}")
    lines.append(I * 2 + r"\vspace{30pt}")
    lines.append(I * 2 + r"\centering")
    lines.append(I * 2 + r"\resizebox{\linewidth}{!}{")
    lines.append(I * 2 + r"\begin{tabular}{" + col_spec + "}")
    lines.append(I * 3 + r"\toprule")
    lines.append(I * 3 + r"\textbf{Size} & " + " & ".join(top_headers) + r" \\")
    lines.append(I * 3 + " ".join(cmidrules))
    lines.append(I * 3 + "& " + " & ".join(sub_headers) + r" \\")
    lines.append(I * 3 + r"\midrule")

    for size in SIZES:
        fd = results.get((size, "FD"), {})
        fcm = results.get((size, "FCM"), {})
        f = F_DATA.get(size, {})

        row = [str(size)]
        for _, _, _, row_fn in groups:
            row.extend(row_fn(fd, f, fcm))

        lines.append(I * 3 + " & ".join(row) + r" \\")

    lines.append(I * 3 + r"\bottomrule")
    lines.append(I * 2 + r"\end{tabular}")
    lines.append(I * 2 + "}")
    lines.append(I * 2 + r"\captionof{table}{Results for Minecraft domain, varying the number of agents. Fact-based relevance analysis reduces actions by up to 99\%, facts and variables by up to 90\%, and solves 50 more problems than the baseline Fast Downward algorithm. The $^\dagger$ symbol indicates that results for FC are the same as F.}")
    lines.append(I * 2 + r"\label{tab:minecraft-hunger}")
    lines.append(I + r"\end{minipage}%")

    return "\n".join(lines)


def main():
    results = load_and_aggregate(EVAL_DIR)
    latex = generate_latex(results)
    print(latex)


if __name__ == "__main__":
    main()
