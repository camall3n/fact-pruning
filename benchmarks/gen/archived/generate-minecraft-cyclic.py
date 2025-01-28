# %%
#!%cd ~/dev/downward/src/translate
# %%
import os
import sys

from translate import main as translate
from translate import options


def tab(n=1, width=4):
    return " " * (width * n)


def generate_problem(n_ag, n_int):
    sections = [f"(define (problem minecraft-cyclic-{n_ag:02d}-{n_int:02d})"]
    sections += [tab() + "(:domain minecraft-cyclic)"]

    objects = [tab(1) + "(:objects"]
    objects += [
        tab(2) + " ".join([f"ag{i:02d}" for i in range(1, n_ag + 1)]) + " - agent"
    ]
    objects += [tab(2) + " ".join([f"n{i:02d}" for i in range(n_int + 1)]) + " - int"]
    objects += [tab(1) + ")"]
    sections += ["\n".join(objects)]

    state = [tab(1) + "(:init"]
    state += [tab(2) + "; ----- inventory -----"]
    state += ["\n".join([tab(2) + f"(hungry ag{i:02d})" for i in range(1, n_ag + 1)])]
    for resource in ["logs", "sticks", "iron", "wool", "food"]:
        state += [
            "\n".join(
                [tab(2) + f"(has-{resource} ag{i:02d} n00)" for i in range(1, n_ag + 1)]
            )
        ]
    state += [tab(2) + "; ----- misc -----"]
    state += [
        "\n".join([tab(2) + f"(are-seq n{i:02d} n{i+1:02d})" for i in range(n_int)])
    ]
    state += [tab(2) + "(= (total-cost) 0)"]
    state += [tab(1) + ")"]
    sections += ["\n".join(state)]

    sections += ["(:goal (and (tribe-has-food)))"]
    sections += ["(:metric minimize (total-cost))"]
    sections += [")\n"]
    return "\n\n".join(sections)


# %% generate pddl
pddl_dir = "../../benchmarks/pddl/minecraft-cyclic/"
os.makedirs(pddl_dir, exist_ok=True)
agent_counts = [1, 2, 4, 8, 16]
int_maxima = [3, 8, 16]
for n_ag in agent_counts:
    for n_int in int_maxima:
        prob_str = generate_problem(n_ag, n_int)
        prob_file = os.path.join(pddl_dir, f"prob-{n_ag:02d}-{n_int:02d}.pddl")
        with open(prob_file, "w") as f:
            f.write(prob_str)

# %% generate sas
sas_dir = "../../benchmarks/sas/basic/minecraft-cyclic/"
os.makedirs(sas_dir, exist_ok=True)

domain_file = os.path.join(pddl_dir, "domain.pddl")
for n_ag in agent_counts:
    for n_int in int_maxima:
        prob_file = os.path.join(pddl_dir, f"prob-{n_ag:02d}-{n_int:02d}.pddl")
        sas_file = os.path.join(sas_dir, f"minecraft-cyclic-{n_ag:02d}-{n_int:02d}.sas")
        sys.argv = [
            "translate.py",
            "--keep-unimportant-variables",
            "--keep-unreachable-facts",
            "--sas-file",
            sas_file,
        ]
        options.setup()
        translate(domain_file, prob_file)
