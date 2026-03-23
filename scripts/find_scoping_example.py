#!/usr/bin/env python
"""Search for a small planning task where every scoping upgrade is independently useful.

Randomly generates ScopingTasks and tests whether each successive configuration
(V → F → FC → FCM → FCMR → FCMRL) produces strictly fewer actions.
"""

import io
import os
import random
import string
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "src/translate")

from scoping.actions import VarValAction
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.scoping import scope
from scoping.task import ScopingTask

CONFIGS = [
    ("V", ScopingOptions(0, 0, 0, 0, 0)),
    ("F", ScopingOptions(0, 0, 1, 0, 0)),
    ("FC", ScopingOptions(1, 0, 1, 0, 0)),
    ("FCM", ScopingOptions(1, 1, 1, 0, 0)),
    ("FCMR", ScopingOptions(1, 1, 1, 1, 0)),
    ("FCMRL", ScopingOptions(1, 1, 1, 1, 1)),
]


def random_task(rng, n_vars=4, max_domain=4, n_actions=10):
    """Generate a random ScopingTask."""
    # Random domains: each variable gets domain size 2-max_domain
    var_names = list(string.ascii_lowercase[:n_vars])
    domains_dict = {}
    for v in var_names:
        size = rng.randint(2, max_domain)
        domains_dict[v] = set(range(size))
    domains = FactSet(domains_dict)

    # Init: all zeros
    init = [(v, 0) for v in var_names]

    # Goal: 1-2 facts on distinct variables, at least one non-zero
    n_goal = rng.randint(1, 2)
    goal_vars = rng.sample(var_names, min(n_goal, n_vars))
    goal = [(v, rng.choice(sorted(domains_dict[v]))) for v in goal_vars]
    # Ensure at least one non-zero goal fact
    if all(val == 0 for _, val in goal):
        v = rng.choice(var_names)
        non_zero = [x for x in domains_dict[v] if x != 0]
        if non_zero:
            goal[0] = (v, rng.choice(non_zero))
        else:
            return None  # Can't make a non-trivial goal

    # Random actions
    action_names = list(string.ascii_lowercase[:n_actions])
    actions = []
    for name in action_names:
        # 0-2 preconditions on random variables
        n_pre = rng.randint(0, 2)
        pre_vars = rng.sample(var_names, min(n_pre, n_vars))
        precondition = [(v, rng.choice(sorted(domains_dict[v]))) for v in pre_vars]

        # 1-3 effects on random variables
        n_eff = rng.randint(1, 3)
        eff_vars = rng.sample(var_names, min(n_eff, n_vars))
        effect = [(v, rng.choice(sorted(domains_dict[v]))) for v in eff_vars]

        # Reject if effect contains entire precondition
        if precondition and set(precondition) <= set(effect):
            return None

        actions.append(VarValAction(name, precondition, effect, 1))

    return ScopingTask(domains, init, goal, actions)


def get_action_names(task):
    return frozenset(a.name for a in task.actions)


def check_task(task):
    """Check if each config strictly reduces the action set. Returns list of action sets or None."""
    # All but at most 1 action must be relaxed-reachable from initial state
    try:
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            reachable = scope(task, ScopingOptions(0, 0, 1, 1, 0))
        finally:
            sys.stdout = old_stdout
    except Exception:
        return None
    unreachable = get_action_names(task) - get_action_names(reachable)
    if len(unreachable) > 1:
        return None

    prev_actions = None
    results = []
    for name, opts in CONFIGS:
        try:
            # Suppress print output from scope()
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                scoped = scope(task, opts)
            finally:
                sys.stdout = old_stdout
        except Exception:
            return None
        actions = get_action_names(scoped)
        if prev_actions is not None and not (actions < prev_actions):
            return None
        results.append((name, actions))
        prev_actions = actions
    if not results[-1][1]:
        return None  # Final action set is empty
    return results


