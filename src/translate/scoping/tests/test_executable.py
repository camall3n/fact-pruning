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


# %%
test_gripper()
test_airport()
test_agricola()

print("All tests passed.")
