#!%cd ~/dev/downward/src/translate

from timer import Timer

from scoping.actions import VarValAction
from scoping.factset import FactSet
from scoping.merging import merge1, merge2, merge3


# a1 = VarValAction(
#     "a1",
#     [("x", 0), ("v1", 0)],
#     [("x", 2)],
#     1,
# )

# b1 = VarValAction(
#     "b1",
#     [("x", 0), ("v1", 1)],
#     [("x", 2)],
#     1,
# )

# a2 = VarValAction(
#     "a2",
#     [("x", 0), ("v2", 0)],
#     [("x", 2)],
#     1,
# )

# b2 = VarValAction(
#     "b2",
#     [("x", 0), ("v2", 1)],
#     [("x", 2)],
#     1,
# )


for n_action_pairs in range(1, 17):
    actions = [
        VarValAction(f"a{i:02d}", [("x", 0), (f"v{i}", 0)], [("x", 1)], 1)
        for i in range(n_action_pairs)
    ] + [
        VarValAction(f"b{i:02d}", [("x", 0), (f"v{i}", 1)], [("x", 1)], 1)
        for i in range(n_action_pairs)
    ]

    variable_domains = FactSet()
    for action in actions:
        variable_domains.add(action.precondition)
        variable_domains.add(action.effect)

    relevant_variables = variable_domains.variables

    with Timer(f"merge3(n{n_action_pairs})"):
        relevant_precondition_facts3, _ = merge3(
            actions=actions,
            relevant_variables=relevant_variables,
            variable_domains=variable_domains,
        )

    with Timer(f"merge2(n{n_action_pairs})"):
        relevant_precondition_facts2, _ = merge2(
            actions=actions,
            relevant_variables=relevant_variables,
            variable_domains=variable_domains,
        )
    with Timer(f"merge1(n{n_action_pairs})"):
        relevant_precondition_facts1 = merge1(
            actions=actions,
            relevant_variables=relevant_variables,
            variable_domains=variable_domains,
        )

    assert relevant_precondition_facts1 == relevant_precondition_facts2
    assert relevant_precondition_facts2 == relevant_precondition_facts3

Timer.stats()

# assert relevant_precondition_facts == relevant_precondition_facts_old

# %%
