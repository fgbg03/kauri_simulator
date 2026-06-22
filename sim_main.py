from node import Node, LeadershipSeizerNode, DisenfranchiserNode, IndirectDisenfranchiserNode, QuietParticipationNode, RandomNode, PeriodicSilentNode
from tree import Tree
from consensus import Kauri
from reputation import Reputation, ReputationOld, ReputationCosntantInnerPenalty
from tree_generator import TreeGenerator, RandomTreeGenerator, BinTreeGenerator, RandomBinGenerator
from tree_evaluator import TreeEvaluator, TreeEvaluatorInforum
from epoch_generator import EpochGenerator, NullEpochGenerator
from epoch_evaluator import EpochEvaluator

import json
from datetime import datetime
import inspect
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
import random

def infinite(epoch):
    return False

def until_epoch(target, n):
    return n == target

def simulation(
        bootstrap1: list[Tree], 
        bootstrap2: list[Tree],

        N: int,
        m: int,
        nodes: list[Node],


        latency_matrix: list[list[int]],
        ideal_latency = 110,

        exit_condition = lambda n: until_epoch(100, n),
        expected_rtt = 400,
        decisions_per_tree = 1,

        faulty_link_penalty = 0.63,
        suspected_leader_penalty = 0.6,
        compensation = 1.1,

        bins_to_use = 2,
        epoch_size = 3,
        scale_function = lambda x: 1/(x+1),
        memory_size = 12, # number of trees

        scheduler= "adaptive",
        reputation= "scaling", # which reputation engine to use

        print_to_stdout = False,
        write_to_file = True,
        consequence_logs = False
):
    reputation_module = None
    tree_evaluator = TreeEvaluator(bootstrap1[0], ideal_latency)
    epoch_evaluator = EpochEvaluator()
    tree_generator = None
    epoch_generator = None
    kauri = None

    schedules: list[list[Tree]] = []

    if reputation == "scaling":
        reputation_module = Reputation(faulty_link_penalty, suspected_leader_penalty, compensation)
    elif reputation == "constant":
        reputation_module = ReputationCosntantInnerPenalty(faulty_link_penalty, suspected_leader_penalty, compensation)
    elif reputation == "old":
        reputation_module = ReputationOld(faulty_link_penalty, suspected_leader_penalty, compensation)
    else:
        print(f"invalid reputation engine '{reputation}'\nuse 'scaling' (default), 'constant', or 'old'")
        exit(0)

    if scheduler == "adaptive":
        tree_generator = TreeGenerator(bins_to_use)
        epoch_generator = EpochGenerator(scale_function, epoch_size)
        kauri = Kauri(expected_rtt, int(expected_rtt*1.5), decisions_per_tree)
        schedules.append(bootstrap1)
        schedules.append(bootstrap2)
    elif scheduler == "adaptive-inforum":
        tree_generator = TreeGenerator(bins_to_use)
        epoch_generator = EpochGenerator(lambda x: 1, epoch_size)
        tree_evaluator = TreeEvaluatorInforum(bootstrap1[0])
        kauri = Kauri(expected_rtt, int(expected_rtt*1.5), decisions_per_tree)
        schedules.append(bootstrap1)
        schedules.append(bootstrap2)
    elif scheduler == "random-full":
        tree_generator = RandomTreeGenerator(epoch_size*decisions_per_tree)
        epoch_generator = NullEpochGenerator()
        kauri = Kauri(expected_rtt, int(expected_rtt*1.5), 1) # one random tree per every decision
        s1 = tree_generator.generate(bootstrap1[0])
        s2 = tree_generator.generate(bootstrap1[0])
        schedules.append(s1)
        schedules.append(s2)
    elif scheduler == "random-lite":
        tree_generator = RandomTreeGenerator(epoch_size)
        epoch_generator = NullEpochGenerator()
        kauri = Kauri(expected_rtt, int(expected_rtt*1.5), decisions_per_tree) # one tree does all decisions it should
        s1 = tree_generator.generate(bootstrap1[0])
        s2 = tree_generator.generate(bootstrap1[0])
        schedules.append(s1)
        schedules.append(s2)
    elif scheduler == "random-bins":
        tree_generator = RandomBinGenerator(epoch_size)
        epoch_generator = NullEpochGenerator()
        kauri = Kauri(expected_rtt, int(expected_rtt*1.5), decisions_per_tree)
        s1 = tree_generator.generate(bootstrap1[0])
        s2 = tree_generator.generate(bootstrap1[0])
        schedules.append(s1)
        schedules.append(s2)
    elif scheduler == "bins":
        tree_generator = BinTreeGenerator(epoch_size)
        epoch_generator = NullEpochGenerator()
        kauri = Kauri(expected_rtt, int(expected_rtt*1.5), decisions_per_tree)
        s1 = tree_generator.generate(bootstrap1[0])
        schedules.append(s1)
        s2 = tree_generator.generate(s1[-1])
        schedules.append(s2)
    else:
        print(f"invalid scheduler '{scheduler}'\nuse 'adaptive', 'bins', 'random-full, 'random-lite', or 'random-bins'")
        exit(0)

    params = {
        "exit_cond": inspect.getsource(exit_condition),
        "N":N,
        "fanout":m,
        "expected_rtt": expected_rtt,
        "decisions_per_tree": decisions_per_tree,
        "faulty_link_penalty": faulty_link_penalty,
        "suspected_leader_penalty": suspected_leader_penalty,
        "block_endorser_compensation": compensation,
        "bins_to_use": bins_to_use,
        "epoch_size": epoch_size,
        "scale_function": inspect.getsource(scale_function),
        "memory_size":f"{memory_size} trees",
        "scheduler": scheduler,
        "reputation": reputation,
        "bootstrap1": bootstrap1,
        "bootstrap2": bootstrap2,
        "ideal_latency": ideal_latency,
        "latency":latency_matrix,
    }

    epoch = 0
    epoch_data = {"params": params}

    epoch_data[0] = {"schedule": bootstrap1, "scores": None}
    epoch_data[1] = {"schedule": bootstrap2, "scores": None}

    while not exit_condition(epoch):
        s = schedules[-2]

        execution_data = kauri.execute_schedule(s, latency_matrix)
        
        base_tree = schedules[-1][-1] # irrelevant for all schedulers but "bins" in this one we need the last tree specificly

        reputation_module.parse_schedule(execution_data, base_tree.nodes)
        
        tree_pool = tree_generator.generate(base_tree)

        scores = []
        for tree in tree_pool:
            scores.append(tree_evaluator.score(tree, latency_matrix))

        # print(f"\n\nEpoch {epoch}:\n")
        # for n in nodes:
        #     print(f"{n}, rep = {n.get_reputation()}")
        # print()
        # for i in range(len(tree_pool)):
        #     print(f"Tree {i}")
        #     print(tree_pool[i])
        #     print(scores[i])
        #     print("---")

        # build memory for chain quality & fairness
        mem = [] # last memory_size trees
        for sched in schedules[::-1]:
            for tr in sched[::-1]:
                mem.append(tr)
                if len(mem) >= memory_size:
                    break
            if len(mem) >= memory_size:
                    break

        unified_scores = [score["unified"] for score in scores]
        new_schedule, new_schedule_tree_scores = epoch_generator.generate_epoch(tree_pool, unified_scores, mem)

        #print(f"New schedule: {new_schedule}")
        #print_schedule_scores(new_schedule_tree_scores)
        
        new_schedule_scores = {}

        new_schedule_scores["min"] = epoch_evaluator.evaluate_epoch_min(new_schedule_tree_scores)
        new_schedule_scores["average"] = epoch_evaluator.evaluate_epoch_avg(new_schedule_tree_scores)
        new_schedule_scores["median"] = epoch_evaluator.evaluate_epoch_median(new_schedule_tree_scores)
        new_schedule_scores["avg-sd"] = epoch_evaluator.evaluate_epoch_avg_minus_sd(new_schedule_tree_scores)

        new_schedule_scores["inliers_average"] = epoch_evaluator.evaluate_epoch_inlier(new_schedule_tree_scores, epoch_evaluator.evaluate_epoch_avg)
        new_schedule_scores["inliers_median"] = epoch_evaluator.evaluate_epoch_inlier(new_schedule_tree_scores, epoch_evaluator.evaluate_epoch_median)
        new_schedule_scores["inliers_avg-sd"] = epoch_evaluator.evaluate_epoch_inlier(new_schedule_tree_scores, epoch_evaluator.evaluate_epoch_avg_minus_sd)

        new_schedule_scores["bad_outliers_average"] = epoch_evaluator.evaluate_epoch_inlier_and_bad_outlier(new_schedule_tree_scores, epoch_evaluator.evaluate_epoch_avg)
        new_schedule_scores["bad_outliers_median"] = epoch_evaluator.evaluate_epoch_inlier_and_bad_outlier(new_schedule_tree_scores, epoch_evaluator.evaluate_epoch_median)
        new_schedule_scores["bad_outliers_avg-sd"] = epoch_evaluator.evaluate_epoch_inlier_and_bad_outlier(new_schedule_tree_scores, epoch_evaluator.evaluate_epoch_avg_minus_sd)

        schedules.append(new_schedule)

        # logging
        epoch_data[epoch]["reputations"] = [n.get_reputation() for n in nodes]
        epoch_data[epoch]["execution"] = execution_data
        epoch_data[epoch+2] = {}
        epoch_data[epoch+2]["schedule"] = new_schedule
        epoch_data[epoch+2]["scores"] = new_schedule_scores
        epoch += 1
    
    # write logs
    if print_to_stdout:
        print(epoch_data)

    now = datetime.now()
    AAAA = now.year
    MM = now.month
    DD = now.day
    hh = now.hour
    mm = now.minute
    ss = now.second

    if write_to_file:
        filepath = f"simresults/simresults{AAAA:04d}{MM:02d}{DD:02d}{hh:02d}{mm:02d}{ss:02d}"
        print("Writing to:", filepath)
        with open(filepath, "w") as fp:
            json.dump(epoch_data, fp, default=lambda x:repr(x), indent=2)
        
    if consequence_logs:
        filepath = f"simresults/simconsequences{AAAA:04d}{MM:02d}{DD:02d}{hh:02d}{mm:02d}{ss:02d}"
        print("Writing to:", filepath)
        with open(filepath, "w") as fp:
            json.dump(reputation_module.consequence_logs, fp, default=lambda x:repr(x), indent=2)


    return epoch_data

