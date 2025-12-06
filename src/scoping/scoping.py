#!%cd ~/dev/downward/src/translate
#
from collections import defaultdict
from typing import Any

from scoping.actions import VarValAction
from scoping.factset import FactSet, VarValPair
from scoping.merging import merge
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
import sas_tasks as fd
from translate import simplify


def compute_sas_reachability(scoped_sas: fd.SASTask):
    try:
        simplify.filter_unreachable_propositions(scoped_sas, quiet=True)
    except simplify.Impossible:
        scoped_sas = ScopingTask.trivial(solvable=False).to_sas()
    except simplify.TriviallySolvable:
        scoped_sas = ScopingTask.trivial(solvable=True).to_sas()
    return scoped_sas


def coarsen_facts_to_variables(facts: FactSet, domains: FactSet) -> None:
    for var, _ in facts:
        facts.union(var, domains[var])


def prune_facts(fact_list: list[VarValPair], relevant_facts: FactSet):
    return [fact for fact in fact_list if fact in relevant_facts]


def prune_mutexes(
    mutex_list: list[list[VarValPair]], relevant_facts: FactSet
) -> list[list[VarValPair]]:
    # Prune irrelevant facts
    mutexes = [prune_facts(mutex, relevant_facts) for mutex in mutex_list]
    # Prune mutexes with < 2 facts
    mutexes = [mutex for mutex in mutexes if mutex and len(mutex) > 1]
    # Prune mutexes with < 2 variables
    mutex_facts = [FactSet(mutex) for mutex in mutexes]
    mutexes = [
        mutex for mutex, facts in zip(mutexes, mutex_facts) if len(facts.variables) > 1
    ]
    # Prune duplicate mutexes, then convert back to list of lists
    mutexes = list(
        map(
            list,
            dict.fromkeys(tuple(dict.fromkeys(mutex)) for mutex in mutexes),
        )
    )
    return mutexes


def prune(scoping_task: ScopingTask, actions: list[VarValAction]) -> ScopingTask:
    # Precondition and goal facts
    facts = FactSet(scoping_task.goal)
    for a in actions:
        facts.add(a.precondition)

    rel_vars = facts.variables

    # Add relevant effect facts
    for a in actions:
        for var, val in a.effect:
            if var in rel_vars:
                facts.add(var, val)

    # Add initial state facts
    facts.add(scoping_task.init)

    # Remove variables with only 1 value
    facts = FactSet({var: values for var, values in facts if len(values) > 1})

    init = prune_facts(scoping_task.init, facts)
    goal = prune_facts(scoping_task.goal, facts)

    # Prune actions and remove any with empty effects
    new_actions = []
    for a in actions:
        new_effect = prune_facts(a.effect, facts)
        if new_effect:
            new_actions.append(
                VarValAction(
                    a.name,
                    prune_facts(a.precondition, facts),
                    new_effect,
                    a.cost,
                )
            )

    mutexes = prune_mutexes(scoping_task.mutexes, facts)

    if scoping_task.axioms:
        raise NotImplementedError(
            "Task contains axioms, but axiom pruning is not yet implemented."
        )
    # If axiom pruning *were* implemented, here's a sketch of what we might do...
    axioms = [
        VarValAction(
            name="",
            precondition=prune_facts(ax.precondition, facts),
            effect=prune_facts(ax.effect, facts),
            cost=0,
        )
        for ax in scoping_task.axioms
    ]
    return ScopingTask(
        domains=facts,
        init=init,
        goal=goal,
        actions=new_actions,
        mutexes=mutexes,
        axioms=axioms,
        metric=scoping_task.metric,
        value_names=scoping_task.value_names,
    )


