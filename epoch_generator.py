from tree import Tree
from node import Node

class EpochGenerator:
    def __init__(self, scale_function, epoch_size):
        self.scale_function = scale_function
        self.epoch_size = epoch_size
    
    def best_tree(self, tree_pool: list[Tree], tree_scores, memory: list[Tree], schedule: list[Tree]):
        best = None
        best_score = None
        for i in range(len(tree_pool)):
            tree = tree_pool[i]
            root_count = len([1 for t in (memory+schedule) if t.root().id == tree.root().id])
            score = tree_scores[i] * self.scale_function(root_count)
            
            if best == None:
                best = tree 
                best_score = score
                continue

            if score > best_score or (score == best_score and tree.root().id < best.root().id): # desempate por id da raiz
                best = tree
                best_score = score
        
        return best, best_score

    def generate_epoch(self, tree_pool, tree_scores, memory):
        schedule = []
        scores = []

        while len(schedule) < self.epoch_size:
            if len(tree_pool) == 0: # à partida o programa deve ser configurado para haver árvores suficientes, mas nunca se sabe
                break

            t, s = self.best_tree(tree_pool, tree_scores, memory, schedule)
            i = tree_pool.index(t)
            tree_pool = tree_pool[:i]+tree_pool[i+1:]
            tree_scores = tree_scores[:i]+tree_scores[i+1:]
            schedule.append(t)
            scores.append(s)
        
        return schedule, scores
    
class NullEpochGenerator(EpochGenerator):
    def __init__(self):
        super().__init__(0,0)
    
    def generate_epoch(self, tree_pool, tree_scores, memory):
        return tree_pool, tree_scores
    
