#!%cd ~/dev/downward/src/translate
# %%
from scoping.actions import VarValAction
from scoping.core import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph


def make_task(
    domains=FactSet(
        {
            "v0": {0, 1},
            "v1": {0, 1},
            "v2": {0, 1},
            "v3": {0, 1, 2},
            "v4": {0, 1},
        }
    ),
    init=[("v0", 0), ("v1", 1), ("v2", 1), ("v3", 2), ("v4", 1)],
    goal=[("v2", 0), ("v3", 2), ("v4", 1)],
    actions=[
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
    ],
    value_names={
        "v0": "01",
        "v1": "01",
        "v2": "01",
        "v3": "012",
        "v4": "01",
    },
):
    return ScopingTask(
        domains, init, goal, actions, metric=True, value_names=value_names
    )


def test_merging_does_not_increase_cost():
    # Initial task
    scoping_task = make_task()
    # sas_task = scoping_task.to_sas()
    # with open("simple.sas", "w") as output_file:
    #     sas_task.output(output_file)
    # TaskGraph(scoping_task, ScopingOptions(0, 0, 1, 0, 0, 0))

    # Scoping CF
    scoped_task_cf = scope(scoping_task, ScopingOptions(1, 0, 1, 0, 0, 0))
    # print(len(scoped_task_cf.actions))
    # TaskGraph(scoped_task_cf, ScopingOptions(1, 1, 1, 0, 0))

    #
    # scoped_sas = scoped_task_cf.to_sas()
    # with open("simple-cf.sas", "w") as output_file:
    #     scoped_sas.output(output_file)

    # Scoping MCF
    scoped_task_mcf = scope(scoping_task, ScopingOptions(1, 1, 1, 0, 0, 0))
    # print(len(scoped_task.actions))
    # TaskGraph(scoped_task, ScopingOptions(1, 1, 1, 0, 0))

    #
    # scoped_task.dump()
    # scoped_sas = scoped_task.to_sas()
    # with open("simple-mcf.sas", "w") as output_file:
    #     scoped_sas.output(output_file)

    assert scoped_task_cf == scoped_task_mcf


test_merging_does_not_increase_cost()

print("All tests passed.")