def print_schedule_scores(s):
    epoch_evaluator = EpochEvaluator()
    print(f" ALL:")
    print(f"     MIN:      {epoch_evaluator.evaluate_epoch_min(s)}")
    print(f"     AVERAGE:  {epoch_evaluator.evaluate_epoch_avg(s)}")
    print(f"     MEDIAN:   {epoch_evaluator.evaluate_epoch_median(s)}")
    print(f"     AVG-SD:   {epoch_evaluator.evaluate_epoch_avg_minus_sd(s)}")
    print(f" INLIERS:")
    print(f"     AVERAGE:  {epoch_evaluator.evaluate_epoch_inlier(s, epoch_evaluator.evaluate_epoch_avg)}")
    print(f"     MEDIAN:   {epoch_evaluator.evaluate_epoch_inlier(s, epoch_evaluator.evaluate_epoch_median)}")
    print(f"     AVG-SD:   {epoch_evaluator.evaluate_epoch_inlier(s, epoch_evaluator.evaluate_epoch_avg_minus_sd)}")
    print(f" BAD OUTLIERS:") 
    print(f"     AVERAGE:  {epoch_evaluator.evaluate_epoch_inlier_and_bad_outlier(s, epoch_evaluator.evaluate_epoch_avg)}")
    print(f"     MEDIAN:   {epoch_evaluator.evaluate_epoch_inlier_and_bad_outlier(s, epoch_evaluator.evaluate_epoch_median)}")
    print(f"     AVG-SD:   {epoch_evaluator.evaluate_epoch_inlier_and_bad_outlier(s, epoch_evaluator.evaluate_epoch_avg_minus_sd)}")


