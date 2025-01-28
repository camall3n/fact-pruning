#!%cd ~/dev/downward/src/translate
# %%
import os
import sys

from translate import main as translate
from translate import options


def generate_problem(n_agents):
    header = f"""(define (problem minecraft-multi-{n_agents:02d})

    (:domain minecraft-multi)

    (:objects"""
    objects = "\n".join([f"        steve{i:02d}" for i in range(1, n_agents + 1)])
    midder = """    )

    (:init"""
    state = "\n".join(
        [f"        (hungry steve{i:02d})" for i in range(1, n_agents + 1)]
    )
    footer = """        (= (total-cost) 0)
    )

    (:goal (and (tribe-has-food)))

    (:metric minimize
        (total-cost)
    )
)
"""
    return "\n".join([header, objects, midder, state, footer])


# %% generate pddl
pddl_dir = "../../benchmarks/pddl/minecraft-multi/"
os.makedirs(pddl_dir, exist_ok=True)
for i in range(20, 21):
    prob_str = generate_problem(i)
    prob_file = os.path.join(pddl_dir, f"prob-{i:02d}.pddl")
    with open(prob_file, "w") as f:
        f.write(prob_str)

# %% generate sas
sas_dir = "../../benchmarks/sas/basic/minecraft-multi/"
os.makedirs(sas_dir, exist_ok=True)

domain_file = os.path.join(pddl_dir, "domain.pddl")
for i in range(20, 21):
    prob_file = os.path.join(pddl_dir, f"prob-food-{i:02d}.pddl")
    sas_file = os.path.join(sas_dir, f"minecraft-multi-food-{i:02d}.sas")
    sys.argv = [
        "translate.py",
        "--keep-unimportant-variables",
        "--keep-unreachable-facts",
        "--sas-file",
        sas_file,
    ]
    options.setup()
    translate(domain_file, prob_file)
