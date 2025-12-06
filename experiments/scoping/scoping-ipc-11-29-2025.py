#! /usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
import itertools
import os

from lab.environments import LocalEnvironment
# from lab.reports import Attribute, geometric_mean
# from downward.reports.compare import ComparativeReport

from parser import SaSParser
import common_setup
from common_setup import IssueConfig, IssueExperiment


BENCHMARKS_DIR = "/mnt/nfs/home/ademello/research/downward-benchmarks"
BENCHMARKS_DIR = os.path.expanduser("~") +"/software/downward-benchmarks"


REVISIONS = ["scoping-experiments"]
BUILDS = ["release"]

CONFIG_NICKS = []

# basic
# V (vars)
# F (facts)
# CF (+causal links)
# MCF (+merge)
# RMCF (+reachability)
# LRMCF (+loop)

# CONFIG_NICKS.append(('basic', ["--translate-options", '--keep-unimportant-variables', "--search-options", "--search", "astar(lmcut())"]))
CONFIG_NICKS.append(('fd', ["--search", "astar(lmcut())"]))
CONFIG_NICKS.append(('basic', ["--translate-options", '--keep-unimportant-variables', "--search-options", "--search", "astar(lmcut())"]))
for x in ["V", "F", "FC", "FCM", "FCMR", "FCMRL"]:
    CONFIG_NICKS.append((x, ["--translate-options", '--keep-unimportant-variables', "--scoping", x, "--search-options", "--search", "astar(lmcut())"]))

CONFIGS = [
    IssueConfig(
        config_nick,
        config,
        build_options=[build],
        driver_options=["--build", build])
    for build in BUILDS
    for config_nick, config in CONFIG_NICKS
]

SUITE = common_setup.DEFAULT_OPTIMAL_SUITE
# SUITE = ["ged-opt14-strips", "pegsol-opt11-strips"]

time_limit = "30m"
memory_limit="3584M"

# SUITE = ["gripper"]
# time_limit = "1m"

ENVIRONMENT = LocalEnvironment(processes=min(64,os.cpu_count()))

PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['PYTHONPATH'] = f"{PLANNER_DIR}/src/"


exp = IssueExperiment(
    revisions=REVISIONS,
    configs=CONFIGS,
    environment=ENVIRONMENT,
    time_limit=time_limit,       # this soft-kills running executable
    memory_limit=memory_limit
)
exp.set_property("planner_time_limit", 1800)     # pass this to executable
exp.set_property("planner_memory_limit", "3.5g")

exp.add_suite(BENCHMARKS_DIR, SUITE)

exp.add_parser(exp.EXITCODE_PARSER)
exp.add_parser(exp.TRANSLATOR_PARSER)
exp.add_parser(exp.SINGLE_SEARCH_PARSER)
exp.add_parser(exp.PLANNER_PARSER)
exp.add_parser(SaSParser())

exp.add_step('build', exp.build)
exp.add_step('start', exp.start_runs)
exp.add_step("parse", exp.parse)

exp.add_fetcher(name='fetch')
# exp.add_fetcher("data/scoping-scoping-ipc-06-27-2025-base-eval")

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
  "translator_variables"
]

attributes += IssueExperiment.DEFAULT_TABLE_ATTRIBUTES + ["num_merge_attempts"]
# exp.add_comparison_table_step(attributes=attributes)

def rename_algorithms(run):
    name = run["algorithm"]
    paper_names = {f"{REVISIONS[0]}-basic": "No scoping", f"{REVISIONS[0]}-fd": "FD"}

    for a in ["V", "F", "FC", "FCM", "FCMR", "FCMRL"]:
        paper_names[f"{REVISIONS[0]}-{a}"] = a
    run["algorithm"] = paper_names[name]
    return run

algos = ["No scoping", "FD", "V", "F", "FC", "FCM", "FCMR", "FCMRL"]
exp.add_absolute_report_step(attributes=attributes, filter=rename_algorithms, filter_algorithm=algos)

from downward.reports.scatter import ScatterPlotReport


class OpsFilters:
    """Compute the IPC quality score.

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

def domain_as_category(run1, run2):
    # run2['domain'] has the same value, because we always
    # compare two runs of the same problem.
    return run1["domain"]

def all_diff(run):
    if run["op_diff"] == 1:
        return run
    return False

alg_pairs = [ ["V", "F"], ["F", "FC"], ["FC", "FCM"], ["FCM", "FCMR"], ["FCMR", "FCMRL"]]

for i, p in enumerate(alg_pairs):
    filters = OpsFilters(p[0], p[1])
    exp.add_report(
        ScatterPlotReport(
            attributes=["translator_operators"],
            filter_algorithm=p,
            filter=[rename_algorithms,filters.store_ops, filters.add_op_diff,all_diff],
            get_category=domain_as_category,
            format="png",  # Use "tex" for pgfplots output.
        ),
        name=f"scatterplot-ops_{i}",
    )

exp.run_steps()


