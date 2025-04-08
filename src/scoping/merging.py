import itertools
from typing import Any
from collections import defaultdict

from normalize import convert_to_DNF
from pddl.conditions import Condition, Disjunction, Conjunction
from pddl.actions import Action, PropositionalAction
from sas_tasks import VarValPair
from scoping.actions import VarValAction
from scoping.factset import FactSet


def get_precondition_facts(action: VarValAction, variable_domains: FactSet) -> FactSet:
    precond_facts = FactSet()
    for var, val in action.precondition:
        if val == -1:
            # TODO: shouldn't these have all been removed during sas parsing?
            precond_facts.union(var, variable_domains[var])
        else:
            precond_facts.add(var, val)
    return precond_facts


def simplify_tautologies(
    partial_states: set[tuple[VarValPair]],
    all_precond_vars: set[Any],
    variable_domains: FactSet,
):
    """Condense the partial states by removing any unconstrained variables"""
    removed_vars = []
    for removed_var in all_precond_vars:
        partial_states_without_var = {
            tuple((var, val) for var, val in partial_state if var != removed_var)
            for partial_state in partial_states
        }

        if len(partial_states_without_var) * len(variable_domains[removed_var]) == len(
            partial_states
        ):
            partial_states = partial_states_without_var
            removed_vars.append(removed_var)
    return partial_states


# def is_more_general(precond_a, precond_b):
#     """Check if precond_a is more general than precond_b.
#     A precondition is more general if it's a proper subset of another precondition."""
#     precond_a_set = set(precond_a)
#     precond_b_set = set(precond_b)
#     return precond_a_set.issubset(precond_b_set) and precond_a_set != precond_b_set


# def topological_sort_preconditions(preconditions):
#     """Sort preconditions topologically so that more general preconditions come first.

#     For example, a precondition with (a=1) should come before one with (a=1, b=3)
#     because the first is more general than the second.
#     """
#     # Build a directed graph
#     graph = defaultdict(list)
#     in_degree = {precond: 0 for precond in preconditions}

#     # Create edges from more general to more specific preconditions
#     for precond_a in preconditions:
#         for precond_b in preconditions:
#             if is_more_general(precond_a, precond_b):
#                 graph[precond_a].append(precond_b)
#                 in_degree[precond_b] += 1

#     # Perform topological sort
#     sorted_preconditions = []
#     queue = [precond for precond, degree in in_degree.items() if degree == 0]

#     while queue:
#         current = queue.pop(0)
#         sorted_preconditions.append(current)

#         for neighbor in graph[current]:
#             in_degree[neighbor] -= 1
#             if in_degree[neighbor] == 0:
#                 queue.append(neighbor)

#     # If not all nodes are visited, there's a cycle (which shouldn't happen with preconditions)
#     if len(sorted_preconditions) != len(preconditions):
#         # Fall back to sorting by length as a simpler approximation
#         return sorted(preconditions, key=len)

#     return sorted_preconditions


def select_actions_matching_var(
    actions: list[VarValAction], var: Any
) -> list[VarValAction]:
    """Select actions that have a specific variable in their precondition"""
    selected_actions = []
    for action in actions:
        if any(a_var == var for a_var, _ in action.precondition):
            selected_actions.append(action)
    return selected_actions


def select_actions_matching_precond(
    actions: list[VarValAction], precond: list[VarValPair], free_var: Any
) -> list[VarValAction]:
    """Select actions that have a specific precondition"""
    selected_actions = []
    for action in actions:
        precond_without_var = sorted(
            [(var, val) for var, val in action.precondition if var != free_var]
        )
        if precond_without_var == sorted(precond):
            selected_actions.append(action)
    return selected_actions


