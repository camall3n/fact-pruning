#!%cd ~/dev/downward/src/translate
#
import argparse
import os

import sas_tasks as fd
from scoping.scoping import scope
from scoping.options import ScopingOptions
from scoping.sas_parser import SasParser
from scoping.task import ScopingTask
from translate import simplify
from translate import timers


def compute_sas_reachability(scoped_sas: fd.SASTask):
    try:
        simplify.filter_unreachable_propositions(scoped_sas, quiet=True)
    except simplify.Impossible:
        scoped_sas = ScopingTask.trivial(solvable=False).to_sas()
    except simplify.TriviallySolvable:
        scoped_sas = ScopingTask.trivial(solvable=True).to_sas()
    return scoped_sas


def scope_sas_task(sas_task: fd.SASTask, scoping_options: ScopingOptions) -> fd.SASTask:
    scoping_task = ScopingTask.from_sas(sas_task)
    scoped_task = scope(scoping_task, scoping_options)
    scoped_sas = scoped_task.to_sas()
    scoped_sas._sort_all()
    return scoped_sas


def scope_sas_file(
    sas_path: str,
    scoping_options: ScopingOptions,
):
    parser = SasParser(pth=sas_path)
    parser.parse()
    sas_task: fd.SASTask = parser.to_fd()
    scoped_sas = scope_sas_task(sas_task, scoping_options)

    if scoping_options.write_output_file:
        filepath, ext = os.path.splitext(sas_path)
        output_filename = filepath + "_scoped" + ext
        with timers.timing("Writing output"):
            with open(output_filename, "w") as f:
                scoped_sas.output(f)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("sas_file", help="path to sas file")
    parser.add_argument(
        "--disable-merging", dest="enable_merging", action="store_false"
    )
    parser.add_argument(
        "--disable-causal-links", dest="enable_causal_links", action="store_false"
    )
    parser.add_argument(
        "--variables-only", dest="enable_fact_based", action="store_false"
    )
    parser.add_argument(
        "--disable-forward-pass", dest="enable_forward_pass", action="store_false"
    )
    parser.add_argument("--disable-loop", dest="enable_loop", action="store_false")
    return parser.parse_args()


def main():
    args = parse_args()
    scoping_options = ScopingOptions(
        enable_causal_links=args.enable_causal_links,
        enable_merging=args.enable_merging,
        enable_fact_based=args.enable_fact_based,
        enable_forward_pass=args.enable_forward_pass,
        enable_loop=args.enable_loop,
    )
    scope_sas_file(args.sas_file, scoping_options)


if __name__ == "__main__":
    main()
