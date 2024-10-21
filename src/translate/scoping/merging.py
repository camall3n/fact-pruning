import itertools
from typing import Any

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


def merge(
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
    if not any(values == variable_domains[var] for var, values in precond_facts):
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
