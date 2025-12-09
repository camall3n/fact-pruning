import pathlib
import random
import tarski as tsk
from tarski import fstrips as fs
from tarski.fstrips import create_fstrips_problem, OptimizationType
from tarski.io import FstripsWriter
from tarski.syntax import land, neg
import os
import shutil


AGENT_RESOURCES = [
    "hungry",
    "has-logs", "has-planks", "has-sticks", "has-stone",
    "has-iron", "has-wool", "has-wood-pickaxe", "has-stone-pickaxe",
    "has-stone-axe", "has-shears", "has-string", "has-honeycomb",
    "has-candle", "has-bed",
]

GLOBAL_PREDICATES = ["tribe-has-food", "cake-ready", "candle-lit"]

# Non-food items for crafting problems
CRAFTING_RESOURCES = [
    "has-logs", "has-planks", "has-sticks", "has-stone",
    "has-iron", "has-wool", "has-wood-pickaxe", "has-stone-pickaxe",
    "has-stone-axe", "has-shears", "has-string", "has-honeycomb",
    "has-candle", "has-bed",
]

def make_language():
    """Define a language that mirrors your STRIPS domain predicates."""
    from tarski.theories import Theory
    lang = tsk.fstrips.language("minecraft", theories=[Theory.ARITHMETIC])
    agent = lang.sort("agent")

    preds = {}
    for p in AGENT_RESOURCES:
        preds[p] = lang.predicate(p, agent)
    for p in GLOBAL_PREDICATES:
        preds[p] = lang.predicate(p)

    # Define total-cost as a function (Integer is available with ARITHMETIC theory)
    preds["total-cost"] = lang.function("total-cost", lang.Integer)

    return lang, preds

def make_agents(lang, n_agents):
    """Create n agent constants with alternating names for readability."""
    A = lang.get_sort("agent")
    names = []
    for i in range(1, n_agents + 1):
        prefix = "steve"
        names.append(f"{prefix}{i:02d}")
    consts = [lang.constant(name, A) for name in names]
    return names, consts

def random_init(problem, lang, preds, agent_consts, init_cfg, rng):
    """Populate :init with randomized per-agent resources and optional global facts."""
    # Initialize total-cost to 0
    problem.init.set(preds["total-cost"](), 0)
    
    # Agent-level resources (including hunger state and items)
    for agc in agent_consts:
        # Add hunger state
        if rng.random() < init_cfg.get("hungry_prob", 0.5):
            problem.init.add(preds["hungry"], agc)

        # Add random resources/items
        k = rng.randint(*init_cfg.get("init_resource_range", (1, 3)))
        candidates = [p for p in AGENT_RESOURCES if p != "hungry"]
        for res in rng.sample(candidates, k=k):
            problem.init.add(preds[res], agc)

    # Global predicates
    for gp in init_cfg.get("global_inits", []):
        problem.init.add(preds[gp]())

def random_hunger_goal(preds, agent_consts, goal_cfg, rng):
    """Create hunger-focused goals where agents must not be hungry."""
    conjuncts = []
    
    include_prob = goal_cfg.get("agent_goal_prob", 0.7)
    
    for agc in agent_consts:
        if rng.random() < include_prob:
            # Goal: agent should NOT be hungry
            conjuncts.append(neg(preds["hungry"](agc)))
    
    # Optionally include global goals
    for gp in goal_cfg.get("global_goals", []):
        conjuncts.append(preds[gp]())
    
    # Ensure there is at least one conjunct
    if not conjuncts:
        conjuncts.append(neg(preds["hungry"](agent_consts[0])))
    
    return land(*conjuncts, flat=True)

