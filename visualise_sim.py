"""
Simulation log visualiser.
Usage: python visualise_sim.py <path_to_json_log>
"""

import sys
import json
import re
import math
from collections import Counter

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ── helpers ──────────────────────────────────────────────────────────────────

def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def epoch_keys(data: dict) -> list[int]:
    keys = [int(k) for k in data if k not in ("params",) and "execution" in data[k]]
    return sorted(keys)


def inner_classes(tree: str) -> Counter:
    all_names = re.findall(r'([A-Z][a-zA-Z0-9]*)<', tree)
    inner = all_names[1:]
    return Counter(inner)


def config_summary(cfg: dict, base_reputations, byz_idxs, num_inner_nodes) -> dict:
    """Extract per-config features."""
    # how many byzantines in the inner nodes of the config (real/perceived)
    tree = cfg["tree"]
    node_idxs = [int(i) for i in re.findall(r'<([a-zA-Z0-9]*)>', tree)]
    inner_idxs = node_idxs[:num_inner_nodes]
    real_byz_ratio = 0
    perceived_byz_ratio = 0
    for idx in inner_idxs:
        if idx in byz_idxs:
            real_byz_ratio += 1
        if base_reputations[idx] < 0.5:
            perceived_byz_ratio += 1
    real_byz_ratio = real_byz_ratio/num_inner_nodes
    perceived_byz_ratio = perceived_byz_ratio/num_inner_nodes

    votes = cfg.get("instance_votes", [])
    n_rounds = len(votes)
    # avg vote time across all votes in all rounds
    times = [v["time"] for rnd in votes for v in rnd]
    avg_time = sum(times) / len(times) if times else None
    classes = inner_classes(cfg.get("tree", ""))
    return {
        "suspected": cfg.get("suspected", False),
        "n_rounds": n_rounds,
        "avg_vote_time": avg_time,
        "node_classes": classes,
        "real_byzantine_ratio": real_byz_ratio,
        "perceived_byzantine_ratio": perceived_byz_ratio,
        "byzantine_leader": node_idxs[0] in byz_idxs
    }


# ── data extraction ───────────────────────────────────────────────────────────

def extract(data: dict) -> dict:
    """
    Returns:
      epochs          : sorted int list
      score_keys      : list of epoch-score alternative names
      epoch_scores    : {score_key: [value per epoch]}   (None → NaN)
      reputations     : [[rep per node] per epoch]
      config_data     : [[config_summary] per epoch]
      n_nodes         : int
    """
    eks = epoch_keys(data)
    n_nodes = data["params"]["N"]

    # byzantines
    params = data["params"]
    tree1 = params["bootstrap1"][0]

    all_matches = re.findall(r'([A-Z][a-zA-Z0-9]*)<', tree1)
    nodes = all_matches[1:]  # skip the Tree class
    count = dict(Counter(nodes))
    n_honest = count.pop("Node")
    idxs = [int(i) for i in re.findall(r'<([a-zA-Z0-9]*)>', tree1)]
    n_faulty = n_nodes - n_honest
    byz_idxs = []
    for i,el in enumerate(nodes):
        if el != "Node":
            byz_idxs.append(idxs[i])

    fanout = data["params"]["fanout"]
    n_inner_nodes = (n_nodes - 1 + fanout - 1) // fanout

    # discover score alternatives from first non-null scores epoch
    score_keys = []
    for k in eks:
        s = data[str(k)].get("scores")
        if s:
            score_keys = list(s.keys())
            break

    epoch_scores = {sk: [] for sk in score_keys}
    reputations = []
    config_data = []
    mean_honest_reps = []
    mean_faulty_reps = []
    real_byzantines_in_inner_nodes = []
    perceived_byzantines_in_inner_nodes = []

    for k in eks:
        ep = data[str(k)]
        s = ep.get("scores") or {}
        for sk in score_keys:
            v = s.get(sk)
            epoch_scores[sk].append(v if v is not None else math.nan)

        reps = ep.get("reputations", [math.nan] * n_nodes)
        reputations.append(reps)

        # get reputations by node behaviour
        honest_reps = [reps[i] for i in range(n_nodes) if i not in byz_idxs and i < len(reps)]
        faulty_reps  = [reps[i] for i in byz_idxs if i < len(reps)]

        mean_honest_reps.append( sum(honest_reps) / len(honest_reps) if honest_reps else math.nan )
        mean_faulty_reps.append( sum(faulty_reps) / len(faulty_reps) if faulty_reps else math.nan )

        exec_block = ep.get("execution", {})
        base_reputations = data[str(int(k)-2)]["reputations"] if int(k)-2 >= 0 else [0.66]*n_nodes
        cfgs = [
            config_summary(exec_block[ck], base_reputations, byz_idxs, n_inner_nodes)
            for ck in exec_block
            if ck != "size"
        ]
        config_data.append(cfgs)
        real_byzantines_in_inner_nodes.append(
            sum(c["real_byzantine_ratio"] for c in cfgs) / len(cfgs) if cfgs else math.nan
        )
        perceived_byzantines_in_inner_nodes.append(
            sum(c["perceived_byzantine_ratio"] for c in cfgs) / len(cfgs) if cfgs else math.nan
        )

    return {
        "epochs": eks,
        "score_keys": score_keys,
        "epoch_scores": epoch_scores,
        "reputations": reputations,
        "config_data": config_data,
        "n_nodes": n_nodes,
        "n_faulty": n_faulty,
        "byz_idxs": byz_idxs,
        "mean_faulty_reps": mean_faulty_reps,
        "mean_honest_reps": mean_honest_reps,
        "real_byzantine_ratio": real_byzantines_in_inner_nodes,
        "perceived_byzantine_ratio": perceived_byzantines_in_inner_nodes
    }


