#!%cd ~/dev/downward/src/translate
# %%
from scoping.actions import VarValAction
from scoping.sas import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph

domains_task1 = FactSet(
    {
        "v0": {0, 1},
        "v1": {0, 1},
        "v2": {0, 1},
        "v3": {0, 1, 2},
        "v4": {0, 1},
    }
)
init_task1 = [("v0", 0), ("v1", 1), ("v2", 1), ("v3", 2), ("v4", 1)]
goal_task1 = [("v2", 0), ("v3", 2), ("v4", 1)]
actions_task1 = [
    VarValAction(
        "(A)",
        [("v0", 0), ("v3", 2), ("v4", 1)],
        [("v0", 1), ("v1", 0), ("v3", 1), ("v4", 0)],
        30,
    ),
    VarValAction(
        "(A')",
        [("v0", 0), ("v3", 2), ("v4", 0)],
        [("v0", 1), ("v1", 0), ("v3", 1), ("v4", 0)],
        30,
    ),
    VarValAction(
        "(B)",
        [("v1", 0), ("v3", 1), ("v4", 0)],
        [("v4", 1)],
        45,
    ),
    VarValAction(
        "(B')",
        [("v1", 0), ("v3", 1), ("v4", 1)],
        [("v4", 0)],
        30,
    ),
    VarValAction(
        "(C)",
        [("v4", 1), ("v3", 1)],
        [("v1", 1), ("v2", 0), ("v3", 2), ("v4", 1)],
        10,
    ),
    VarValAction(
        "(C')",
        [("v4", 0), ("v3", 1)],
        [("v1", 1), ("v2", 0), ("v3", 2), ("v4", 0)],
        10,
    ),
    VarValAction(
        "(D)",
        [("v0", 0), ("v3", 2), ("v4", 1)],
        [("v0", 1), ("v1", 0), ("v3", 0), ("v4", 1)],
        45,
    ),
    VarValAction(
        "(D')",
        [("v0", 0), ("v3", 2), ("v4", 0)],
        [("v0", 1), ("v1", 0), ("v3", 0), ("v4", 1)],
        45,
    ),
    VarValAction(
        "(E)",
        [("v1", 0), ("v3", 0), ("v4", 1)],
        [("v1", 0), ("v3", 1), ("v4", 1)],
        45,
    ),
    VarValAction(
        "(E')",
        [("v1", 0), ("v3", 0), ("v4", 0)],
        [("v1", 0), ("v3", 1), ("v4", 1)],
        45,
    ),
]
value_names_task1 = {
    "v0": "01",
    "v1": "01",
    "v2": "01",
    "v3": "012",
    "v4": "01",
}


def make_task1():
    return ScopingTask(
        domains=domains_task1,
        init=init_task1,
        goal=goal_task1,
        actions=actions_task1,
        metric=True,
        value_names=value_names_task1,
    )


def make_task2():
    domains_task2 = FactSet(domains_task1)
    domains_task2.union(FactSet({"v5": {0, 1}}))
    actions_task2 = actions_task1 + [
        VarValAction(
            "(G)",
            goal_task1,
            [("v5", 1)],
            0,
        )
    ]
    value_names_task2 = value_names_task1.copy()
    value_names_task2["v5"] = "01"

    return ScopingTask(
        domains=domains_task2,
        init=init_task1 + [("v5", 0)],
        goal=[("v5", 1)],
        actions=actions_task2,
        metric=True,
        value_names=value_names_task2,
    )


domains_task3 = FactSet(
    {
        "v0": {0, 1},
        "v1": {0, 1},
        "v2": {0, 1},
        "v3": {0, 1, 2},
        "v4": {0, 1},
    }
)
init_task3 = [("v0", 0), ("v1", 1), ("v2", 1), ("v3", 2), ("v4", 1)]
goal_task3 = [("v2", 0), ("v3", 2), ("v4", 1)]
actions_task3 = [
    VarValAction(
        "(A)",
        [("v0", 0), ("v3", 2), ("v4", 1)],
        [("v0", 1), ("v1", 0), ("v3", 1), ("v4", 0)],
        30,
    ),
    VarValAction(
        "(A')",
        [("v0", 0), ("v3", 2), ("v4", 0)],
        [("v0", 1), ("v1", 0), ("v3", 1)],
        30,
    ),
    VarValAction(
        "(B)",
        [("v1", 0), ("v3", 1), ("v4", 0)],
        [("v4", 1)],
        45,
    ),
    VarValAction(
        "(B')",
        [("v1", 0), ("v3", 1), ("v4", 1)],
        [("v4", 0)],
        30,
    ),
    VarValAction(
        "(C)",
        [("v3", 1), ("v4", 1)],
        [("v1", 1), ("v2", 0), ("v3", 2)],
        10,
    ),
    VarValAction(
        "(C')",
        [("v3", 1), ("v4", 0)],
        [("v1", 1), ("v2", 0), ("v3", 2)],
        10,
    ),
    VarValAction(
        "(D)",
        [("v0", 0), ("v3", 2), ("v4", 1)],
        [("v0", 1), ("v1", 0), ("v3", 0)],
        45,
    ),
    VarValAction(
        "(D')",
        [("v0", 0), ("v3", 2), ("v4", 0)],
        [("v0", 1), ("v1", 0), ("v3", 0), ("v4", 1)],
        45,
    ),
    VarValAction(
        "(E)",
        [("v1", 0), ("v3", 0), ("v4", 1)],
        [("v1", 0), ("v3", 1)],
        45,
    ),
    VarValAction(
        "(E')",
        [("v1", 0), ("v3", 0), ("v4", 0)],
        [("v1", 0), ("v3", 1), ("v4", 1)],
        45,
    ),
]
value_names_task3 = {
    "v0": "01",
    "v1": "01",
    "v2": "01",
    "v3": "012",
    "v4": "01",
}


def make_task3():
    return ScopingTask(
        domains=domains_task3,
        init=init_task3,
        goal=goal_task3,
        actions=actions_task3,
        metric=True,
        value_names=value_names_task3,
    )


def test_merging_does_not_increase_cost(scoping_task: ScopingTask):
    scoped_task_cf = scope(scoping_task, ScopingOptions(1, 0, 1, 0, 0, 0))
    scoped_task_mcf = scope(scoping_task, ScopingOptions(1, 1, 1, 0, 0, 0))
    assert scoped_task_cf == scoped_task_mcf


# %%
test_merging_does_not_increase_cost(make_task1())
# %%
test_merging_does_not_increase_cost(make_task2())
# %%
test_merging_does_not_increase_cost(make_task3())
# %%

print("All tests passed.")

# %%
