#! /usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import os

from lab.environments import LocalEnvironment
# from lab.reports import Attribute, geometric_mean
# from downward.reports.compare import ComparativeReport

from parser import SaSParser
import common_setup
from common_setup import IssueConfig, IssueExperiment


BENCHMARKS_DIR = "/data/software/fdr-generator/benchmarks/structural"

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

CONFIG_NICKS.append(('fd', ["--search", "astar(lmcut())"]))


CONFIGS = [
    IssueConfig(
        config_nick,
        config,
        build_options=[build],
        driver_options=["--build", build])
    for build in BUILDS
    for config_nick, config in CONFIG_NICKS
]

SUITE = [ "bi-partite-sas", "chain-0.1-sas", "chain-0.5-sas", "dag-0.1-sas", "dag-0.5-sas", "directed-chain-sas", "inverted-fork-sas", "polytree-0.25-sas", "polytree-0.75-sas", "random-0.25-sas", "random-0.75-sas", "star-0.25-sas", "star-0.75-sas", "bidirectional-bi-partite-sas", "chain-0.25-sas", "chain-0.75-sas", "dag-0.25-sas", "dag-0.75-sas", "fork-sas", "polytree-0.1-sas", "polytree-0.5-sas", "random-0.1-sas", "random-0.5-sas", "star-0.1-sas", "star-0.5-sas", "tree-sas"]

time_limit = "30m"
memory_limit="3584M"

# SUITE = ["gripper"]
# time_limit = "1m"

ENVIRONMENT = LocalEnvironment(processes=48)

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
exp.add_absolute_report_step(attributes=attributes)

exp.run_steps()