def merge3(
    actions: list[VarValAction],
    relevant_variables: list[Any],
    variable_domains: FactSet,
) -> tuple[FactSet, dict]:
    """Get the relevant precondition facts after merging actions"""
    info = {
        "Scoping merge attempts": 0,
    }
    if len(actions) == 1:
        return get_precondition_facts(actions[0], variable_domains), info
    h0 = actions[0].effect_hash(relevant_variables)
    for a in actions[1:]:
        h = a.effect_hash(relevant_variables)
        assert h == h0, "Attempted to merge skills with different effects/costs"
    info["Scoping merge attempts"] += 1

    # Merging only helps if at least one variable spans its whole domain
    precond_facts = FactSet()
    is_empty_precondition = False
    for a in actions:
        precond_facts.union(get_precondition_facts(a, variable_domains))
        if not a.precondition:
            is_empty_precondition = True
    if is_empty_precondition:
        if all([len(action.precondition) == 0 for action in actions]):
            info["Scoping merge attempts"] = 0
        return FactSet(), info
    complete_vars = [
        var for var, values in precond_facts if values == variable_domains[var]
    ]
    if not complete_vars:
        return precond_facts, info

    relevant_precond_facts = FactSet()
    visited_action_names = set()
    for var_to_remove in complete_vars:
        # consider all actions that have this variable in their precondition
        # and look for ways to simplify the preconditions
        considered_actions = select_actions_matching_var(actions, var_to_remove)
        if not considered_actions:
            # no actions have this variable in their precondition, so the
            # variable can be deleted, and there are no relevant facts to add
            continue

        # compute the unique preconditions for the actions, excluding this variable
        preconds_without_var = [
            [(var, val) for var, val in action.precondition if var != var_to_remove]
            for action in considered_actions
        ]
        unique_preconds_without_var = set(
            [tuple(sorted(precond)) for precond in preconds_without_var]
        )
        for precond_without_var in unique_preconds_without_var:
            # get all actions that match this partial precondition
            filtered_actions = select_actions_matching_precond(
                actions, precond_without_var, var_to_remove
            )

            # get list of values of var_to_remove required for the filtered_actions
            var_to_remove_values = [
                FactSet(a.precondition)[var_to_remove] for a in filtered_actions
            ]
            var_to_remove_values = set().union(
                *[
                    val_set if val_set else variable_domains[var_to_remove]
                    for val_set in var_to_remove_values
                ]
            )

            # check if all possible values of var_to_remove are covered by some action
            if var_to_remove_values != variable_domains[var_to_remove]:
                # not all possible values of the variable are covered by some action
                # so we need to store the var_to_remove facts
                relevant_precond_facts.add(
                    (var_to_remove, val) for val in var_to_remove_values
                )
            # either way, we need to store the precondition facts without the variable
            relevant_precond_facts.add(precond_without_var)

            # mark the filtered_actions as visited
            for a in filtered_actions:
                visited_action_names.add(a.name)

    # We should have marked actions as visited already so there shouldn't be too
    # many left to consider. There are no variables to remove in these actions,
    # because we've already tried to remove all possible variables. so we just mark
    # their preconditions as relevant.
    for action in actions:
        if action.name not in visited_action_names:
            relevant_precond_facts.add(action.precondition)
    return relevant_precond_facts, info


def merge(
    actions: list[VarValAction],
    relevant_variables: list[Any],
    variable_domains: FactSet,
) -> tuple[FactSet, dict]:
    return merge3(actions, relevant_variables, variable_domains)


def merge2(
    actions: list[VarValAction],
    relevant_variables: list[Any],
    variable_domains: FactSet,
) -> tuple[FactSet, dict]:
    """Get the relevant precondition facts after merging actions"""
    info = {
        "Scoping merge attempts": 0,
    }
    if len(actions) == 1:
        return get_precondition_facts(actions[0], variable_domains), info
    h0 = actions[0].effect_hash(relevant_variables)
    for a in actions[1:]:
        h = a.effect_hash(relevant_variables)
        assert h == h0, "Attempted to merge skills with different effects/costs"
    info["Scoping merge attempts"] += 1

    # Merging only helps if at least one variable spans its whole domain
    precond_facts = FactSet()
    is_empty_precondition = False
    for a in actions:
        precond_facts.union(get_precondition_facts(a, variable_domains))
        if not a.precondition:
            is_empty_precondition = True
    if is_empty_precondition:
        if all([len(action.precondition) == 0 for action in actions]):
            info["Scoping merge attempts"] = 0
        return FactSet(), info
    complete_vars = [
        var for var, values in precond_facts if values == variable_domains[var]
    ]
    if not complete_vars:
        return precond_facts, info

    # Collect the precondition variables
    precond_vars_by_action = [
        sorted(set([var for var, _ in a.precondition])) for a in actions
    ]
    all_precond_vars = sorted(set().union(*precond_vars_by_action))

    reduced_var_domains = FactSet(variable_domains)
    removed_vars = []

    # See whether we can remove any of the complete variables
    for var_to_remove in complete_vars:
        safe_to_remove = True
        # scan over all possible assignments to the remaining variables
        remaining_vars = [var for var in all_precond_vars if var != var_to_remove]
        remaining_var_domains = [reduced_var_domains[var] for var in remaining_vars]
        remaining_var_partial_states = itertools.product(*remaining_var_domains)
        for i, partial_state in enumerate(remaining_var_partial_states):
            # prepare to reconstruct the full state for each value of var_to_remove
            partial_state = list(partial_state)
            var_to_remove_index = all_precond_vars.index(var_to_remove)
            partial_state.insert(var_to_remove_index, None)
            always_has_action = True
            never_has_action = True
            for val in reduced_var_domains[var_to_remove]:
                partial_state[var_to_remove_index] = val
                full_state = list(zip(all_precond_vars, partial_state))
                has_action = any(action.can_run(full_state) for action in actions)
                if has_action:
                    never_has_action = False
                else:
                    always_has_action = False
                if not (always_has_action or never_has_action):
                    break

            if not (always_has_action or never_has_action):
                # found a partial state with inconsistent action applicability so
                # this var can't be removed. (no need to check more partial states)
                safe_to_remove = False
                break

        if safe_to_remove:
            # for the rest of the merge, we can set this var to a single value
            # to speed up the remaining checks.
            first_val = reduced_var_domains[var_to_remove].pop()
            reduced_var_domains[var_to_remove].clear()
            reduced_var_domains[var_to_remove].add(first_val)
            removed_vars.append(var_to_remove)

    relevant_precond_facts = FactSet()
    for var_to_remove in all_precond_vars:
        if var_to_remove not in removed_vars:
            relevant_precond_facts.union(var_to_remove, precond_facts[var_to_remove])

    return relevant_precond_facts, info


