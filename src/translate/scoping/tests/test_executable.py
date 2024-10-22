#!%cd ~/dev/downward/src/translate
#
from scoping.core import scope_sas
from scoping.options import ScopingOptions


scoping_options = ScopingOptions(0, 0, 0, 0, 0, write_output_file=False)


def test_gripper():
    sas_path = "../../benchmarks/basic/gripper/prob01.sas"
    scope_sas(sas_path, scoping_options)


def test_airport():
    sas_path = "../../benchmarks/basic/airport/p01-airport1-p1.sas"
    scope_sas(sas_path, scoping_options)


def test_agricola():
    sas_path = "../../benchmarks/basic/agricola-opt18-strips/p01.sas"
    scope_sas(sas_path, scoping_options)


def test_dummy_unsolvable():
    sas_path = "../../benchmarks/basic/mystery/prob07.sas"
    scope_sas(sas_path, scoping_options)


def test_parcprinter():
    sas_path = "../../benchmarks/basic/parcprinter-08-strips/p01.sas"
    scope_sas(sas_path, scoping_options=ScopingOptions(0, 0, 1, 0, 0))


# %%
test_gripper()
test_airport()
test_agricola()
# test_dummy_unsolvable()
# %%
test_parcprinter()

print("All tests passed.")
