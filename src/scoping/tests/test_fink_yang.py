#!%cd ~/dev/downward/src/translate
# %%

from scoping.actions import VarValAction
from scoping.scoping import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph

# %%


def make_task(
    domains=FactSet({"C": {0, 1}, "M": {0, 1}, "B": {0, 1}}),
    init=[("C", 0), ("B", 0), ("M", 0)],
    goal=[("B", 1)],
    actions=[
        VarValAction("fill_cup", [("C", 0)], [("M", 1), ("C", 1)], 1),
        VarValAction("empty_cup", [("C", 1)], [("C", 0)], 1),
        VarValAction(
            "heat_in_microwave", [("M", 0), ("C", 1)], [("M", 1), ("B", 1)], 1
        ),
    ],
):
    return ScopingTask(domains, init, goal, actions)


# %%
scoping_task = make_task()
# %%
TaskGraph(scoping_task, ScopingOptions(0, 0, 1, 0, 0, 0))

# %%
scoped_task_f = scope(scoping_task, ScopingOptions(0, 0, 1, 0, 0, 0))
TaskGraph(scoped_task_f, ScopingOptions(0, 0, 1, 0, 0, 0))


assert scoped_task_f.domains == scoping_task.domains
assert sorted(scoped_task_f.actions, key=lambda a: a.name) == sorted(
    scoping_task.actions, key=lambda a: a.name
)
print("All tests passed.")
