from node import Node
from tree import Tree

class Reputation:
    def __init__(self, k_fl, k_sl, k_be):
        self.k_fl = k_fl # faulty link
        self.k_sl = k_sl # suspected leader
        self.k_be = k_be # block endorser
    
    def penalty_byzantine(self, node: Node):
        # TODO: set timeout and check timeout before trying to adjust score
        node.set_reputation(0)

    def penalty_faulty_link(self, node: Node):
        node.set_reputation(self.k_fl * node.get_reputation())

    def penalty_suspected_leader(self, node: Node):
        node.set_reputation(self.k_sl * node.get_reputation())

    def compensation_block_endorser(self, node: Node):
        node.set_reputation(self.k_be * node.get_reputation())

    def parse_schedule(self, schedule_data):
        for i in range(schedule_data["size"]):
            config_data = schedule_data[i]
            self.parse_config(config_data)
    
    def parse_config(self, config_data):
        tree = config_data["tree"]
        suspected = config_data["suspected"]
        instance_votes = config_data["instance_votes"]

        if suspected:
            self.penalty_suspected_leader(tree.root())

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

