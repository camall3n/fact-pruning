#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os
import json
import re
import shutil
import ast

from lab.parser import Parser


def sas_name(content, props):
    # the entire json is in content, adding only run_dir to props
    data = json.loads(content)
    domain = data.get("domain", None)
    if domain is None:
        domain = data["id"][1]
    problem = data["problem"].replace(".pddl", ".sas")
    repo = data.get("repo", "/data/software/fd-scoping")
    benchmarks = "benchmarks"
    alg = data["algorithm"]
    path = os.path.join(repo, benchmarks, alg, domain)
    os.makedirs(path, exist_ok=True)
    props["sas_name"] = os.path.join(path, problem)
    exp_name = data.get("experiment_name", "scoping")
    target_sas_file = data["problem"].replace(".sas", "_scoped.sas")
    target_sas_path = os.path.join("data", exp_name, data["run_dir"], target_sas_file)
    fname = os.path.join("data", exp_name, data["run_dir"], "output.sas")
    if os.path.exists(fname):
        shutil.copyfile(fname, props["sas_name"])
    if os.path.exists(target_sas_path):
        # props["sas_name"] = os.path.join(path, target_sas_file)
        shutil.copyfile(target_sas_path, props["sas_name"])


def parse_statistics(content, props):
    """Parse all translator output of the following form:

    Translator xxx: yyy

    """
    pattern = re.compile(r"^Translator (.+): (\d+)(?: KB|)$", flags=re.M)
    for name, count in pattern.findall(content):
        attr = name.lower().replace(" ", "_")
        # Support strings, numbers, tuples, lists, dicts, Booleans, and None.
        props[f"translator_{attr}"] = ast.literal_eval(count)

def parse_translator_timestamps(content, props):
    """Parse all translator output of the following forms:

        Computing fact groups: [0.000s CPU, 0.004s wall-clock]
        Writing output... [0.000s CPU, 0.001s wall-clock]

    The last line reads:

        Done! [6.860s CPU, 6.923s wall-clock]

    """
    pattern = re.compile(
        r"^(.+)(?:\.\.\.|:|!) \[(.+)s CPU, .+s wall-clock\]$", flags=re.M
    )
    for section, time in pattern.findall(content):
        section = section.lower().replace(" ", "_")
        props[f"translator_time_{section}"] = float(time)


class SaSParser(Parser):
    def __init__(self):
        Parser.__init__(self)

        self.add_function(sas_name, file="static-properties")
        self.add_function(parse_translator_timestamps)
        self.add_function(parse_statistics)