#!%cd ~/dev/downward/src/translate
#
import argparse
import os

import sas_tasks as fd
from scoping.actions import VarValAction
from scoping.backward import compute_goal_relevance
from scoping.forward import compute_reachability
from scoping.factset import FactSet, VarValPair
from scoping.options import ScopingOptions
from scoping.sas_parser import SasParser
from scoping.task import ScopingTask


def scope_backward(
    scoping_task: ScopingTask,
    enable_merging: bool = True,
    enable_causal_links: bool = True,
    enable_fact_based: bool = True,
) -> ScopingTask:
    facts, actions = compute_goal_relevance(
        scoping_task=scoping_task,
        enable_merging=enable_merging,
        enable_causal_links=enable_causal_links,
        enable_fact_based=enable_fact_based,
    )
    # Explicitly add precond facts in case preconds were dropped in a merge
    precond_facts = FactSet()
    for a in actions:
        precond_facts.add(a.precondition)
    facts.union(precond_facts)

    # Also add side-effects on vars that appear in preconds
    for a in actions:
        for var, val in a.effect:
            if var in precond_facts.variables:
                facts.add(var, val)
    return prune_task(scoping_task, facts, actions)


def scope_forward(scoping_task: ScopingTask) -> tuple[ScopingTask, bool]:
    facts, actions, goal_reachable = compute_reachability(scoping_task=scoping_task)
    return prune_task(scoping_task, facts, actions), goal_reachable


def prune_facts(fact_list: list[VarValPair], relevant_facts: FactSet):
    return [fact for fact in fact_list if fact in relevant_facts]


def prune_task(
    scoping_task: ScopingTask, facts: FactSet, actions: list[VarValAction]
) -> ScopingTask:
    facts = FactSet({var: values for var, values in facts if len(values) > 1})

    init = prune_facts(scoping_task.init, facts)
    goal = prune_facts(scoping_task.goal, facts)
    actions = [
        VarValAction(
            name=a.name,
            precondition=prune_facts(a.precondition, facts),
            effect=prune_facts(a.effect, facts),
            cost=a.cost,
        )
        for a in actions
    ]
    mutexes = [prune_facts(mutex, facts) for mutex in scoping_task.mutexes]
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
    )


def scope(
    scoping_task: ScopingTask,
    options: ScopingOptions,
):
    while True:
        scoped_task = scope_backward(
            scoping_task,
            enable_merging=options.enable_merging,
            enable_causal_links=options.enable_causal_links,
            enable_fact_based=options.enable_fact_based,
        )
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


def scope_sas(
    sas_path: str,
    scoping_options: ScopingOptions,
):
    # sas_path = "../../toy-minecraft-merging.sas"
    parser = SasParser(pth=sas_path)
    parser.parse()
    sas_task: fd.SASTask = parser.to_fd()
    # sas_task.dump()
    scoping_task = ScopingTask.from_sas(sas_task)
    scoped_task = scope(scoping_task, scoping_options)
    scoped_sas = scoped_task.to_sas()
    # scoped_sas.dump()
    filepath, ext = os.path.splitext(sas_path)
    output_filename = filepath + "_scoped" + ext
    with open(output_filename, "w") as f:
        scoped_sas.output(f)


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
    scope_sas(args.sas_file, scoping_options)


if __name__ == "__main__":
    main()
