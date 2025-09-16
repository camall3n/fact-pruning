#!%cd ~/dev/downward/src/translate
#
import argparse
from collections import defaultdict
import os

import sas_tasks as fd
from scoping.actions import VarValAction
from scoping.backward import (
    compute_goal_relevance,
    get_goal_relevant_facts,
    coarsen_facts_to_variables,
    filter_causal_links,
)
from scoping.forward import compute_reachability
from scoping.factset import FactSet, VarValPair
from scoping.options import ScopingOptions
from scoping.sas_parser import SasParser
from scoping.task import ScopingTask
from translate import timers
from translate import simplify
from translate import unsolvable_sas_task, solvable_sas_task, trivial_task


def scope_backward(
    scoping_task: ScopingTask,
    enable_merging: bool = True,
    enable_causal_links: bool = True,
    enable_fact_based: bool = True,
) -> tuple[ScopingTask, dict]:
    relevant_facts = FactSet(scoping_task.goal)
    relevant_actions: list[VarValAction] = []
    remaining_actions = scoping_task.actions

    while remaining_actions or (relevant_facts != scoping_task.domains):
        # Find new actions that cause the relevant facts
        filtered_facts = filter_causal_links(
            relevant_facts,
            scoping_task.init,
            relevant_actions,
            enable_fact_based=enable_fact_based,
            enable_causal_links=enable_causal_links,
        )

        if not enable_fact_based:
            coarsen_facts_to_variables(filtered_facts, scoping_task.domains)

        newly_relevant_actions, remaining_actions = get_goal_relevant_actions(
            filtered_facts, remaining_actions
        )

        if not newly_relevant_actions:
            break
        relevant_actions += newly_relevant_actions

        # Find new precondition facts of the relevant actions
        newly_relevant_facts, info = get_goal_relevant_facts(
            scoping_task.domains,
            relevant_facts,
            relevant_actions,
            enable_merging=enable_merging,
        )

        if newly_relevant_facts in relevant_facts:
            break
        relevant_facts.union(newly_relevant_facts)

    # If an init fact contradicts all relevant_facts, or if it contradicts a
    # precondition, ensure that we can detect it.
    for var, val in scoping_task.init:
        if var in relevant_facts.variables:
            relevant_facts.add(var, val)
        for action in relevant_actions:
            for a_var, a_val in action.precondition:
                if var == a_var and val != a_val:
                    relevant_facts.add(var, val)
                    relevant_facts.add(a_var, a_val)

    if not enable_fact_based:
        relevant_facts = filter_causal_links(
            relevant_facts,
            scoping_task.init,
            relevant_actions,
            enable_fact_based=enable_fact_based,
            enable_causal_links=enable_causal_links,
        )
        coarsen_facts_to_variables(relevant_facts, scoping_task.domains)

    return prune_task(scoping_task, relevant_facts, relevant_actions), info


def get_goal_relevant_actions(
    facts: FactSet, actions: list[VarValAction]
) -> tuple[list[VarValAction], list[VarValAction]]:
    relevant_actions = []
    remaining_actions = []
    for action in actions:
        for fact in action.effect:
            if fact in facts:
                relevant_actions.append(action)
                break
        else:
            remaining_actions.append(action)
    return relevant_actions, remaining_actions


def old_scope_backward(
    scoping_task: ScopingTask,
    enable_merging: bool = True,
    enable_causal_links: bool = True,
    enable_fact_based: bool = True,
) -> tuple[ScopingTask, dict]:
    relevant_facts, relevant_actions, info = compute_goal_relevance(
        scoping_task=scoping_task,
        enable_merging=enable_merging,
        enable_causal_links=enable_causal_links,
        enable_fact_based=enable_fact_based,
    )
    # Explicitly add precond facts in case preconds were dropped in a merge
    precond_facts = FactSet()
    for a in relevant_actions:
        precond_facts.add(a.precondition)
    relevant_facts.union(precond_facts)

    # Also add side-effect facts on relevant vars
    for a in relevant_actions:
        for var, val in a.effect:
            if var in relevant_facts.variables:
                relevant_facts.add(var, val)
    return prune_task(scoping_task, relevant_facts, relevant_actions), info


def scope_forward(scoping_task: ScopingTask) -> tuple[ScopingTask, bool]:
    facts, actions, goal_reachable = compute_reachability(scoping_task=scoping_task)
    return prune_task(scoping_task, facts, actions), goal_reachable


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


def prune_task(
    scoping_task: ScopingTask, facts: FactSet, actions: list[VarValAction]
) -> ScopingTask:
    facts = FactSet({var: values for var, values in facts if len(values) > 1})

    init = prune_facts(scoping_task.init, facts)
    goal = prune_facts(scoping_task.goal, facts)

    # Prune precondition/effect facts from actions
    actions = [
        VarValAction(
            name=a.name,
            precondition=prune_facts(a.precondition, facts),
            effect=prune_facts(a.effect, facts),
            cost=a.cost,
        )
        for a in actions
    ]
    actions = [a for a in actions if a.effect]  # then prune empty actions

    mutexes = prune_mutexes(scoping_task.mutexes, facts)
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
        actions=actions,
        mutexes=mutexes,
        axioms=axioms,
        metric=scoping_task.metric,
        value_names=scoping_task.value_names,
    )


