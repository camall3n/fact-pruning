# %%
#!%cd ~/dev/downward/src/translate

# %%
from collections import defaultdict
from typing import Any, Tuple

from sas_tasks import SASTask, VarValPair
from scoping.actions import VarValAction
from scoping.factset import FactSet
from scoping.merging import merge
from scoping.task import ScopingTask


def filter_causal_links(
    facts: FactSet,
    init: list[VarValPair],
    effect_facts: FactSet,
    enable_fact_based: bool = False,
    enable_causal_links: bool = False,
) -> FactSet:
    """Remove any facts from `facts` that are present in the initial state `init` and
    unthreatened by any of the `effect_facts`."""
    if not enable_causal_links:
        return facts

    def benign_sets(val):
        return [set(), set([val])] if enable_fact_based else [set()]

    # [(var, val) in s0 s.t. dne action `a` where eff(a)[var] ≠ val]
    unthreatened_init_facts = [
        (var, val) for (var, val) in init if effect_facts[var] in benign_sets(val)
    ]
    unthreatened_init_facts = FactSet(unthreatened_init_facts)
    relevant_facts = FactSet()
    for var, values in facts:
        for val in values:
            if (var, val) not in unthreatened_init_facts:
                relevant_facts.add(var, val)
    return relevant_facts


def get_goal_relevant_actions(
    facts: FactSet, actions: list[VarValAction]
) -> list[VarValAction]:
    """Find all actions that achieve at least one fact in `facts`."""
    # The same action may achieve multiple facts, so we de-duplicate with a set
    return list(set([a for a in actions for fact in a.effect if fact in facts]))


def partition_actions(
    relevant_variables: list[Any], actions: list[VarValAction]
) -> list[list[VarValAction]]:
    """Partition actions by (effect, cost), ignoring irrelevant variables"""
    # TODO: replace with hash map
    unique_effects_and_costs = defaultdict(list)
    for a in actions:
        unique_effects_and_costs[a.effect_hash(relevant_variables)].append(a)
    # unique_effects_and_costs = set([a.effect_hash(relevant_variables) for a in actions])
    effect_cost_partitions = list(unique_effects_and_costs.values())
    # for effect_cost in unique_effects_and_costs:
    #     matching_actions = [
    #         a for a in actions if a.effect_hash(relevant_variables) == effect_cost
    #     ]
    #     effect_cost_partitions.append(matching_actions)
    return effect_cost_partitions


def coarsen_facts_to_variables(facts: FactSet, domains: FactSet) -> None:
    for var, _ in facts:
        facts.union(var, domains[var])


def get_goal_relevant_facts(
    domains: FactSet,
    relevant_facts: FactSet,
    relevant_actions: list[VarValAction],
    enable_merging: bool = False,
) -> tuple[FactSet, dict]:
    """Find all facts that appear in the (simplified) preconditions
    of the (possibly merged) relevant actions."""
    relevant_vars = relevant_facts.variables
    if enable_merging:
        action_partitions = partition_actions(relevant_vars, relevant_actions)
    else:
        # make an separate partition for each action
        action_partitions = list(map(lambda x: [x], relevant_actions))

    newly_relevant_facts = FactSet()
    aggregated_info = defaultdict(int)
    for actions in action_partitions:
        relevant_precond_facts, info = merge(actions, relevant_vars, domains)
        for key, val in info.items():
            aggregated_info[key] += val
        newly_relevant_facts.union(relevant_precond_facts)
    newly_relevant_facts.difference(relevant_facts)

    return newly_relevant_facts, aggregated_info
