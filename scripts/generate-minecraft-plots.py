# %% Imports and setup
from collections import defaultdict
from pathlib import Path
import json
import re

import matplotlib.pyplot as plt
import numpy as np

# Path to your experiment's eval directory
EVAL_DIR = Path("experiments/scoping/data/scoping-scoping-minecraft-12-09-2025-eval")

REVISIONS = ["scoping-experiments"]

# Publication-quality settings
MARKER_SIZE = 100
MARKER_LINEWIDTH = 2
LINE_WIDTH = 3

base_font_size = 20

plt.rcParams.update(
    {
        "font.size": base_font_size,
        "axes.titlesize": base_font_size + 4,
        "axes.labelsize": base_font_size + 2,
        "legend.title_fontsize": base_font_size,
        "axes.linewidth": 2,
        "xtick.major.width": 2,
        "ytick.major.width": 2,
        "xtick.minor.width": 1,
        "ytick.minor.width": 1,
        "xtick.major.size": 12,
        "ytick.major.size": 12,
        "xtick.minor.size": 6,
        "ytick.minor.size": 6,
        "xtick.labelsize": base_font_size,
        "ytick.labelsize": base_font_size,
        "legend.fontsize": base_font_size,
    }
)


# %% Load data
def load_properties(eval_dir):
    with open(eval_dir / "properties") as f:
        return json.load(f)


def rename_algorithm(name):
    paper_names = {f"{REVISIONS[0]}-basic": "No scoping", f"{REVISIONS[0]}-fd": "FD"}
    for a in ["V", "F", "FC", "FCM", "FCMR", "FCMRL"]:
        paper_names[f"{REVISIONS[0]}-{a}"] = a
    return paper_names.get(name, name)


def format_domain_name(domain):
    """Extract size number from domain for legend label."""
    match = re.search(r"/(\d+)$", domain)
    if match:
        return int(match.group(1))
    return domain


def extract_pairs(data, attribute, alg1, alg2):
    """Extract (alg1_value, alg2_value, domain) tuples for each task."""
    tasks = defaultdict(dict)
    for run_id, run in data.items():
        if not isinstance(run, dict):
            continue
        algo = rename_algorithm(run.get("algorithm", ""))
        if algo not in [alg1, alg2]:
            continue
        domain = run.get("domain")
        problem = run.get("problem")
        task = (domain, problem)
        value = run.get(attribute)
        if value is not None:
            tasks[task][algo] = value
            tasks[task]["domain"] = domain

    pairs = []
    for task, values in tasks.items():
        if alg1 in values and alg2 in values:
            if values[alg1] != values[alg2]:
                pairs.append((values[alg1], values[alg2], values["domain"]))
    return pairs


def count_wins(pairs, alg1, alg2):
    """Count tasks where each algorithm has lower value."""
    alg1_wins = sum(1 for x, y, _ in pairs if x < y)
    alg2_wins = sum(1 for x, y, _ in pairs if y < x)
    return alg1_wins, alg2_wins


def plot_scatter(pairs, title, alg1, alg2, outfile, max_limit=None):
    """Create scatter plot with equal axes."""
    fig, ax = plt.subplots(figsize=(8, 8))

    # Group by domain for coloring
    domains = sorted(set(format_domain_name(p[2]) for p in pairs))
    colors = plt.cm.tab10(np.linspace(0, 1, len(domains)))
    domain_colors = dict(zip(domains, colors))
    markers = ["x", "+", "o", "s", "^", "v", "<", ">", "D", "p"]
    domain_markers = {d: markers[i % len(markers)] for i, d in enumerate(domains)}

    for domain in domains:
        domain_pairs = [(x, y) for x, y, d in pairs if format_domain_name(d) == domain]
        xs, ys = zip(*domain_pairs) if domain_pairs else ([], [])
        ax.scatter(
            xs,
            ys,
            c=[domain_colors[domain]],
            marker=domain_markers[domain],
            label=domain,
            s=MARKER_SIZE,
            linewidths=MARKER_LINEWIDTH,
        )

    # Set equal log scale limits
    all_values = [p[0] for p in pairs] + [p[1] for p in pairs]
    min_val = min(all_values) * 0.8
    max_val = max_limit if max_limit is not None else max(all_values) * 1.2

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)

    # Diagonal line
    ax.plot([min_val, max_val], [min_val, max_val], "k-", alpha=1.0, lw=LINE_WIDTH)

    # Count wins for axis labels
    alg1_wins, alg2_wins = count_wins(pairs, alg1, alg2)
    ax.set_xlabel(f"{alg1} (lower for {alg1_wins} tasks)")
    ax.set_ylabel(f"{alg2} (lower for {alg2_wins} tasks)")
    ax.set_title(title)
    ax.legend(loc="upper left", title=r"Size")
    ax.set_aspect("equal")

    plt.tight_layout()
    plt.savefig(outfile, dpi=300, bbox_inches="tight")
    plt.show()


# %% Load data
data = load_properties(EVAL_DIR)


# %% Generate operators scatter plot
pairs = extract_pairs(data, "translator_operators", "FD", "FCM")
plot_scatter(
    pairs, "Actions", "FD", "FCM", "minecraft-actions-improvement.png", max_limit=1e5
)


# %% Generate facts scatter plot
# pairs = extract_pairs(data, "translator_facts", "FD", "FCM")
# plot_scatter(pairs, "Facts", "FD", "FCM", "scatterplot-facts-custom.png", max_limit=1e3)
