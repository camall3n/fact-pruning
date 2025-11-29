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
    domains=FactSet(
        {
            "v": {0, 1},
            "w": {0, 1},
            "x": {0, 1},
            "y": {0, 1},
            "z": {0, 1, 2},
        }
    ),
    actions=[
        VarValAction("a", [("w", 0)], [("w", 1)], 1),
        VarValAction("b", [("w", 1)], [("x", 1)], 1),
        VarValAction("c", [("x", 1), ("y", 1)], [("z", 2)], 1),
        VarValAction("d", [("w", 0)], [("x", 1)], 1),
        VarValAction("e", [("x", 1), ("y", 0)], [("z", 2)], 1),
        VarValAction("f", [("x", 0), ("y", 0)], [("z", 2)], 1),
        VarValAction("g", [], [("v", 0)], 1),
        VarValAction("h", [("v", 0)], [("y", 0)], 1),
        VarValAction("i", [("x", 0)], [("z", 1)], 1),
    ],
    init=[
        ("v", 0),
        ("w", 0),
        ("x", 0),
        ("y", 0),
        ("z", 0),
    ],
    goal=[
        ("z", 2),
    ],
):
    return ScopingTask(domains, init, goal, actions)


def test_v():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 0, 0, 0))

    assert sorted(scoped_task.domains.variables) == ["w", "x", "y", "z"]
    assert sorted(a.name for a in scoped_task.actions) == list("abcdefhi")


def test_f():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 1, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("abcdefh")


def test_m():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 1, 0, 0, 0))

    assert scoped_task.domains == scoping_task.domains
    assert sorted(a.name for a in scoped_task.actions) == list("bcdefghi")


def test_c():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 0, 0, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 1, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("abcdefhi")


def test_cf():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 0, 1, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("abcdef")


def test_mf():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 1, 1, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("bcdefh")


def test_mc():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 0, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 1, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("bcdefhi")


def test_mcf():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("bcdef")


def test_r():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 0, 1, 0))

    assert scoped_task.domains == FactSet({"w": {0, 1}, "x": {0, 1}, "z": {0, 1, 2}})
    assert sorted(a.name for a in scoped_task.actions) == list("abdefi")


def test_rmcf():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 0))
    assert scoped_task.domains == FactSet({"x": {0, 1}, "z": {0, 2}})
    assert sorted(a.name for a in scoped_task.actions) == list("def")


def test_lrmcf():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 1))

    assert scoped_task.domains == FactSet({"z": {0, 2}})
    assert sorted(a.name for a in scoped_task.actions) == list("f")


# %%
test_v()  # abcdefhi
test_f()  # abcdefh
test_cf()  # bcdefh
test_mcf()  # bcdef
# %%
test_rmcf()  # def
test_lrmcf()  # f

print("All tests passed.")


# %%
scoping_task = make_task()
TaskGraph(scoping_task, ScopingOptions(0, 0, 1, 0, 0))

# %%
scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 0, 0, 0))
TaskGraph(scoped_task, ScopingOptions(0, 0, 1, 0, 0))