def random_crafting_goal(preds, agent_consts, goal_cfg, rng):
    """Create crafting-focused goals where agents must have items (hunger doesn't matter)."""
    conjuncts = []

    requirements_range = goal_cfg.get("requirements_per_agent_range", (1, 1))
    include_prob = goal_cfg.get("agent_goal_prob", 0.7)

    for agc in agent_consts:
        if rng.random() < include_prob:
            k_per_agent = rng.randint(*requirements_range)
            chosen = rng.sample(CRAFTING_RESOURCES, k=k_per_agent)
            for res in chosen:
                conjuncts.append(preds[res](agc))

    # Optionally include global goals (empty for pure crafting problems)
    for gp in goal_cfg.get("global_goals", []):
        conjuncts.append(preds[gp]())

    # Ensure there is at least one conjunct
    if not conjuncts:
        # Fallback: give a random agent a random number of random items
        fallback_agent = rng.choice(agent_consts)
        k_fallback = rng.randint(*requirements_range)
        chosen = rng.sample(CRAFTING_RESOURCES, k=k_fallback)
        for res in chosen:
            conjuncts.append(preds[res](fallback_agent))

    return land(*conjuncts, flat=True)

def generate_problem(n_agents, seed, init_cfg, goal_cfg, problem_type):
    """Build a single problem with randomized init and goal."""
    rng = random.Random(seed)
    lang, preds = make_language()
    
    problem_name = f"minecraft-{problem_type}-a{n_agents}-s{seed}"
    problem = create_fstrips_problem(
        lang, domain_name="minecraft", problem_name=problem_name
    )

    # Create agents
    agent_names, agent_consts = make_agents(lang, n_agents)

    # Init (same for both problem types)
    random_init(problem, lang, preds, agent_consts, init_cfg, rng)

    # Goal - based on problem type
    if problem_type == "hunger":
        problem.goal = random_hunger_goal(preds, agent_consts, goal_cfg, rng)
    else:  # crafting
        problem.goal = random_crafting_goal(preds, agent_consts, goal_cfg, rng)

    # Set the optimization metric
    from collections import namedtuple
    Metric = namedtuple('Metric', ['opt_type', 'opt_expression'])
    problem.plan_metric = Metric(OptimizationType.MINIMIZE, preds["total-cost"]())

    return problem

def main():
    agent_counts_hunger = [1, 2, 5, 10, 12, 15, 20, 25]
    agent_counts_crafting = []#[1, 2, 5, 10, 15, 20]

    init_cfg = {
        "hungry_prob": 1.0,  # 100% chance each agent starts hungry
        "init_resource_range": (1, 5),  # Each agent has 1-5 random items
        "global_inits": []
    }

    # Goal configuration for hunger problems
    hunger_goal_cfg = {
        "agent_goal_prob": 1.0,  # 100% of agents must not be hungry
        "global_goals": []
    }

    # Goal configuration for crafting problems
    crafting_goal_cfg = {
        "requirements_per_agent_range": (1, 5),  # 1-5 items per agent in goal
        "agent_goal_prob": 0.3,  # Fewer agents in goal for more variety
        "global_goals": []
    }
    
    os.makedirs("problems/hunger")
    shutil.copy("domain.pddl", "problems/hunger")

    for n_agents in agent_counts_hunger:
        for i in range(2):
            seed = n_agents * 1000 + i  # Unique seed for each problem
            problem = generate_problem(n_agents, seed, init_cfg, hunger_goal_cfg, "hunger")
            writer = FstripsWriter(problem)
            fname = f"./problems/hunger/minecraft_hunger_agents-{n_agents}_seed-{seed}.pddl"
            writer.write_instance(fname, constant_objects=[])

    os.makedirs("problems/craft")
    shutil.copy("domain.pddl", "problems/craft")
    

    for n_agents in agent_counts_crafting:
        for i in range(1):
            seed = n_agents * 1000 + i + 100000  # Offset to avoid collision with hunger seeds
            problem = generate_problem(n_agents, seed, init_cfg, crafting_goal_cfg, "crafting")
            writer = FstripsWriter(problem)
            fname = f"./problems/craft/minecraft_crafting_agents-{n_agents}_seed-{seed}.pddl"
            writer.write_instance(fname, constant_objects=[])


if __name__ == "__main__":
    main()