def test_broken_schedule():
    kauri = Kauri(100, 400, 5)
    tree1 = Tree(nodes, m) # árvore com líder lento
    tree2 = tree1.innerNodeRotations()[1] # líder bom

    res = kauri.execute_schedule([tree1, tree1], latency_matrix)
    print(f"Schedule size: {res['size']}")
    for i in range(res['size']):
        el = res[i]
        print(f"Tree {i}:")
        print(f"\tTree: {el['tree']}")
        print(f"\tFrom intance {el['start']} to {el['target']}")
        print(f"\tSuspected: {el['suspected']}")
        print(f"\tExecuted instances: {len(el['instance_votes'])}")

    res = kauri.execute_schedule([tree1, tree2], latency_matrix)
    print(f"Schedule size: {res['size']}")
    for i in range(res['size']):
        el = res[i]
        print(f"Tree {i}:")
        print(f"\tTree: {el['tree']}")
        print(f"\tFrom intance {el['start']} to {el['target']}")
        print(f"\tSuspected: {el['suspected']}")
        print(f"\tExecuted instances: {len(el['instance_votes'])}")
        if len(el['instance_votes']) != 0:
            print(f"Votes: {el['instance_votes'][0]}")

def test_schedule_scoring_methods():
    s1 = [
        1,
        1,
        0.63,
        0.6,
        0.59,
        0.55,
        0.49,
        0.20,
        0
    ]
    scores = [s1]
    for i, s in enumerate(scores):
        print(f"Scores {i+1}: {sorted(s)}")
        print_schedule_scores(s)
        print()

