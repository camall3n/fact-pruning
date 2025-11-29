#!%cd ~/dev/downward/src/translate
# %%

from scoping.actions import VarValAction
from scoping.sas import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph

# %%


def make_task(
    domains=FactSet({"x": {0, 1, 2}, "y": {0, 1, 2}, "z": {0, 1}}),
    init=[("x", 0), ("y", 0), ("z", 0)],
    goal=[("x", 1)],
    actions=[
        VarValAction("a", [("x", 2)], [("x", 1)], 1),
        VarValAction("b", [("y", 0)], [("y", 1)], 1),
        VarValAction("c", [("y", 0)], [("x", 1)], 1),
        VarValAction("d", [], [("x", 2), ("y", 0)], 1),
        VarValAction("e", [], [("y", 0)], 1),
    ],
):
    return ScopingTask(domains, init, goal, actions)


# %%


def test_f_scoping():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 1, 0, 0))

    assert scoped_task.domains == FactSet({"x": {0, 1, 2}})
    assert sorted(a.name for a in scoped_task.actions) == list("acd")


def test_cf_scoping():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 0, 1, 0, 0))

    assert scoped_task.domains == FactSet({"x": {0, 1, 2}})
    assert sorted(a.name for a in scoped_task.actions) == list("acd")


def test_empty_action_pruning():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 1, 0, 0))

    for a in scoped_task.actions:
        assert a.effect, "Found empty action after scoping"


# %%
test_f_scoping()
test_cf_scoping()
test_empty_action_pruning()

print("All tests passed.")