def merge1(
    actions: list[VarValAction],
    relevant_variables: list[Any],
    variable_domains: FactSet,
) -> FactSet:
    """Get the relevant precondition facts after merging actions"""
    if len(actions) == 1:
        return get_precondition_facts(actions[0], variable_domains)
    h0 = actions[0].effect_hash(relevant_variables)
    for a in actions[1:]:
        h = a.effect_hash(relevant_variables)
        assert h == h0, "Attempted to merge skills with different effects/costs"

    # Merging only helps if at least one variable spans its whole domain
    precond_facts = FactSet()
    for a in actions:
        precond_facts.union(get_precondition_facts(a, variable_domains))
        if not a.precondition:
            return FactSet()
    complete_vars = [
        var for var, values in precond_facts if values == variable_domains[var]
    ]
    if not complete_vars:
        return precond_facts

    # Collect the precondition variables
    precond_vars_by_action = [set([var for var, _ in a.precondition]) for a in actions]
    all_precond_vars = set().union(*precond_vars_by_action)

    # Build the set of satisfying partial states for the merged action
    satisfying_partial_states = set()
    for action, precond_vars in zip(actions, precond_vars_by_action):
        dont_care_vars = all_precond_vars.difference(precond_vars)
        dont_care_domains = [variable_domains[var] for var in dont_care_vars]
        dont_care_val_combos = list(itertools.product(*dont_care_domains))
        dont_care_varval_combos = [
            list(zip(dont_care_vars, dont_care_vals))
            for dont_care_vals in dont_care_val_combos
        ]
        for dont_care_varvals in dont_care_varval_combos:
            partial_state = tuple(sorted(action.precondition + dont_care_varvals))
            satisfying_partial_states.add(partial_state)

    satisfying_partial_states = simplify_tautologies(
        satisfying_partial_states, all_precond_vars, variable_domains
    )
    relevant_precond_facts = FactSet()
    for partial_state in satisfying_partial_states:
        relevant_precond_facts.add(partial_state)
    return relevant_precond_facts


def merge_pddl(actions: list[(Action | PropositionalAction)]):
    # Check if actions have same effects (on relevant vars)!
    #  - either pass relevant_vars as input to merge()
    #  - or scope the actions so they don't include irrelevant vars before sending to merge()
    h0 = actions[0].hashable()
    for a in actions[1:]:
        h = a.hashable()
        assert h == h0, "Attempted to merge skills with different effects"
    if isinstance(actions[0], PropositionalAction):
        get_precond = lambda action: Conjunction(action.precondition)
    else:
        get_precond = lambda action: action.precondition
    formula_dnf = Disjunction([get_precond(a) for a in actions])
    formula_cnf = dnf2cnf(formula_dnf)
    return formula_cnf, formula_dnf


def fully_simplify(formula: Condition, max_iters: int = 10):
    result = formula
    for _ in range(max_iters):
        simplified = result.simplified()
        if simplified == result:
            break
        else:
            result = simplified
    return result


def dnf2cnf(formula: Disjunction):
    """Convert formula ϕ to CNF"""
    formula = fully_simplify(formula)
    # print('ϕ')
    # formula.dump()

    # 1. negate ϕ => ¬ϕ
    negated_formula = fully_simplify(formula.negate())
    # print('¬ϕ')
    # negated_formula.dump()

    # 2. convert ¬ϕ to DNF
    negated_DNF = fully_simplify(convert_to_DNF(negated_formula))
    # print('(¬ϕ)_DNF')
    # negated_DNF.dump()

    # 3. negate result and simplify
    cnf = fully_simplify(negated_DNF.negate())
    # print('CNF')
    # cnf.dump()

    return cnf
