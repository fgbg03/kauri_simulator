from tree import Tree
from node import Node
import numpy as np

class TreeGenerator:
    def __init__(self, bins_to_use = 1):
        self.bins_to_use = bins_to_use # how many bins to try to use when generating trees

    def generate(self, base_tree: Tree):
        num_inner_nodes = base_tree.size_inner_nodes()

        nodes = sorted(list(base_tree.nodes), key= lambda x: (x.get_reputation(), x.id), reverse=True) # TODO desempate com id talvez não seja ideal

        bins = [nodes[i:i+num_inner_nodes] for i in range(0, len(nodes), num_inner_nodes)]
        
        if len(bins[-1]) != num_inner_nodes: # ensure last bin fills inner nodes
            tmp1 = bins.pop()
            tmp2 = bins.pop()
            bins.append(tmp2+tmp1)

        tree_pool = []

        for i, bin in enumerate(bins):
            #if i >= self.bins_to_use:
            #    break

            tree_nodes = [] + bin # current bin first (inner nodes), concat -> do not pass reference
            for j, b in enumerate(bins): # add remaining bins
                if j == i:
                    continue
                tree_nodes += b

            t = Tree(tree_nodes, base_tree.fanout)
            tree_pool += t.innerNodeRotations()

        return tree_pool
    
class NullTreeGenerator(TreeGenerator):
    def __init__(self):
        super().__init__()
    
    def generate(self, base_tree):
        return []
    
class RandomTreeGenerator(TreeGenerator):
    def __init__(self, n_trees):
        super().__init__()
        self.n_trees = n_trees

    def generate(self, base_tree):
        fanout = base_tree.fanout
        node_tuple = base_tree.nodes
        tree_pool = []
        for _ in range(self.n_trees):
            rand_nodes = list(node_tuple)
            np.random.shuffle(rand_nodes)
            new_tree = Tree(rand_nodes, fanout)
            tree_pool.append(new_tree)
        return tree_pool
    
class BinTreeGenerator(TreeGenerator):
    def __init__(self, n_trees, bins_to_use=1):
        super().__init__(bins_to_use)
        self.n_trees = n_trees
    
    """
    base_tree should be the last tree used before generating more bin-based trees
        in order to follow kauri's logic
    """
    def generate(self, base_tree):
        def log(base, v):
            return np.log(v) / np.log(base)
        tree_pool = []
        last_tree = base_tree

        m = base_tree.fanout
        n = len(base_tree.nodes)
        depth = np.ceil(log(m, n * (m-1) + 1))-1
        shift = (m**depth - 1) / (m - 1) # shift between two consecutive trees
        shift = int(shift)

        for _ in range(self.n_trees):
            next_nodes = np.roll(list(last_tree.nodes), shift)
            new_tree = Tree(next_nodes, m)
            tree_pool.append(new_tree)
            last_tree = new_tree
        return tree_pool
    
class RandomBinGenerator(TreeGenerator):
    def __init__(self, n_trees):
        super().__init__()
        self.n_trees = n_trees

    def generate(self, base_tree):
        fanout = base_tree.fanout
        
        num_inner_nodes = base_tree.size_inner_nodes()

        nodes = sorted(list(base_tree.nodes), key= lambda x: (x.get_reputation(), x.id), reverse=True) # TODO desempate com id talvez não seja ideal

        bins = [nodes[i:i+num_inner_nodes] for i in range(0, len(nodes), num_inner_nodes)]
        
        if len(bins[-1]) != num_inner_nodes: # ensure last bin fills inner nodes
            tmp1 = bins.pop()
            tmp2 = bins.pop()
            bins.append(tmp2+tmp1)

        tree_pool = []

        for _ in range(self.n_trees):
            r = np.random.randint(0, len(bins))

            inner_bin = [] + bins[r]
            np.random.shuffle(inner_bin)

            leaf_bins = []
            for i, b in enumerate(bins):
                if r == i:
                    continue
                leaf_bins += b
            np.random.shuffle(leaf_bins)

            new_tree = Tree(inner_bin+leaf_bins, fanout)
            tree_pool.append(new_tree)
        return tree_pool
    
if __name__ == "__main__":
    print("testing tree generators")
    nodes = [Node(6), Node(3), Node(0), Node(4), Node(2), Node(5), Node(1)]
    base_tree = Tree(nodes,2)

    print("testing random tree generator")
    rtg = RandomTreeGenerator(10)
    gen1 = rtg.generate(base_tree)
    gen2 = rtg.generate(base_tree)

    print(f"gen1 == gen2 => {np.array_equal(gen1,gen2)}")
    print(f"gen1:\n{gen1}")
    print(f"\ngen2:\n{gen2}")

    print("\n\n\ntesting bin tree generator")
    btg = BinTreeGenerator(7)
    gen = btg.generate(base_tree)

    print(gen)
    for i, t in enumerate(gen):
        print(f"Tree {i+1}")
        t.draw()
        print()

    print("testing random bins")
    rbg = RandomBinGenerator(10)
    gen1 = rbg.generate(base_tree)
    gen2 = rbg.generate(base_tree)

    print(f"gen1 == gen2 => {np.array_equal(gen1,gen2)}")
    print(f"gen1:\n{gen1}")
    print(f"\ngen2:\n{gen2}")

    for i, t in enumerate(gen1):
        print(f"Tree {i+1}")
        t.draw()
        print()