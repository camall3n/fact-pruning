# -*- coding: utf-8 -*-

import json
import sys

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        data = json.load(f)
    for _, e in data.items():
        if e["problem"].endswith(".pddl"):
            e["problem"] = e["problem"].replace(".pddl", ".sas")

    with open(sys.argv[1], "w") as f:
        json.dump(data, f, indent=4)
