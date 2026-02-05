from tree import Tree
from node import Node

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
            if i >= self.bins_to_use:
                break

            tree_nodes = [] + bin # current bin first (inner nodes), concat -> do not pass reference
            for j, b in enumerate(bins): # add remaining bins
                if j == i:
                    continue
                tree_nodes += b

            t = Tree(tree_nodes, base_tree.fanout)
            tree_pool += t.innerNodeRotations()

        return tree_pool