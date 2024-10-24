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

DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
BENCHMARKS_DIR = os.environ["DOWNWARD_BENCHMARKS"]
REVISIONS = ["loop-sorted"]
BUILDS = ["release"]

CONFIG_NICKS = []

CONFIG_NICKS.append(('basic', ["--translate"]))

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

# SUITE = ["gripper"]

ENVIRONMENT = LocalEnvironment(processes=48)

exp = IssueExperiment(
    revisions=REVISIONS,
    configs=CONFIGS,
    environment=ENVIRONMENT,
    time_limit="30m",       # this soft-kills running executable
    memory_limit="3584M"
)
exp.set_property("planner_time_limit", 1800)     # pass this to executable
exp.set_property("planner_memory_limit", "3.5g")

exp.add_suite(BENCHMARKS_DIR, SUITE)

exp.add_parser(exp.EXITCODE_PARSER)
exp.add_parser(exp.TRANSLATOR_PARSER)
exp.add_parser(exp.SINGLE_SEARCH_PARSER)
exp.add_parser(exp.PLANNER_PARSER)
exp.add_parser(SaSParser())

exp.add_fetcher("data/sorted-basic-eval")
exp.add_fetcher("data/scoping-eval")
# exp.add_fetcher("data/sorted-basic_cg-eval")

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

# exp.add_comparison_table_step(attributes=attributes)
exp.add_absolute_report_step(attributes=attributes)

exp.run_steps()


