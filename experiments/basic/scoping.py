#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from lab.environments import LocalEnvironment
from lab.experiment import Experiment
from downward import suites

from parser import SaSParser
import common_setup
from common_setup import IssueConfig, IssueExperiment

BENCHMARKS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),"benchmarks", "basic")
# BENCHMARKS_DIR = os.environ["DOWNWARD_BENCHMARKS"]
REVISIONS = ["loop"]
BUILDS = ["release"]

CONFIG_NICKS = []


ALGS = {
    "vanilla" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--variables-only", "--disable-loop", "--disable-forward-pass", "--disable-merging", "--disable-causal-links"],
    "M" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--variables-only", "--disable-loop", "--disable-forward-pass", "--disable-causal-links"],
    "CL" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--variables-only", "--disable-loop", "--disable-forward-pass", "--disable-merging"],
    "MCL" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--variables-only", "--disable-loop", "--disable-forward-pass"],
    "FMCL" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--variables-only", "--disable-loop"],
    "FLMCL" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--variables-only"],
# 
    "val-vanilla" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--disable-loop", "--disable-forward-pass", "--disable-merging", "--disable-causal-links"],
    "val-M" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--disable-loop", "--disable-forward-pass", "--disable-causal-links"],
    "val-CL" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--disable-loop", "--disable-forward-pass", "--disable-merging"],
    "val-MCL" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--disable-loop", "--disable-forward-pass"],
    "val-FMCL" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py", "--disable-loop"],
    "val-FLMCL" : ["PYTHONPATH=src/translate/", "python", "src/translate/scoping/core.py"],
}


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

SUITE = ["gripper"]

ENVIRONMENT = LocalEnvironment(processes=48)
exp = Experiment(environment=ENVIRONMENT)

TIME_LIMIT=1800
MEMORY_LIMIT="3584M"

exp.set_property("planner_time_limit", 1800)     # pass this to executable
exp.set_property("planner_memory_limit", "3.5g")


# exp.add_parser(exp.EXITCODE_PARSER)
# exp.add_parser(exp.TRANSLATOR_PARSER)
# exp.add_parser(exp.SINGLE_SEARCH_PARSER)
# exp.add_parser(exp.PLANNER_PARSER)
exp.add_parser(SaSParser())


for alg, conf in ALGS.items():
    for task in suites.build_suite(BENCHMARKS_DIR, SUITE):
        run = exp.add_run()
        # Create symbolic links and aliases. This is optional. We
        # could also use absolute paths in add_command().
        #run.add_resource("domain", task.domain_file, symlink=True)
        run.add_resource("problem", task.problem_file, symlink=True)
        # We could also use exp.add_resource().
        command = conf + ["{problem}"]
        run.add_command(
            "run-planner",
            command,
            time_limit=TIME_LIMIT,
            memory_limit=MEMORY_LIMIT,
        )
        # AbsoluteReport needs the following properties:
        # 'domain', 'problem', 'algorithm', 'coverage'.
        #run.set_property("domain", task.domain)
        run.set_property("problem", task.problem)
        run.set_property("algorithm", alg)
        # BaseReport needs the following properties:
        # 'time_limit', 'memory_limit'.
        run.set_property("time_limit", TIME_LIMIT)
        run.set_property("memory_limit", MEMORY_LIMIT)
        # Every run has to have a unique id in the form of a list.
        # The algorithm name is only really needed when there are
        # multiple algorithms.
        run.set_property("id", [alg, task.domain, task.problem])



exp.add_step('build', exp.build)
exp.add_step('start', exp.start_runs)
exp.add_step("parse", exp.parse)

exp.add_fetcher(name='fetch')

#attributes = IssueExperiment.DEFAULT_TABLE_ATTRIBUTES
# exp.add_comparison_table_step(attributes=attributes)
#exp.add_absolute_report_step(attributes=attributes)

exp.run_steps()