# ── colour palette ────────────────────────────────────────────────────────────

SCORE_COLOURS = [
    "#eb182a", "#2a9d8f", "#e9c46a", "#457b9d",
    "#f4a261", "#8ecae6", "#a8dadc", "#6d6875", "#7209b7", "#13AA13", "#B60155", "#FF98DD"
]
NODE_COLOURS = [
    "#4cc9f0", "#f72585", "#7209b7", "#3a0ca3",
    "#4361ee", "#4cc9f0", "#560bad",
]


# ── figure builders ───────────────────────────────────────────────────────────

def fig_epoch_scores(d: dict) -> go.Figure:
    """Line chart of all epoch-score alternatives over time."""
    fig = go.Figure()

    eks = d["epochs"]
    n_suspected = [
        sum(1 for c in cfgs if c["suspected"])
        for cfgs in d["config_data"]
    ]
    fig.add_trace(go.Bar(
        x=eks, y=n_suspected,
        marker_color="#3b3b3b",
        name="Suspected configs",
    ))
    n_byz_leaders = [
        sum(1 for c in cfgs if c["byzantine_leader"])
        for cfgs in d["config_data"]
    ]
    fig.add_trace(go.Bar(
        x=eks, y=n_byz_leaders,
        marker_color="#3e3f00",
        name="Byzantine leaders",
    ))

    j = 0
    for i, sk in enumerate(d["score_keys"]):
        j = i
        vals = d["epoch_scores"][sk]
        fig.add_trace(go.Scatter(
            x=eks, y=vals,
            mode="lines+markers",
            name=sk,
            line=dict(color=SCORE_COLOURS[i % len(SCORE_COLOURS)], width=2),
            marker=dict(size=5),
            connectgaps=False,
        ))
    
    j+=1
    vals = d["real_byzantine_ratio"]
    fig.add_trace(go.Scatter(
        x=eks, y=vals,
        mode="lines+markers",
        name="real_byzantine_ratio",
        line=dict(color=SCORE_COLOURS[j % len(SCORE_COLOURS)], width=2),
        marker=dict(size=5),
        connectgaps=False,
    ))
    j+=1
    vals = d["perceived_byzantine_ratio"]
    fig.add_trace(go.Scatter(
        x=eks, y=vals,
        mode="lines+markers",
        name="perceived_byzantine_ratio",
        line=dict(color=SCORE_COLOURS[j % len(SCORE_COLOURS)], width=2),
        marker=dict(size=5),
        connectgaps=False,
    ))

    fig.update_layout(
        title="Epoch Score Alternatives Over Time",
        xaxis_title="Epoch",
        yaxis_title="Score",
        legend_title="Formula",
        hovermode="x unified",
    )
    return fig


# def fig_reputation_heatmap(d: dict) -> go.Figure:
#     """Heatmap: node reputations across epochs."""
#     n_nodes = d["n_nodes"]
#     z = [[row[n] if n < len(row) else math.nan for n in range(n_nodes)]
#          for row in d["reputations"]]
#     fig = go.Figure(go.Heatmap(
#         z=[[row[n] for n in range(n_nodes)] for row in z],
#         x=[f"Node {n}" for n in range(n_nodes)],
#         y=d["epochs"],
#         colorscale="Viridis",
#         colorbar=dict(title="Reputation"),
#     ))
#     fig.update_layout(
#         title="Node Reputations (Scores) per Epoch",
#         xaxis_title="Node",
#         yaxis_title="Epoch",
#         yaxis=dict(autorange="reversed"),
#     )
#     return fig


# def fig_epoch_detail(d: dict, epoch_idx: int) -> go.Figure:
#     """
#     For a single epoch: bar chart of node reputations + per-config info.
#     epoch_idx is the position in d["epochs"], not the epoch number.
#     """
#     ep_num = d["epochs"][epoch_idx]
#     reps = d["reputations"][epoch_idx]
#     cfgs = d["config_data"][epoch_idx]
#     n_nodes = d["n_nodes"]

