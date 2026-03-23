#!/usr/bin/env python

from math import exp, log
from pathlib import Path

from downward.reports.absolute import AbsoluteReport
from lab.reports import Attribute, geometric_mean


def geometric_mean_nonzero(values):
    values = [v for v in values if v and v > 0]
    if not values:
        return None
    return exp(sum(log(v) for v in values) / len(values))


# EVAL_DIR = Path("experiments/scoping/data/scoping-scoping-ipc-11-29-2025-eval")
EVAL_DIR = Path("experiments/scoping/data/scoping-scoping-minecraft-12-09-2025-eval")

ALGO_NAMES = {
    "scoping-experiments-basic": "None",
    "scoping-experiments-fd": "FD",
    "scoping-experiments-V": "V",
    "scoping-experiments-F": "F",
    "scoping-experiments-FC": "FC",
    "scoping-experiments-FCM": "FCM",
    "scoping-experiments-FCMR": "FCMR",
    "scoping-experiments-FCMRL": "FCMRL",
}

ALGO_ORDER = ["None", "FD", "V", "F", "FC", "FCM", "FCMR", "FCMRL"]

NO_SCOPING_ALGOS = {"None", "FD"}


def rename_and_validate(run):
    algo = run.get("algorithm")
    if algo in ALGO_NAMES:
        run["algorithm"] = ALGO_NAMES[algo]

    scoping_time = run.get("translator_time_scoping")
    if scoping_time is not None:
        run["pruning_time"] = scoping_time

    new_algo = run.get("algorithm")
    if new_algo not in NO_SCOPING_ALGOS:
        if scoping_time is None:
            return False

    return run


PRUNING_TIME = Attribute(
    "pruning_time",
    absolute=True,
    function=geometric_mean_nonzero,
    min_wins=True,
)

ATTRIBUTES = [
    Attribute("translator_operators", function=sum),
    Attribute("translator_facts", function=sum),
    Attribute("translator_variables", function=sum),
    Attribute("translator_task_size", function=sum),
    Attribute("coverage", function=sum, min_wins=False),
    Attribute("translator_time_done", absolute=True, function=sum),
    Attribute("pruning_time", absolute=True, function=sum),
    Attribute("search_time", absolute=True, function=sum),
    Attribute("total_time", absolute=True, function=sum),
]

report = AbsoluteReport(
    attributes=ATTRIBUTES,
    filter=rename_and_validate,
    filter_algorithm=ALGO_ORDER,
)
report(str(EVAL_DIR), "report.html")
