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


BENCHMARKS_DIR = os.environ["DOWNWARD_BENCHMARKS"]


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

CONFIG_NICKS.append(('basic', ["--translate-options", '--keep-unimportant-variables', "--search-options", "--search", "astar(lmcut())"]))
for x in ["V", "F", "CF", "MCF", "RMCF", "LRMCF"]:
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

time_limit = "30m"
memory_limit="3584M"

SUITE = ["gripper"]
time_limit = "1m"

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

attributes = IssueExperiment.DEFAULT_TABLE_ATTRIBUTES + ["num_merge_attempts"]
# exp.add_comparison_table_step(attributes=attributes)
exp.add_absolute_report_step(attributes=attributes)

exp.run_steps()


