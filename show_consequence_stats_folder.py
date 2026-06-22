"""
Usage:
    python show_consequence_stats_folder.py <json_folder> <total> <group1_index> [<group1_index> ...]

Arguments:
    json_folder     Path to a folder containing JSON files with action counts per index.
                    The last 50 files in lexicographic order are loaded and their counts
                    are summed across files.
    total           Total number of readings per file (integer). Multiplied by the number
                    of files loaded to obtain the effective total used for rate computation.
    group1_index    One or more indices that form Group 1.
                    All remaining indices in the JSON are assigned to Group 2.

Output:
    - One figure per action showing count per index.
    - One figure with the mean count (normalised by total) per action for each group.
"""

import json
import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_data_from_folder(folder: str, n: int = 50) -> tuple[dict, int]:
    """
    Load the last *n* JSON files (lexicographic order) from *folder* and
    return (merged_data, files_loaded).

    Counts are summed across files; use (total * files_loaded) as the
    effective total when computing rates.
    """
    import os
    paths = sorted(
        os.path.join(folder, f)
        for f in os.listdir(folder)
    )
    selected = paths[-n:]
    if not selected:
        print(f"No JSON files found in '{folder}'.")
        sys.exit(1)


    unmerged: dict[str, dict[int, dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    merged: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for i, path in enumerate(selected):
        with open(path, "r", encoding="utf-8") as fh:
            file_data: dict = json.load(fh)
        for idx, counts in file_data.items():
            for action, count in counts.items():
                merged[idx][action] += count
                unmerged[idx][i][action] += count

    return {idx: dict(counts) for idx, counts in merged.items()}, unmerged, len(selected)


def collect_actions(data: dict) -> list[str]:
    """Return a sorted list of all action keys present across all indices."""
    actions = set()
    for counts in data.values():
        actions.update(counts.keys())
    return sorted(actions)


def per_index_counts(data: dict, action: str) -> tuple[list[str], list[int]]:
    """Return (indices, counts) for a given action, sorted by index."""
    indices = sorted(data.keys())
    counts = [data[idx].get(action, 0) for idx in indices]
    return indices, counts


def group_mean(data: dict, indices: list[str], total: int) -> dict[str, float]:
    """Mean count (as fraction of total) per action for the given indices."""
    if not indices:
        return {}
    actions = collect_actions(data)
    means = {}
    for action in actions:
        raw = [data[idx].get(action, 0) for idx in indices if idx in data]
        means[action] = np.mean(raw) / total if total > 0 else 0.0
    return means


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_per_action(data: dict, actions: list[str], group1: list[str], total) -> None:
    """One figure per action: bar chart of counts per index."""
    group1_set = set(group1)
    all_indices = sorted(data.keys())
    colours = ["tab:red" if idx in group1_set else "tab:blue" for idx in all_indices]

    for action in actions:
        rates = [data[idx].get(action, 0) / total for idx in all_indices]

        fig, ax = plt.subplots(figsize=(max(6, len(all_indices) * 0.5), 5))
        bars = ax.bar(all_indices, rates, color=colours, edgecolor="white", linewidth=0.5)

        ax.set_title(f"Action '{action}' — rate per index (count / total)")
        ax.set_xlabel("Index")
        ax.set_ylabel("Rate (count / total)")
        ax.tick_params(axis="x", rotation=45)

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="tab:red", label="Faulty"),
            Patch(facecolor="tab:blue", label="Correct"),
        ]
        ax.legend(handles=legend_elements)

        fig.tight_layout()
        plt.show()


def plot_group_means(data: dict, total: int, group1: list[str]) -> None:
    """One figure: mean count per action for each group."""
    all_indices = sorted(data.keys())
    group1_set = set(group1)
    group2 = [idx for idx in all_indices if idx not in group1_set]

    actions = collect_actions(data)
    means1 = group_mean(data, group1, total)
    means2 = group_mean(data, group2, total)

    x = np.arange(len(actions))
    width = 0.45

    fig, ax = plt.subplots(figsize=(max(6, len(actions) * 1.0), 5))
    vals1 = [means1.get(a, 0) for a in actions]
    vals2 = [means2.get(a, 0) for a in actions]
    bars1 = ax.bar(x - width / 2, vals1, width, label="Faulty", color="tab:red", edgecolor="white")
    bars2 = ax.bar(x + width / 2, vals2, width, label="Correct", color="tab:blue", edgecolor="white")

    for bar, val in [*zip(bars1, vals1), *zip(bars2, vals2)]:
        ax.annotate(
            f"{val:.6f}",
            xy=(bar.get_x() + bar.get_width() / 2, val),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=7,
        )

    ax.set_title("Mean action rate per group (count / total readings)")
    ax.set_xlabel("Action")
    ax.set_ylabel("Mean rate")
    ax.set_xticks(x)
    ax.set_xticklabels(actions)
    ax.legend()

    fig.tight_layout()
    plt.show()


#######

