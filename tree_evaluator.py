from tree import Tree
from node import Node

class TreeEvaluator:
    def __init__(self, tree: Tree, ideal_average_latency):
        # best behaviour tree estimation -> every reputation = 1 => N*rep = N
        self.ideal_behaviour_score = tree.size()
        
        # best network tree estimation -> every link has ideal average latency -> get sum of distances to root from quorum
        quorum_size = (tree.size()-1) // 3 * 2 + 1
        count = 1
        level = 1
        net_score = 0
        while count < quorum_size:
            net_score += ideal_average_latency * min(quorum_size-count, tree.fanout**level) * level
            count += min(quorum_size-count, tree.fanout**level)
            level += 1

        self.ideal_networks_score = net_score
    
    def distance_to_root(self, tree, node, latency_matrix):
        child = node
        parent = tree.parent(child)
        distance = 0
        while parent != None:
            distance += latency_matrix[child.id][parent.id]
            child = parent
            parent = tree.parent(child)
        return distance

    def score_behaviour(self, tree: Tree):
        pending = [tree.root()]
        score = 0

        while len(pending) != 0:
            current = pending.pop()
            pending += tree.children(current)

            p = 1
            current = tree.parent(current)
            while current != None:
                p *= current.get_reputation()
                current = tree.parent(current)
            
            score += p
        
        return score

    def score_network(self, tree: Tree, latency_matrix):
        quorum_size = (tree.size()-1) // 3 * 2 + 1

        pending = [tree.root()]
        count = 0
        score = 0

        while count < quorum_size:
            closest = None
            distance = None

            for n in pending:
                if closest == None:
                    closest = n
                    distance = self.distance_to_root(tree, n, latency_matrix)
                else:
                    d = self.distance_to_root(tree, n, latency_matrix)
                    if d < distance or (d == distance and n.id < closest.id):
                        closest = n
                        distance = d
            
            count += 1
            score += distance
            pending.remove(closest)
            pending += tree.children(closest)
        
        return score
            


    def score_unify(self, behaviour, network):
        # normalise scores so that they're [0,1] with 0 being the worst value and 1 being the best
        behaviour_norm = behaviour/self.ideal_behaviour_score
        network_norm = self.ideal_networks_score/network

        # discretise behaviour score (primary indicator)
        behaviour_discrete = int(behaviour_norm*10)/10.0 # steps of 0.1

        # scale network score to fit between the discrete steps
        network_scaled = network_norm/10.0

        return behaviour_discrete + network_scaled


    def score(self, tree: Tree, latency_matrix):
        scores = {}

        scores["behaviour"] = self.score_behaviour(tree)
        scores["network"] = self.score_network(tree, latency_matrix)
        scores["unified"] = self.score_unify(scores["behaviour"], scores["network"])

        return scores
    
class TreeEvaluatorInforum(TreeEvaluator):
    def __init__(self, tree):
        super().__init__(tree, 1)

    def score_behaviour(self, tree):
        total = 0

        for node in tree.get_inner_nodes():
            total += node.get_reputation()
        
        return total
    
    def score(self, tree: Tree, latency_matrix):
        scores = {}

        scores["unified"] = self.score_behaviour(tree)

        return scores