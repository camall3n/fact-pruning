"""Text-based trace of the scoping algorithm for any mode (V, F, FC, FCM, FCMR, FCMRL).

Mirrors the actual code path: scope() → relevance() → prune() → prune_non_reachable_via_sas().
"""

from scoping.actions import VarValAction
from scoping.backward import coarsen_facts_to_variables
from scoping.factset import FactSet
from scoping.merging import get_precondition_facts, merge
from scoping.options import ScopingOptions
from scoping.scoping import compute_sas_reachability, partition_actions, prune
from scoping.task import ScopingTask


def prune_non_reachable_preserve_names(scoping_task: ScopingTask) -> ScopingTask:
    """Like prune_non_reachable_via_sas but preserves original variable names and values."""
    # Record the mappings that to_sas() will use
    sorted_vars = sorted(scoping_task.domains.variables)
    sorted_vals = {var: sorted(vals) for var, vals in scoping_task.domains}

    sas_task = scoping_task.to_sas()
    scoped_sas = compute_sas_reachability(sas_task)
    result = ScopingTask.from_sas(scoped_sas)

    # Build reverse mappings: SAS index → original var name, SAS val index → original val
    remaining_sas_vars = sorted(result.domains.variables)
    var_map = {i: sorted_vars[i] for i in remaining_sas_vars if i < len(sorted_vars)}
    # For each remaining SAS var, the SAS values 0..k map back to sorted_vals[original_var][0..k]
    val_map = {}
    for sas_var, orig_var in var_map.items():
        orig_sorted = sorted_vals[orig_var]
        val_map[sas_var] = {i: orig_sorted[i] for i in range(len(orig_sorted))}

    def remap_facts(facts):
        return [(var_map.get(v, v), val_map.get(v, {}).get(val, val)) for v, val in facts]

    domains = FactSet({
        var_map[v]: {val_map[v][val] for val in vals}
        for v, vals in result.domains
        if v in var_map
    })
    actions = [
        VarValAction(a.name, remap_facts(a.precondition), remap_facts(a.effect), a.cost)
        for a in result.actions
    ]
    return ScopingTask(
        domains=domains,
        init=remap_facts(result.init),
        goal=remap_facts(result.goal),
        actions=actions,
        mutexes=[remap_facts(m) for m in result.mutexes] if result.mutexes else [],
        metric=result.metric,
        value_names=scoping_task.value_names,
    )


def fmt_facts(facts: FactSet) -> str:
    """Format a FactSet as {(v,0),(v,1),...} sorted."""
    pairs = []
    for var, values in sorted(facts.facts.items()):
        for val in sorted(values):
            pairs.append(f"({var},{val})")
    return "{" + ", ".join(pairs) + "}" if pairs else "{}"


def fmt_actions(actions) -> str:
    return "{" + ",".join(sorted(a.name for a in actions)) + "}"


def fmt_effect_hash(eh) -> str:
    facts, cost = eh
    return "[" + ", ".join(f"({v},{val})" for v, val in facts) + "]"


def trace_relevance(task: ScopingTask, options: ScopingOptions) -> list[VarValAction]:
    """Trace the backward relevance analysis (mirrors relevance() in scoping.py)."""
    s0 = FactSet(task.init)
    prev_facts = FactSet(task.goal)
    prev_actions = []
    iteration = 0

    if not options.enable_fact_based:
        coarsen_facts_to_variables(prev_facts, task.domains)

    print(f"  F⁰ = {fmt_facts(prev_facts)}")
    print(f"  O⁰ = {fmt_actions(prev_actions)}")

    while True:
        iteration += 1
        print(f"\n  --- Iteration {iteration} ---")

        # Causal link filtering (inline, matching relevance())
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

            print(f"  C = {fmt_facts(causally_linked_facts)}")
            print(f"  F̄ = {fmt_facts(filtered_facts)}")
        else:
            filtered_facts = prev_facts

        if not options.enable_fact_based:
            coarsen_facts_to_variables(filtered_facts, task.domains)

        # Select actions (inline loop matching relevance())
        actions = []
        for a in task.actions:
            for f in a.effect:
                if f in filtered_facts:
                    actions.append(a)
                    break

        print(f"  Selected actions: {fmt_actions(actions)}")

        # reduce_and_get_facts: partition + merge
        relevant_vars = prev_facts.variables
        print(f"  V(F) = {{{','.join(str(v) for v in sorted(relevant_vars))}}}")

        if options.enable_merging:
            action_partitions = partition_actions(relevant_vars, actions)
        else:
            action_partitions = [[a] for a in actions]

        facts = FactSet(prev_facts)
        print(f"  Partitions:")
        for part in action_partitions:
            eh = part[0].effect_hash(relevant_vars)
            merged_pre, _ = merge(part, relevant_vars, task.domains)
            names = ",".join(sorted(a.name for a in part))
            print(f"    {fmt_effect_hash(eh)}: {{{names}}}")
            if len(part) > 1:
                for a in part:
                    pre = get_precondition_facts(a, task.domains)
                    print(f"      {a.name}: pre = {fmt_facts(pre)}")
                print(f"      merged pre → {fmt_facts(merged_pre)}")
            else:
                print(f"      pre = {fmt_facts(merged_pre)}")
            facts.union(merged_pre)

        if not options.enable_fact_based:
            coarsen_facts_to_variables(facts, task.domains)

        print(f"  F' = {fmt_facts(facts)}")

        if facts == prev_facts and len(actions) == len(prev_actions):
            print(f"  *** Converged ***")
            break
        prev_facts = facts
        prev_actions = actions

    return actions


