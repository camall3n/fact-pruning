#!%cd ~/dev/downward/src/translate
# %%

from scoping.actions import VarValAction
from scoping.new import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph

# %%


def make_task(
    domains=FactSet(
        {
            "w": {0, 1},
            "x": {0, 1},
            "y": {0, 1},
            "z": {0, 1},
        }
    ),
    actions=[
        VarValAction("a", [("z", 1)], [("x", 0), ("y", 1)], 1),
        VarValAction("b", [("z", 0)], [("x", 1), ("y", 1)], 1),
        VarValAction("c", [("x", 1)], [("w", 1)], 3),
        VarValAction("d", [("x", 0), ("y", 1)], [("w", 1)], 1),
        VarValAction("e", [("w", 0), ("z", 0)], [("z", 1)], 1),
    ],
    init=[
        ("w", 0),
        ("x", 0),
        ("y", 0),
        ("z", 0),
    ],
    goal=[
        ("w", 1),
        ("y", 1),
    ],
):
    return ScopingTask(domains, init, goal, actions)


def test_lrmcf():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 1))

    assert scoped_task.domains == scoping_task.domains
    assert sorted(a.name for a in scoped_task.actions) == list("abcde")


# %%
test_lrmcf()  # abcde

print("All tests passed.")


# %%
scoping_task = make_task()
TaskGraph(scoping_task, ScopingOptions(0, 0, 1, 0, 0))

# %%
scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 0, 0, 0))
# %%
TaskGraph(scoping_task, ScopingOptions(1, 1, 1, 0, 0))

TaskGraph(scoped_task, ScopingOptions(0, 0, 1, 0, 0))
