#!%cd ~/dev/downward/src/translate
# %%

from scoping.actions import VarValAction
from scoping.new import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph

# %%


def make_easy_task(
    domains=FactSet({"x": {0, 1, 2}, "y": {0, 1, 2}, "z": {0, 1}}),
    init=[("x", 1), ("y", 0), ("z", 0)],
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


def make_impossible_task(
    domains=FactSet({"x": {0, 1, 2}, "y": {0, 1, 2}, "z": {0, 1}}),
    init=[("x", 1), ("y", 0), ("z", 0)],
    goal=[("x", 0)],
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
    scoping_task = make_easy_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 1, 0, 0))

    assert scoped_task.domains == FactSet({"x": {1, 2}})
    assert sorted(a.name for a in scoped_task.actions) == list("acd")


def test_rmcf_easy():
    scoping_task = make_easy_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 0))

    assert scoped_task.domains == FactSet({0: {0, 1}})
    assert scoped_task.actions == []
    assert scoped_task.init == scoped_task.goal


def test_rmcf_hard():
    scoping_task = make_impossible_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 0))

    assert scoped_task.domains == FactSet({0: {0, 1}})
    assert scoped_task.actions == []
    assert scoped_task.init != scoped_task.goal


# %%
test_f_scoping()
test_rmcf_easy()
test_rmcf_hard()

print("All tests passed.")