def cleanup_task(task, results):
    """Canonicalize a task for human readability."""
    # Step 1: Collect used values per variable, remap to consecutive from 0
    used = {v: set() for v in task.domains.facts}
    for v, val in task.init + task.goal:
        used[v].add(val)
    for a in task.actions:
        for v, val in a.precondition + a.effect:
            used[v].add(val)

    # All variables must have at least 2 used values
    if any(len(vals) < 2 for vals in used.values()):
        return None

    val_maps = {}
    for v in used:
        old_vals = sorted(used[v])
        val_maps[v] = {old: new for new, old in enumerate(old_vals)}

    # Step 2: Rename variables by domain size (ascending), then alphabetical
    old_vars = sorted(used.keys(), key=lambda v: (len(used[v]), v))
    new_var_names = list(
        string.ascii_lowercase[23 : 23 + len(old_vars)]
    )  # x, y, z, w (wraps)
    if len(old_vars) > 3:
        new_var_names = ["w", "x", "y", "z"][: len(old_vars)]
    else:
        new_var_names = ["x", "y", "z"][: len(old_vars)]
    var_map = dict(zip(old_vars, new_var_names))

    def remap_facts(facts):
        return sorted([(var_map[v], val_maps[v][val]) for v, val in facts])

    new_domains = FactSet({var_map[v]: set(range(len(used[v]))) for v in used})
    new_init = remap_facts(task.init)
    new_goal = remap_facts(task.goal)

    # Step 3 & 4: Rename actions by removal order (last removed = last letter)
    # Build removal order from results
    action_sets = [actions for _, actions in results]
    # Actions kept at each level: FCMRL ⊂ FCMR ⊂ FCM ⊂ FC ⊂ F ⊂ V
    # Name actions so that those kept longest get first letters
    name_order = []
    # Start from the most-pruned set, add in order of "when they survive until"
    for i in range(len(action_sets) - 1, -1, -1):
        if i == len(action_sets) - 1:
            # Actions in the final (most pruned) set - these survive everything
            layer = sorted(action_sets[i])
        else:
            # Actions in this set but not in the next (more pruned) set
            layer = sorted(action_sets[i] - action_sets[i + 1])
        name_order.extend(layer)

    action_name_map = {
        old: string.ascii_lowercase[j] for j, old in enumerate(name_order)
    }

    new_actions = []
    for old_name in name_order:
        old_action = next(a for a in task.actions if a.name == old_name)
        pre = remap_facts(old_action.precondition)
        eff = [f for f in remap_facts(old_action.effect) if f not in pre]
        new_actions.append(
            VarValAction(
                action_name_map[old_name],
                pre,
                eff,
                old_action.cost,
            )
        )

    # Check all actions are unique (same precondition + effect = duplicate)
    signatures = set()
    for a in new_actions:
        sig = (tuple(a.precondition), tuple(a.effect))
        if sig in signatures:
            return None
        signatures.add(sig)

    return ScopingTask(new_domains, new_init, new_goal, new_actions)


def format_facts(facts):
    """Format a list of (var, val) tuples with double quotes."""
    return "[" + ", ".join(f'("{v}", {val})' for v, val in facts) + "]"


def format_task(task, results):
    """Format a found task as copy-pasteable Python."""
    sorted_vars = sorted(task.domains.facts.keys())
    lines = []
    lines.append("domains=FactSet({")
    for i, v in enumerate(sorted_vars):
        vals = sorted(task.domains.facts[v])
        trailing = "," if i < len(sorted_vars) - 1 else ""
        lines.append(f'    "{v}": {{{", ".join(str(x) for x in vals)}}}{trailing}')
    lines.append("}),")
    lines.append(f"init={format_facts(task.init)},")
    lines.append(f"goal={format_facts(task.goal)},")
    lines.append("actions=[")
    for a in task.actions:
        lines.append(
            f'    VarValAction("{a.name}", {format_facts(a.precondition)}, {format_facts(a.effect)}, {a.cost}),'
        )
    lines.append("],")
    lines.append("")
    lines.append("")
    lines.append("# Action sets per configuration:")
    for name, actions in results:
        lines.append(f"#   {name:6s}: {''.join(sorted(actions))}")
    return "\n".join(lines)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    rng = random.Random(seed)
    found = 0
    attempts = 0

    print(f"Searching (seed={seed})...")
    while found < 5:
        attempts += 1
        if attempts % 10000 == 0:
            print(f"  ...{attempts} attempts so far", flush=True)
        task = random_task(rng)
        if task is None:
            continue
        results = check_task(task)
        if results is not None:
            cleaned = cleanup_task(task, results)
            if cleaned is None:
                continue
            cleaned_results = check_task(cleaned)
            if cleaned_results is None:
                continue  # Cleanup broke the property, skip
            found += 1
            print(f"\n{'=' * 60}")
            print(f"Found example #{found} (after {attempts} attempts)")
            print(f"{'=' * 60}")
            print(format_task(cleaned, cleaned_results))

    print(f"\nDone. Found {found} examples in {attempts} attempts.")


if __name__ == "__main__":
    main()
