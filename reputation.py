from node import Node
from tree import Tree

class Reputation:
    def __init__(self, k_fl, k_sl, k_be):
        self.k_fl = k_fl # faulty link
        self.k_sl = k_sl # suspected leader
        self.k_be = k_be # block endorser

        self.consequence_logs = {}
    
    def update_logs(self, node_id, consequence):
        if self.consequence_logs.get(node_id) == None:
            self.consequence_logs[node_id] = {}
        
        if self.consequence_logs[node_id].get(consequence) == None:
            self.consequence_logs[node_id][consequence] = 0
        
        self.consequence_logs[node_id][consequence] += 1
    
    def penalty_byzantine(self, node: Node):
        # TODO: set timeout and check timeout before trying to adjust score
        node.set_reputation(0)

    def penalty_faulty_link(self, node: Node):
        node.set_reputation(self.k_fl * node.get_reputation())
        self.update_logs(node.id, "g")
        

    def penalty_suspected_leader(self, node: Node):
        node.set_reputation(self.k_sl * node.get_reputation())

    def penalty_suspected_inner_nodes(self, nodes_by_level: list[list[Node]], m):
        for level, nodes_in_level in enumerate(nodes_by_level):
            factor = self.k_sl ** (1/len(nodes_in_level))
            for node in nodes_in_level:
                node.set_reputation(factor * node.get_reputation())
                self.update_logs(node.id, f"d{level}")

    def penalty_suspected_inner_nodes_constant(self, nodes_by_level: list[list[Node]], m):
        for level, nodes_in_level in enumerate(nodes_by_level):
            factor = self.k_sl
            for node in nodes_in_level:
                node.set_reputation(factor * node.get_reputation())
                self.update_logs(node.id, f"d{level}")


    def compensation_block_endorser(self, node: Node):
        node.set_reputation(self.k_be * node.get_reputation())
        self.update_logs(node.id, "a")

    def parse_schedule(self, schedule_data, nodes: tuple[Node]):
        for i in range(schedule_data["size"]):
            config_data = schedule_data[i]
            self.parse_config(config_data)
        for p in nodes:
            p.bound_reputation()
    
    def parse_config(self, config_data):
        tree: Tree = config_data["tree"]
        suspected = config_data["suspected"]
        instance_votes = config_data["instance_votes"]

        if suspected:
            #self.penalty_suspected_leader(tree.root())
            self.penalty_suspected_inner_nodes(tree.get_inner_nodes_by_level(), tree.fanout)
            #self.penalty_suspected_inner_nodes_constant(tree.get_inner_nodes_by_level(), tree.fanout)

        for instance in instance_votes:
            self.parse_instance(tree, instance)
    
    def parse_instance(self, tree: Tree, votes):
        voter_ids = [v["id"] for v in votes]
        
        compensate = []
        penalise = []

        for id in voter_ids:
            node = tree.get_node(id)
            children = tree.children(node)

            hasPenalty = False
            for c in children:
                if c.id not in voter_ids:
                    hasPenalty = True
                    penalise.append(c.id)
                    penalise.append(node.id)
            if not hasPenalty:
                compensate.append(node.id)
        
        for id in compensate:
            self.compensation_block_endorser(tree.get_node(id))

        for id in penalise:
            self.penalty_faulty_link(tree.get_node(id))

# Only penalises the leader for faulty configs
class ReputationOld(Reputation):
    def __init__(self, k_fl, k_sl, k_be):
        super().__init__(k_fl, k_sl, k_be)
    
    def parse_config(self, config_data):
        tree: Tree = config_data["tree"]
        suspected = config_data["suspected"]
        instance_votes = config_data["instance_votes"]

        if suspected:
            self.penalty_suspected_leader(tree.root())
            #self.penalty_suspected_inner_nodes(tree.get_inner_nodes_by_level(), tree.fanout)
            #self.penalty_suspected_inner_nodes_constant(tree.get_inner_nodes_by_level(), tree.fanout)

        for instance in instance_votes:
            self.parse_instance(tree, instance)

# Penalises every inner node with the same factor when a config does not produce blocks
class ReputationCosntantInnerPenalty(Reputation):
    def __init__(self, k_fl, k_sl, k_be):
        super().__init__(k_fl, k_sl, k_be)
    
    def parse_config(self, config_data):
        tree: Tree = config_data["tree"]
        suspected = config_data["suspected"]
        instance_votes = config_data["instance_votes"]

        if suspected:
            #self.penalty_suspected_leader(tree.root())
            #self.penalty_suspected_inner_nodes(tree.get_inner_nodes_by_level(), tree.fanout)
            self.penalty_suspected_inner_nodes_constant(tree.get_inner_nodes_by_level(), tree.fanout)

        for instance in instance_votes:
            self.parse_instance(tree, instance)
