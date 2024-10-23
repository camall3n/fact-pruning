#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os
import json
import shutil

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

class SaSParser(Parser):
    def __init__(self):
        Parser.__init__(self)

        self.add_function(sas_name, file="static-properties")