def trace(task: ScopingTask, options: ScopingOptions):
    """Trace the full scoping algorithm (mirrors scope() in scoping.py)."""
    mode_parts = []
    if not options.enable_fact_based:
        mode_parts.append("V")
    else:
        mode_parts.append("F")
    if options.enable_causal_links:
        mode_parts.append("C")
    if options.enable_merging:
        mode_parts.append("M")
    if options.enable_forward_pass:
        mode_parts.append("R")
    if options.enable_loop:
        mode_parts.append("L")
    mode = "".join(mode_parts)

    print(f"=== Trace: {mode} ===")
    print(f"Init: {task.init}")
    print(f"Goal: {task.goal}")
    print(f"Actions: {','.join(sorted(a.name for a in task.actions))}")
    print()

    round_num = 0
    current_task = task
    while True:
        round_num += 1
        if options.enable_loop and round_num > 1:
            print(f"\n{'='*40}")
        print(f"Backward pass{f' (round {round_num})' if options.enable_loop else ''}:")

        # relevance()
        actions = trace_relevance(current_task, options)
        print(f"\n  Result: O = {fmt_actions(actions)}")

        # prune()
        scoped_task = prune(current_task, actions)
        print(f"  After pruning: {','.join(sorted(a.name for a in scoped_task.actions))} actions")
        print(f"  Domains: {{{', '.join(f'{v}:{sorted(vals)}' for v, vals in sorted(scoped_task.domains.facts.items()))}}}")

        if not options.enable_forward_pass or scoped_task == current_task:
            break

        # prune_non_reachable_via_sas()
        print(f"\nForward pass{f' (round {round_num})' if options.enable_loop else ''}:")
        prev_action_names = set(a.name for a in scoped_task.actions)
        scoped_task = prune_non_reachable_preserve_names(scoped_task)
        new_action_names = set(a.name for a in scoped_task.actions)
        removed = prev_action_names - new_action_names
        if removed:
            print(f"  Removed unreachable: {{{','.join(sorted(removed))}}}")
        else:
            print(f"  No unreachable actions removed")
        print(f"  Actions: {','.join(sorted(a.name for a in scoped_task.actions))}")

        if (
            not options.enable_loop
            or scoped_task == current_task
            or scoped_task.is_trivial()
        ):
            break
        current_task = scoped_task

    print(f"\n=== Final: {fmt_actions(scoped_task.actions)} ===")


EXAMPLES = {
    3: lambda: ScopingTask(
        domains=FactSet({"w": {0, 1}, "x": {0, 1}, "y": {0, 1, 2, 3}, "z": {0, 1, 2, 3}}),
        init=[("w", 0), ("x", 0), ("y", 0), ("z", 0)],
        goal=[("x", 0), ("z", 2)],
        actions=[
            VarValAction("a", [], [("z", 2)], 1),
            VarValAction("b", [], [("y", 0), ("z", 1)], 1),
            VarValAction("c", [("z", 1)], [("x", 0), ("z", 2)], 1),
            VarValAction("d", [("y", 1)], [("w", 0), ("y", 2), ("z", 1)], 1),
            VarValAction("e", [("y", 2)], [("w", 1), ("y", 0), ("z", 2)], 1),
            VarValAction("f", [], [("w", 0), ("y", 1)], 1),
            VarValAction("g", [], [("z", 3)], 1),
            VarValAction("h", [], [("w", 1), ("x", 1)], 1),
            VarValAction("i", [("x", 1), ("z", 3)], [("x", 0), ("y", 3)], 1),
            VarValAction("j", [("y", 3)], [("w", 0), ("z", 0)], 1),
        ],
    ),
}

CONFIGS = {
    "V": ScopingOptions(0, 0, 0, 0, 0),
    "F": ScopingOptions(0, 0, 1, 0, 0),
    "FC": ScopingOptions(1, 0, 1, 0, 0),
    "FCM": ScopingOptions(1, 1, 1, 0, 0),
    "FCMR": ScopingOptions(1, 1, 1, 1, 0),
    "FCMRL": ScopingOptions(1, 1, 1, 1, 1),
}


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    example = int(args[0]) if args else 3
    mode = args[1] if len(args) > 1 else "FCM"

    task = EXAMPLES[example]()
    trace(task, CONFIGS[mode])