def scope(
    scoping_task: ScopingTask,
    options: ScopingOptions,
):
    aggregated_info = defaultdict(int)
    while True:
        scoped_task, info = scope_backward(
            scoping_task,
            enable_merging=options.enable_merging,
            enable_causal_links=options.enable_causal_links,
            enable_fact_based=options.enable_fact_based,
        )
        for key, val in info.items():
            aggregated_info[key] += val
        if options.enable_forward_pass:
            scoped_task, goal_reachable = scope_forward(scoped_task)
            if not goal_reachable:
                # TODO: do something smart
                pass
        if (
            options.enable_loop
            and options.enable_forward_pass
            and (scoped_task != scoping_task)
        ):
            scoping_task = scoped_task
        else:
            break
    return scoped_task


def track_scoping_progress(info: dict, sas_task: fd.SASTask, first=False) -> None:
    if first:
        info["Scoping vars"] = ""
        info["Scoping facts"] = ""
        info["Scoping operators"] = ""
        sep = ""
    else:
        sep = " -> "
    info["Scoping vars"] += sep + f"{len(sas_task.variables.ranges)}"
    info["Scoping facts"] += sep + f"{sum(sas_task.variables.ranges)}"
    info["Scoping operators"] += sep + f"{len(sas_task.operators)}"


def pruning_did_occur(sas_task: fd.SASTask, scoped_sas: fd.SASTask) -> bool:
    n_vars_removed = len(sas_task.variables.ranges) - len(scoped_sas.variables.ranges)
    n_facts_removed = sum(sas_task.variables.ranges) - sum(scoped_sas.variables.ranges)
    n_actions_removed = len(sas_task.operators) - len(scoped_sas.operators)
    something_was_removed = (n_vars_removed + n_facts_removed + n_actions_removed) > 0
    return something_was_removed


def is_trivial(scoped_sas: fd.SASTask) -> bool:
    return scoped_sas in [
        trivial_task(solvable=True),
        trivial_task(solvable=False),
    ]


def scope_sas_task(
    sas_task: fd.SASTask,
    scoping_options: ScopingOptions,
) -> tuple[fd.SASTask, dict]:
    aggregated_info = {
        "Scoping merge attempts": 0,
        "Scoping merge successes": 0,
    }
    track_scoping_progress(aggregated_info, sas_task, first=True)
    info = {}
    should_continue = True
    while should_continue:
        should_continue = False
        scoping_task = ScopingTask.from_sas(sas_task)
        scoped_task, info = scope_backward(
            scoping_task,
            enable_merging=scoping_options.enable_merging,
            enable_causal_links=scoping_options.enable_causal_links,
            enable_fact_based=scoping_options.enable_fact_based,
        )
        for key, val in info.items():
            aggregated_info[key] += val
        scoped_sas = scoped_task.to_sas()
        if scoping_options.enable_forward_pass and pruning_did_occur(
            sas_task, scoped_sas
        ):
            try:
                simplify.filter_unreachable_propositions(scoped_sas, quiet=True)
            except simplify.Impossible:
                scoped_sas = unsolvable_sas_task("Simplified to trivially false goal")
            except simplify.TriviallySolvable:
                scoped_sas = solvable_sas_task("Simplified to empty goal")

            if scoping_options.enable_loop:
                if pruning_did_occur(sas_task, scoped_sas) and not is_trivial(
                    scoped_sas
                ):
                    sas_task = scoped_sas
                    should_continue = True
        track_scoping_progress(aggregated_info, scoped_sas)

    scoped_sas._sort_all()
    return scoped_sas, aggregated_info


def scope_sas_file(
    sas_path: str,
    scoping_options: ScopingOptions,
):
    parser = SasParser(pth=sas_path)
    parser.parse()
    sas_task: fd.SASTask = parser.to_fd()
    scoped_sas, info = scope_sas_task(sas_task, scoping_options)
    for key, val in sorted(info.items()):
        print(f"{key}: {val}")

    if scoping_options.write_output_file:
        filepath, ext = os.path.splitext(sas_path)
        output_filename = filepath + "_scoped" + ext
        with timers.timing("Writing output"):
            with open(output_filename, "w") as f:
                scoped_sas.output(f)
    return info


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("sas_file", help="path to sas file")
    parser.add_argument(
        "--disable-merging", dest="enable_merging", action="store_false"
    )
    parser.add_argument(
        "--disable-causal-links", dest="enable_causal_links", action="store_false"
    )
    parser.add_argument(
        "--variables-only", dest="enable_fact_based", action="store_false"
    )
    parser.add_argument(
        "--disable-forward-pass", dest="enable_forward_pass", action="store_false"
    )
    parser.add_argument("--disable-loop", dest="enable_loop", action="store_false")
    return parser.parse_args()


def main():
    args = parse_args()
    scoping_options = ScopingOptions(
        enable_causal_links=args.enable_causal_links,
        enable_merging=args.enable_merging,
        enable_fact_based=args.enable_fact_based,
        enable_forward_pass=args.enable_forward_pass,
        enable_loop=args.enable_loop,
    )
    scope_sas_file(args.sas_file, scoping_options)


if __name__ == "__main__":
    main()
