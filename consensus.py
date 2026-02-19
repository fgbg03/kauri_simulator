from tree import Tree
from node import Node

class Kauri:
    def __init__(self, soft_timeout, hard_timeout, decisions_per_tree):
        self.soft_timeout = soft_timeout
        self.hard_timeout = hard_timeout
        self.decisions_per_tree = decisions_per_tree
        self.executed_instances = 0
        self.next_target = decisions_per_tree
    
    def execute_schedule(self, schedule, latency_matrix):
        schedule_data = {"size": len(schedule)}
        start = self.executed_instances
        target = self.next_target
        for i, tree in enumerate(schedule):
            res = self.execute_configuration(tree, latency_matrix, start, target)

            schedule_data[i] = res

            # em caso de falha, a árvore seguinte faz apenas as instâncias que lhe competiam
            start += len(res["instance_votes"])
            target += len(res["instance_votes"])
        
        self.executed_instances = start
        self.next_target = target
        return schedule_data

    def execute_configuration(self, tree: Tree, latency_matrix, start_instance, target_instance):
        votes = {"tree": tree, "start": start_instance, "target": target_instance, "suspected": False, "instance_votes": []}
        i = start_instance
        while i < target_instance:
            # simular cada instancia e aplicar lógica para abortar configuração
            res = self.execute_instance(tree, latency_matrix)

            if len(res) == 0: # timed out -> abort configuration
                votes["suspected"] = True
                break
            votes["instance_votes"].append(res)
            i += 1
            # por enquanto isto ou aborta imediatamente, ou obtém k resultados iguais
        
        return votes
    
    def execute_instance(self, tree: Tree, latency_matrix):
        # get timestamp of nodes arriving at the root
        votes = []

        nodes = [tree.root()]
        while len(nodes) != 0:
            n = nodes.pop()
            
            child = n
            parent = tree.parent(n)
            time = 0
            # time from node to root
            while parent != None:
                # check parent wants do receive child's vote and child want to pass vote to parent
                if parent.is_byzantine(child, tree) or child.is_byzantine(parent, tree):
                    time = -1
                    break
                time += latency_matrix[child.id][parent.id]
                child = parent
                parent = tree.parent(parent)

            # add vote if aggregated
            if time >= 0:
                time *= 2
                votes.append({"id": n.id, "time": time})

            nodes += tree.children(n)

        # exclude late votes

        votes.sort(key=lambda v: (v["time"],v["id"]), reverse=True) #TODO: desempates estão a ser resolvidos com o ID, talvez devessem ser resolvidos com a posição na árvore

        collected = []

        # collect all votes before first timeout
        i = len(votes)
        while i > 0 and votes[i-1]["time"] <= self.soft_timeout:
            i -= 1

        collected += votes[i:]

        votes = votes[:i] # remove collected votes

        # collect votes before second timeout to reach quorum
        quroum_size = (tree.size()-1) // 3 * 2 + 1
        while len(collected) < quroum_size:
            if len(votes) == 0:
                break
            v = votes.pop()
            if v["time"] <= self.hard_timeout:
                collected.append(v)
            else:
                break
        
        if len(collected) < quroum_size: # too many late votes -> no verified block
            return []
        else:
            return collected

class KauriBatataQuente(Kauri):
    def execute_schedule(self, schedule, latency_matrix):
        schedule_data = {"size": len(schedule)}
        start = self.executed_instances
        target = self.next_target
        for i, tree in enumerate(schedule):
            res = self.execute_configuration(tree, latency_matrix, start, target)

            schedule_data[i] = res

            # em caso de falha, a árvore seguinte faz as instâncias deixadas pela anterior
            start += len(res["instance_votes"])
            target += self.decisions_per_tree
        
        self.executed_instances = start
        self.next_target = target
        return schedule_data