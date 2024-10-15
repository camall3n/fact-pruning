#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os
import json
import shutil

from lab.parser import Parser


def sas_name(content, props):
    # the entire json is in content, adding only run_dir to props
    data = json.loads(content)
    domain = data["domain"]
    problem = data["problem"].replace(".pddl", ".sas")
    repo = data["repo"]
    benchmarks = "benchmarks"
    alg = data["algorithm"]
    path = os.path.join(repo, benchmarks, alg, domain)
    os.makedirs(path, exist_ok=True)
    props["sas_name"] = os.path.join(path, problem)
    fname = os.path.join("data", data["experiment_name"], data["run_dir"], "output.sas")
    if os.path.exists(fname):
        shutil.copyfile(fname, props["sas_name"])

class SaSParser(Parser):
    def __init__(self):
        Parser.__init__(self)

        self.add_function(sas_name, file="static-properties")
