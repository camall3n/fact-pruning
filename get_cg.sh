#!/bin/bash
# $1 - domain file
# $2 - problem file

PYTHONPATH=./builds/release/bin/ ./fast-downward.py --keep-sas-file $1 $2 --search "astar(max([cg(),const(value=infinity)]))" > /dev/null

dot -Tpdf causal_graph.dot > causal_graph.pdf