#     fig = make_subplots(
#         rows=2, cols=1,
#         subplot_titles=(
#             f"Epoch {ep_num} — Node Reputations",
#             f"Epoch {ep_num} — Config Stats",
#         ),
#         vertical_spacing=0.15,
#     )

#     # node reputations bar
#     fig.add_trace(go.Bar(
#         x=[f"Node {i}" for i in range(n_nodes)],
#         y=reps,
#         marker_color=NODE_COLOURS[:n_nodes],
#         name="Reputation",
#     ), row=1, col=1)

#     # per-config: avg vote time + n_rounds
#     cfg_labels = [f"Config {i}" for i in range(len(cfgs))]
#     avg_times = [c["avg_vote_time"] or 0 for c in cfgs]
#     n_rounds = [c["n_rounds"] for c in cfgs]

#     fig.add_trace(go.Bar(
#         x=cfg_labels, y=avg_times,
#         name="Avg Vote Time",
#         marker_color="#e63946",
#     ), row=2, col=1)
#     fig.add_trace(go.Bar(
#         x=cfg_labels, y=n_rounds,
#         name="# Rounds",
#         marker_color="#457b9d",
#     ), row=2, col=1)

#     fig.update_layout(
#         title=f"Epoch {ep_num} Detail",
#         barmode="group",
#         showlegend=True,
#     )
#     fig.update_yaxes(title_text="Reputation", row=1, col=1)
#     fig.update_yaxes(title_text="Value", row=2, col=1)

#     return fig


def fig_scores_vs_reputations(d: dict) -> go.Figure:
    """
    Scatter: for each epoch, plot each score alternative vs
    mean node reputation, coloured by epoch.
    """
    eks = d["epochs"]
    mean_reps = [
        sum(r for r in row if not math.isnan(r)) / max(1, sum(1 for r in row if not math.isnan(r)))
        for row in d["reputations"]
    ]

    fig = go.Figure()
    for i, sk in enumerate(d["score_keys"]):
        vals = d["epoch_scores"][sk]
        valid = [(eks[j], vals[j], mean_reps[j]) for j in range(len(eks))
                 if not isinstance(vals[j], str) and not math.isnan(vals[j])]
        if not valid:
            continue
        xs, ys, zs = zip(*valid)
        fig.add_trace(go.Scatter(
            x=zs, y=ys,
            mode="markers",
            name=sk,
            marker=dict(
                color=list(xs),
                colorscale="Plasma",
                size=8,
                colorbar=dict(title="Epoch") if i == 0 else None,
                showscale=(i == 0),
            ),
            text=[f"Epoch {e}" for e in xs],
            hovertemplate="%{text}<br>mean rep=%{x:.3f}<br>score=%{y:.3f}",
        ))
    fig.update_layout(
        title="Epoch Score vs Mean Node Reputation",
        xaxis_title="Mean Node Reputation",
        yaxis_title="Epoch Score",
        legend_title="Formula",
    )
    return fig


def fig_suspected_configs(d: dict) -> go.Figure:
    """Bar chart: number of suspected configs per epoch."""
    eks = d["epochs"]
    n_suspected = [
        sum(1 for c in cfgs if c["suspected"])
        for cfgs in d["config_data"]
    ]
    fig = go.Figure(go.Bar(
        x=eks, y=n_suspected,
        marker_color="#f4a261",
        name="Suspected configs",
    ))
    fig.update_layout(
        title="Suspected Configurations per Epoch",
        xaxis_title="Epoch",
        yaxis_title="Count",
    )
    return fig


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2:
        print("Usage: python visualise_sim.py <path>")
        sys.exit(1)

    path = sys.argv[1]
    data = load(path)
    d = extract(data)

    print(f"Loaded {len(d['epochs'])} epochs, {d['n_nodes']} nodes, "
          f"{len(d['score_keys'])} score alternatives: {d['score_keys']}")

    figs = [
        ("epoch_scores",           fig_epoch_scores(d)),
#        ("reputation_heatmap",     fig_reputation_heatmap(d)),
        ("scores_vs_reputations",  fig_scores_vs_reputations(d)),
#        ("suspected_configs",      fig_suspected_configs(d)),
    ]

    # also show detail for first, middle and last epoch
    # for idx in [0, len(d["epochs"]) // 2, len(d["epochs"]) - 1]:
    #     figs.append((f"epoch_{d['epochs'][idx]}_detail", fig_epoch_detail(d, idx)))

    for name, fig in figs:
        _apply_theme(fig)
        fig.show()
        print(f"  ✓ {name}")


def _apply_theme(fig: go.Figure):
    fig.update_layout(
        template="plotly_dark",
        font=dict(family="monospace", size=12),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        margin=dict(l=60, r=40, t=60, b=50),
    )


if __name__ == "__main__":
    main()
