from collections import defaultdict
import itertools
import os

from lab.environments import LocalEnvironment
from lab.experiment import Experiment
from lab.reports import Attribute

from parser import SaSParser
import common_setup
from common_setup import IssueConfig, IssueExperiment

from downward.reports.scatter import ScatterPlotReport
from downward.reports.absolute import AbsoluteReport

# Path to the first experiment's data (with V, F, FC, FCM)
FIRST_EXP_DATA = "data/scoping-scoping-ipc-11-29-2025-eval"
# Path to the second experiment's data (with FCMR, FCMRL)
SECOND_EXP_DATA = "data/scoping-scoping-ipc-11-29-2025_bug_fix-eval"

REVISIONS = ["scoping-experiments"]

# Create a new experiment just for fetching and plotting
exp = Experiment()

# Fetch data from both experiments
exp.add_fetcher(FIRST_EXP_DATA)
exp.add_fetcher(SECOND_EXP_DATA)

attributes = [
  "translator_axioms",
  "translator_derived_variables",
  "translator_facts",
  "translator_goal_facts",
  "translator_mutex_groups",
  "translator_operators",
  "translator_peak_memory",
  "translator_task_size",
  "translator_time_done",
  "translator_time_writing_output",
  "translator_total_mutex_groups_size",
  "translator_variables",
  "coverage",
  "error",
  "run_dir",
  "total_time",
  "search_time",
]

def rename_algorithms(run):
    name = run["algorithm"]
    paper_names = {f"{REVISIONS[0]}-basic": "No scoping", f"{REVISIONS[0]}-fd": "FD"}

    for a in ["V", "F", "FC", "FCM", "FCMR", "FCMRL"]:
        paper_names[f"{REVISIONS[0]}-{a}"] = a
    run["algorithm"] = paper_names[name]
    return run

algos = ["No scoping", "FD", "V", "F", "FC", "FCM", "FCMR", "FCMRL"]

# Add absolute report
exp.add_report(
    AbsoluteReport(attributes=attributes, filter=[rename_algorithms], filter_algorithm=algos),
    outfile="report.html"
)

class OpsFilters:
    """
    >>> from downward.reports.absolute import AbsoluteReport
    >>> filters = OpsFilters()
    >>> report = AbsoluteReport(filter=[filters.store_ops, filters.add_op_diff])
    """

    def __init__(self, alg1, alg2):
        self.alg1_ops = defaultdict(int)
        self.alg2_ops = defaultdict(int)
        self.alg1 = alg1
        self.alg2 = alg2

    def _get_task(self, run):
        return (run["domain"], run["problem"])

    def _compute_op_diff(self, run):
        if self.alg1_ops[self._get_task(run)] is None:
            return 0
        if self.alg2_ops[self._get_task(run)] is None:
            return 0
        if self.alg1_ops[self._get_task(run)] == self.alg2_ops[self._get_task(run)]:
            return 0
        return 1

    def store_ops(self, run):
        ops = run.get("translator_operators")
        alg = run.get("algorithm")
        if alg == self.alg1:
            self.alg1_ops[self._get_task(run)] = ops
        if alg == self.alg2:
            self.alg2_ops[self._get_task(run)] = ops
        return True

    def add_op_diff(self, run):
        run["op_diff"] = self._compute_op_diff(run)
        return run

class FactsFilters:
    """
    >>> from downward.reports.absolute import AbsoluteReport
    >>> filters = FactsFilters()
    >>> report = AbsoluteReport(filter=[filters.store_facts, filters.add_fact_diff])
    """

    def __init__(self, alg1, alg2):
        self.alg1_facts = defaultdict(int)
        self.alg2_facts = defaultdict(int)
        self.alg1 = alg1
        self.alg2 = alg2

    def _get_task(self, run):
        return (run["domain"], run["problem"])

    def _compute_fact_diff(self, run):
        if self.alg1_facts[self._get_task(run)] is None:
            return 0
        if self.alg2_facts[self._get_task(run)] is None:
            return 0
        if self.alg1_facts[self._get_task(run)] == self.alg2_facts[self._get_task(run)]:
            return 0
        return 1

    def store_facts(self, run):
        f = run.get("translator_facts")
        alg = run.get("algorithm")
        if alg == self.alg1:
            self.alg1_facts[self._get_task(run)] = f
        if alg == self.alg2:
            self.alg2_facts[self._get_task(run)] = f
        return True

    def add_fact_diff(self, run):
        run["fact_diff"] = self._compute_fact_diff(run)
        return run


def domain_as_category(run1, run2):
    # run2['domain'] has the same value, because we always
    # compare two runs of the same problem.
    return run1["domain"]

def all_op_diff(run):
    if run["op_diff"] == 1:
        return run
    return False

def all_fact_diff(run):
    if run["fact_diff"] == 1:
        return run
    return False

alg_pairs = [ ["V", "F"], ["F", "FC"], ["FC", "FCM"], ["FCM", "FCMR"], ["FCMR", "FCMRL"]]

for i, p in enumerate(alg_pairs):
    filters = OpsFilters(p[0], p[1])
    exp.add_report(
        ScatterPlotReport(
            attributes=["translator_operators"],
            filter_algorithm=p,
            filter=[rename_algorithms, filters.store_ops, filters.add_op_diff, all_op_diff],
            get_category=domain_as_category,
            format="png",
        ),
        name=f"scatterplot-ops_{i}",
    )

for i, p in enumerate(alg_pairs):
    filters = FactsFilters(p[0], p[1])
    exp.add_report(
        ScatterPlotReport(
            attributes=["translator_facts"],
            filter_algorithm=p,
            filter=[rename_algorithms, filters.store_facts, filters.add_fact_diff, all_fact_diff],
            get_category=domain_as_category,
            format="png",
        ),
        name=f"scatterplot-facts_{i}",
    )

exp.run_steps()