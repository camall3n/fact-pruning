#!%cd ~/dev/downward/src/translate
# %%

from scoping.actions import VarValAction
from scoping.scoping import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph


def make_task(n: int):
    if n == 3:
        return ScopingTask(
            domains=FactSet({"x": {0, 1}, "y": {0, 1, 2, 3}, "z": {0, 1, 2, 3}}),
            init=[("x", 0), ("y", 0), ("z", 0)],
            goal=[("x", 0), ("z", 2)],
            actions=[
                VarValAction("a", [], [("z", 2)], 1),
                VarValAction("b", [], [("y", 0), ("z", 1)], 1),
                VarValAction("c", [("z", 1)], [("x", 0), ("z", 2)], 1),
                VarValAction("d", [("y", 1)], [("y", 2), ("z", 1)], 1),
                VarValAction("e", [("y", 2)], [("y", 0), ("z", 2)], 1),
                VarValAction("f", [], [("y", 1)], 1),
                VarValAction("g", [], [("z", 3)], 1),
                VarValAction("h", [], [("x", 1)], 1),
                VarValAction("i", [("x", 1), ("z", 3)], [("x", 0), ("y", 3)], 1),
                VarValAction("j", [("y", 3)], [("z", 0)], 1),
            ],
        )
    else:
        raise RuntimeError


# %%
# TaskGraph(make_task(1), ScopingOptions(0, 0, 1, 0, 0))
# TaskGraph(make_task(2), ScopingOptions(0, 0, 1, 0, 0))
TaskGraph(make_task(3), ScopingOptions(0, 0, 1, 0, 0))
# TaskGraph(make_task(4), ScopingOptions(0, 0, 1, 0, 0))
# TaskGraph(make_task(5), ScopingOptions(0, 0, 1, 0, 0))

# %%

TaskGraph(make_task(3), ScopingOptions(0, 0, 1, 0, 0))


# %%
def get_actions(task, options):
    scoped_task = scope(task, options)
    return "".join(sorted([a.name for a in scoped_task.actions]))


scoping_task = make_task(3)

assert get_actions(scoping_task, ScopingOptions(0, 0, 0, 0, 0)) == "abcdefghij"
assert get_actions(scoping_task, ScopingOptions(0, 0, 1, 0, 0)) == "abcdefghi"
assert get_actions(scoping_task, ScopingOptions(1, 0, 1, 0, 0)) == "abcdef"
assert get_actions(scoping_task, ScopingOptions(1, 1, 1, 0, 0)) == "abcde"
assert get_actions(scoping_task, ScopingOptions(1, 1, 1, 1, 0)) == "abc"
assert get_actions(scoping_task, ScopingOptions(1, 1, 1, 1, 1)) == "a"

print("All tests passed.")