def boxplot_from_lists(data, labels, title="Boxplot", xlabel="Category", ylabel="Values", threshold=0.66, jitter=0.08):
    """
    Draw boxplots and overlay the raw data points used to compute them.

    Parameters
    ----------
    data : list[list[float]]
        Each inner list becomes one boxplot.
    labels : list[str]
        Label for each boxplot.
    title : str
        Plot title.
    ylabel : str
        Y-axis label.
    jitter : float
        Horizontal random displacement for points (visual separation).
    """

    # ---- validation ----
    if len(data) != len(labels):
        raise ValueError("data and labels must have the same length")

    # ---- plotting ----
    fig, ax = plt.subplots(figsize=(8, 5))

    # Draw boxplots
    ax.boxplot(
        data,
        labels=labels,
        showmeans=True,
        patch_artist=True,
        zorder=1
    )

    # Reference line at threshold
    ax.axhline(
        y=threshold,
        linestyle=":",
        linewidth=2,
        color="black",
        alpha=0.8,
        zorder=0
    )

    # Overlay raw data points
    for i, values in enumerate(data, start=1):
        x_positions = [
            i + random.uniform(-jitter, jitter)
            for _ in values
        ]
        ax.scatter(
            x_positions,
            values,
            color="orange",        # fixed color
            edgecolors="black",    # keeps visible over box
            linewidths=0.5,
            alpha=0.85,
            s=30,
            zorder=2
        )

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.show()


def categorical_points(y_values, labels, xlabel="Category", ylabel="Value", title="Point Plot"):
    """
    Plot one point per y value using categorical x labels.

    Parameters
    ----------
    y_values : list[float]
        Y coordinates for each point.
    labels : list[str]
        Label for each x position (same length as y_values).
    xlabel : str
        X-axis label.
    ylabel : str
        Y-axis label.
    title : str
        Plot title.
    """

    # ---- validation ----
    if len(y_values) != len(labels):
        raise ValueError("y_values and labels must have the same length")

    # map labels -> x positions
    x_positions = list(range(len(labels)))

    # ---- plotting ----
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(x_positions, y_values)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # ---- More Y ticks ----
    ax.yaxis.set_major_locator(MultipleLocator(0.01))
    ax.yaxis.set_minor_locator(AutoMinorLocator(1))

    # ---- Guide lines ----
    ax.grid(which="major", axis="y", linestyle=":", linewidth=1.0, alpha=0.7)
    ax.grid(which="minor", axis="y", linestyle=":", linewidth=0.6, alpha=0.4)

    plt.tight_layout()
    plt.show()

def select_latency(i,j, too_slow: list[int] = [], bad_pairs: list[tuple[int,int]] = []):
    if i == j:
        return 0
    if i in too_slow or j in too_slow:
        return 500
    if (i,j) in bad_pairs or (j,i) in bad_pairs:
        return 500
    return 100

if __name__ == "__main__":
    print("Started")
    N = 111 # N nodes
    f = (N-1)//3
    quorum_size = 2*f+1
    m = 10 # m fanout
    b_v = 20 # blocks per view
    v_e = 25 # views per epoch
    nodes = [Node(i) for i in range(N)]
    #targets = [i*3+1 for i in range(17)] # for disenfranchiser nodes
    for i in range(9):
        idx = i*3
        nodes[idx] = PeriodicSilentNode(idx)

    latency_matrix = [[select_latency(i,j, too_slow=[]) for j in range(N)] for i in range(N)]

    t1 = Tree(nodes, m)
    inner = t1.size_inner_nodes()
    t2 = Tree(nodes[inner:2*inner]+nodes[:inner]+nodes[2*inner:], m)

    simulation(
        t1.innerNodeRotations(), t2.innerNodeRotations(), N, m, nodes, latency_matrix, 
        decisions_per_tree=b_v, epoch_size=v_e, memory_size=25, 
        compensation=1.01, faulty_link_penalty=0.6400, suspected_leader_penalty=0.5035,
        scale_function=lambda x: 1/(1-(5/(4*N))) + x/(v_e*5/4/N-v_e),
        scheduler="random-bins", consequence_logs=True, reputation="constant"
    )

    print("Finished")