def relevance(scoping_task: ScopingTask, options: ScopingOptions) -> list[VarValAction]:
    s0 = FactSet(scoping_task.init)
    prev_facts = FactSet(scoping_task.goal)
    prev_actions = []
    while True:
        if options.enable_causal_links:
            threatening_facts = FactSet()
            for a in prev_actions:
                for f in a.effect:
                    if f not in s0:
                        threatening_facts.add(*f)
            threatened_vars = threatening_facts.variables

            causally_linked_facts = FactSet()
            for var, values in s0:
                if var not in threatened_vars:
                    for val in values:
                        causally_linked_facts.add(var, val)

            filtered_facts = FactSet()
            for var, values in prev_facts:
                for val in values:
                    if (var, val) not in causally_linked_facts:
                        filtered_facts.add(var, val)
        else:
            filtered_facts = prev_facts

        if not options.enable_fact_based:
            coarsen_facts_to_variables(filtered_facts, scoping_task.domains)

        actions = []
        for a in scoping_task.actions:
            for f in a.effect:
                if f in filtered_facts:
                    actions.append(a)
                    break

        facts, info = reduce_and_get_facts(
            scoping_task, actions, prev_facts, options.enable_merging
        )
        if not options.enable_fact_based:
            coarsen_facts_to_variables(filtered_facts, scoping_task.domains)

        if facts == prev_facts and len(actions) == len(prev_actions):
            break
        prev_facts = facts
        prev_actions = actions
    return actions


def prune_non_reachable(scoping_task: ScopingTask) -> ScopingTask:
    prev_facts = FactSet(scoping_task.init)
    prev_actions = []
    while True:
        facts = FactSet(prev_facts)
        actions = []
        for a in scoping_task.actions:
            if FactSet(a.precondition) in prev_facts:
                actions.append(a)
                facts.add(a.effect)

        if facts == prev_facts and len(actions) == len(prev_actions):
            break
        prev_facts = facts
        prev_actions = actions

    if FactSet(scoping_task.goal) not in facts:
        scoped_task = ScopingTask.trivial(solvable=False)
    else:
        scoped_task = prune(scoping_task, actions)
        if FactSet(scoped_task.goal) in FactSet(scoped_task.init):
            scoped_task = ScopingTask.trivial(solvable=True)
    return scoped_task


def prune_non_reachable_via_sas(scoping_task: ScopingTask) -> ScopingTask:
    sas_task = scoping_task.to_sas()
    scoped_sas = compute_sas_reachability(sas_task)
    scoped_task = ScopingTask.from_sas(scoped_sas)
    return scoped_task


def reduce_and_get_facts(
    scoping_task: ScopingTask,
    actions: list[VarValAction],
    facts: FactSet,
    enable_merging: bool,
) -> tuple[FactSet, dict]:
    relevant_vars = facts.variables
    if enable_merging:
        action_partitions = partition_actions(relevant_vars, actions)
    else:
        # make a separate partition for each action
        action_partitions = list(map(lambda x: [x], actions))

    relevant_facts = FactSet(facts)
    aggregated_info = defaultdict(int)
    for actions in action_partitions:
        relevant_precond_facts, info = merge(
            actions, relevant_vars, scoping_task.domains
        )
        for key, val in info.items():
            aggregated_info[key] += val
        relevant_facts.union(relevant_precond_facts)

    return relevant_facts, aggregated_info


def partition_actions(
    relevant_variables: list[Any], actions: list[VarValAction]
) -> list[list[VarValAction]]:
    """Partition actions by (effect, cost), ignoring irrelevant variables"""
    # TODO: replace with hash map
    unique_effects_and_costs = defaultdict(list)
    for a in actions:
        unique_effects_and_costs[a.effect_hash(relevant_variables)].append(a)
    effect_cost_partitions = list(unique_effects_and_costs.values())
    return effect_cost_partitions


def update_stats(stats: dict[str, list], scoping_task: ScopingTask):
    stats["n_vars"].append(len(scoping_task.domains.variables))
    stats["n_facts"].append(scoping_task.domains.n_facts)
    stats["n_actions"].append(len(scoping_task.actions))


def scope(scoping_task: ScopingTask, options: ScopingOptions) -> ScopingTask:
    stats = defaultdict(list)
    update_stats(stats, scoping_task)
    while True:
        relevant_actions = relevance(scoping_task, options)
        scoped_task = prune(scoping_task, relevant_actions)
        update_stats(stats, scoped_task)
        if not options.enable_forward_pass or scoped_task == scoping_task:
            break
        scoped_task = prune_non_reachable_via_sas(scoped_task)
        update_stats(stats, scoped_task)
        if (
            not options.enable_loop
            or scoped_task == scoping_task
            or scoped_task.is_trivial()
        ):
            break
        scoping_task = scoped_task
    for key, val in sorted(stats.items()):
        print(f"{key}: {val}")
    return scoped_task
