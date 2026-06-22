"""
Simulation log visualiser — matplotlib edition.
Only plots mean_faulty_reps and mean_honest_reps.
Usage: python visualise_sim_mpl.py <path_to_json_log>
"""

import sys
import json
import re
import math
from collections import Counter
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


# ── helpers ───────────────────────────────────────────────────────────────────

def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def epoch_keys(data: dict) -> list[int]:
    keys = [int(k) for k in data if k not in ("params",) and "execution" in data[k]]
    return sorted(keys)


# ── data extraction ───────────────────────────────────────────────────────────

def extract(data: dict) -> dict:
    eks = epoch_keys(data)
    n_nodes = data["params"]["N"]

    params = data["params"]
    tree1 = params["bootstrap1"][0]

    all_matches = re.findall(r'([A-Z][a-zA-Z0-9]*)<', tree1)
    nodes = all_matches[1:]
    count = dict(Counter(nodes))
    n_honest = count.pop("Node")
    idxs = [int(i) for i in re.findall(r'<(\d+)[,>]', tree1)][1:]
    n_faulty = n_nodes - n_honest
    byz_idxs = [idxs[i] for i, el in enumerate(nodes) if el != "Node"]
    print(f"byz indices: {byz_idxs}")

    mean_honest_reps = []
    mean_faulty_reps  = []
    max_faulty_reps   = []
    min_honest_reps   = []

    for k in eks:
        ep = data[str(k)]
        reps = ep.get("reputations", [math.nan] * n_nodes)

        honest_reps = [reps[i] for i in range(n_nodes) if i not in byz_idxs and i < len(reps)]
        faulty_reps  = [reps[i] for i in byz_idxs if i < len(reps)]

        mean_honest_reps.append(sum(honest_reps) / len(honest_reps) if honest_reps else math.nan)
        mean_faulty_reps.append(sum(faulty_reps)  / len(faulty_reps)  if faulty_reps  else math.nan)
        max_faulty_reps.append(max(faulty_reps)   if faulty_reps  else math.nan)
        min_honest_reps.append(min(honest_reps)   if honest_reps  else math.nan)

    return {
        "epochs":           eks,
        "n_nodes":          n_nodes,
        "n_faulty":         n_faulty,
        "byz_idxs":         byz_idxs,
        "mean_faulty_reps": mean_faulty_reps,
        "mean_honest_reps": mean_honest_reps,
        "max_faulty_reps":  max_faulty_reps,
        "min_honest_reps":  min_honest_reps,
    }


# ── figure ────────────────────────────────────────────────────────────────────

def plot_mean_reps(d: dict, filename: str) -> None:
    eks              = d["epochs"]
    mean_honest_reps = np.clip(d["mean_honest_reps"], 1e-200, None)
    mean_faulty_reps = np.clip(d["mean_faulty_reps"], 1e-200, None)
    max_faulty_reps  = np.clip(d["max_faulty_reps"], 1e-200, None)
    min_honest_reps  = np.clip(d["min_honest_reps"], 1e-200, None)

    fig, ax = plt.subplots(figsize=(3, 2))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    #ax.semilogy()
    ax.plot(eks, min_honest_reps,
            color="#86BE86", linewidth=1, linestyle=":", marker=10, markersize=4,
            label="Reputação mínima em nós corretos")
    ax.plot(eks, mean_honest_reps,
            color="#13AA13", linewidth=1, marker="+", markersize=4,
            label="Reputação média em nós corretos")
    
    ax.plot(eks, max_faulty_reps,
            color="#c99396", linewidth=1, linestyle=":", marker=11, markersize=4,
            label="Reputação máxima em nós incorretos")
    ax.plot(eks, mean_faulty_reps,
            color="#eb182a", linewidth=1, marker="x", markersize=4,
            label="Reputação média em nós incorretos")
    

    #ax.set_title(f"{filename}",
    #             color="black", fontfamily="monospace", fontsize=13)
    ax.set_xlabel("Época", color="black", fontfamily="monospace")
    ax.set_ylabel("Reputação", color="black", fontfamily="monospace")

    ax.set_ylim(bottom=1e-100, top=1)

    # ax.semilogy()
    # ax.set_yticks([1, 10**-100, 1e-200])
    # ax.yaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=4))

    ax.tick_params(colors="black", labelsize=10)
    for spine in ax.spines.values():
        spine.set_edgecolor("#aaa")

    ax.grid(color="#ddd", linestyle="--", linewidth=0.6)

    #legend = ax.legend(fontsize=10, facecolor="white", edgecolor="#aaa",
    #                   labelcolor="black", prop={"family": "monospace"})


    plt.tight_layout()
    plt.show()



def main():
    if len(sys.argv) != 2:
        print("Usage: python matplotlib_visualise_sim_mpl.py <path>")
        sys.exit(1)

    path = sys.argv[1]
    data = load(path)
    d    = extract(data)

    slash    = path.rfind("/")
    filename = path if slash == -1 else path[slash + 1:]

    print(f"Loaded {len(d['epochs'])} epochs, {d['n_nodes']} nodes.")
    plot_mean_reps(d, filename)
    print("  ✓ mean_reps")


if __name__ == "__main__":
    main()