def calc_worst_case(unmerged_data: dict, group1: list):
    group1_set = set(group1)
    all_indices = sorted(unmerged_data.keys())
    worst_case = 0 # the penalty the least lucky correct node supports
    string = "ERROR"
    all_penalties = {}
    for idx in all_indices:
        if idx in group1:
                continue # byz
        for attempt in unmerged_data[idx]:
            reward = 1.01
            P_reward = unmerged_data[idx][attempt].get("a",0)
            gama = unmerged_data[idx][attempt].get("g",0)
            delta = unmerged_data[idx][attempt].get("d0",0) + unmerged_data[idx][attempt].get("d1",0)
            P_penalty = gama + delta
            penalty = np.exp(-P_reward*np.log(reward)/P_penalty)

            all_penalties[idx] = penalty

            if penalty > worst_case:
                worst_case = penalty
                string = f"Correct node {idx} is worst case supporting penalty {penalty} vs reward {reward} at rate {P_penalty}/{P_reward}, {P_penalty} = {gama} + {delta}"

    # for x, y in all_penalties.items():
    #     print(x, "-", y)
    
    mean = 0
    for x in all_penalties.values():
        mean += x
    mean = mean/len(all_penalties.values())
    print("Mean penalty floor =", mean)
    print(string)

    worst_case = 1 # the penalty the luckiest faulty node supports
    string = "ERROR"
    all_penalties = {}

    for idx in all_indices:
        if not idx in group1:
                continue # byz
        for attempt in unmerged_data[idx]:
            reward = 1.01
            P_reward = unmerged_data[idx][attempt].get("a",0)
            gama = unmerged_data[idx][attempt].get("g",0)
            delta = unmerged_data[idx][attempt].get("d0",0) + unmerged_data[idx][attempt].get("d1",0)
            P_penalty = gama + delta
            penalty = np.exp(-P_reward*np.log(reward)/P_penalty)

            all_penalties[idx] = penalty

            if penalty < worst_case:
                worst_case = penalty
                string = f"Faulty node {idx} is worst case supporting penalty {penalty} vs reward {reward} at rate {P_penalty}/{P_reward}, {P_penalty} = {gama} + {delta}"
    
    mean = 0
    for x in all_penalties.values():
        mean += x
    mean = mean/len(all_penalties.values())
    print("Mean penalty floor =", mean)
    print(string)

def calc_worst_case_merged(data: dict, group1: list, total: int):
    group1_set = set(group1)
    all_indices = sorted(data.keys())
    worst_case = 0 # the penalty the least lucky correct node supports
    string = "ERROR"
    all_penalties = {}
    for idx in all_indices:
        if idx in group1:
                continue # byz
        reward = 1.01
        P_reward = data[idx].get("a",0)
        gama = data[idx].get("g",0)
        delta = data[idx].get("d0",0) + data[idx].get("d1",0)
        P_penalty = gama + delta
        penalty = np.exp(-P_reward*np.log(reward)/P_penalty)

        all_penalties[idx] = penalty

        if penalty > worst_case:
            worst_case = penalty
            string = f"Correct node {idx} is worst case supporting penalty {penalty} vs reward {reward} at rate {P_penalty}/{P_reward}, {P_penalty} = {gama} + {delta}, a={P_reward/total*100:0.2f} g={gama/total*100:0.2f} d={delta/total*100:0.2f}"

    # for x, y in all_penalties.items():
    #     print(x, "-", y)
    
    mean = 0
    for x in all_penalties.values():
        mean += x
    mean = mean/len(all_penalties.values())
    print("Mean penalty floor =", mean)
    print(string)

    worst_case = 1 # the penalty the luckiest faulty node supports
    string = "ERROR"
    all_penalties = {}

    for idx in all_indices:
        if not idx in group1:
                continue # byz
        reward = 1.01
        P_reward = data[idx].get("a",0)
        gama = data[idx].get("g",0)
        delta = data[idx].get("d0",0) + data[idx].get("d1",0)
        P_penalty = gama + delta
        penalty = np.exp(-P_reward*np.log(reward)/P_penalty)

        all_penalties[idx] = penalty

        if penalty < worst_case:
            worst_case = penalty
            string = f"Faulty node {idx} is worst case supporting penalty {penalty} vs reward {reward} at rate {P_penalty}/{P_reward}, {P_penalty} = {gama} + {delta}, a={P_reward/total*100:0.2f} g={gama/total*100:0.2f} d={delta/total*100:0.2f}"
    
    mean = 0
    for x in all_penalties.values():
        mean += x
    mean = mean/len(all_penalties.values())
    print("Mean penalty floor =", mean)
    print(string)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    json_folder = sys.argv[1]
    total_per_file = int(sys.argv[2])
    group1 = sys.argv[3:]  # remaining args are Group 1 indices

    data, unmerged_data, files_loaded = load_data_from_folder(json_folder)
    total = total_per_file * files_loaded
    print(f"Loaded {files_loaded} file(s) from '{json_folder}'. Effective total = {total}.")

    actions = collect_actions(data)

    # Validate group1 indices
    unknown = [idx for idx in group1 if idx not in data]
    if unknown:
        print(f"Warning: the following indices were not found in the JSON: {unknown}")
    
    #print("worst case unmerged")
    #calc_worst_case(unmerged_data,group1)
    #print()
    print("worst case merged")
    calc_worst_case_merged(data,group1,total)

    #plot_per_action(data, actions, group1, total)
    plot_group_means(data, total, group1)


if __name__ == "__main__":
    main()