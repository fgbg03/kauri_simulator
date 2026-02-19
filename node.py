class Node:
    def __init__(self, id):
        self.id = id
        self._reputation = 0.66

    def set_reputation(self, value):
        value = min(value, 1)
        value = max(value, 0)
        self._reputation = value

    def get_reputation(self):
        return self._reputation
    
    # return if node performs byzantine actions to omit its or the targets vote in a given tree
    def is_byzantine(self, target, tree):
        return False # default node is honest

    def __eq__(self, other): 
        if not isinstance(other, Node):
            return False
        return self.id == other.id
    
    def __str__(self):
        char = self.id if self.id < 10 else chr(ord("A") + self.id-10)
        return f"{type(self).__name__} {char}"
    
    def __repr__(self):
        return f"{type(self).__name__}<{self.id}>"

# does not aggregate/disseminate from/to its targets
class DisenfranchiserNode(Node):
    def __init__(self, id, target_ids: list[int]):
        super().__init__(id)
        self.target_ids = target_ids.copy()
    
    def is_byzantine(self, target, tree):
        if target.id in self.target_ids:
            return True

        return False

# if targets are not directly bellow, checks if it's beneficial to attack
class IndirectDisenfranchiserNode(DisenfranchiserNode):
    def __init__(self, id, target_ids, penalty_rate, compensation_rate):
        super().__init__(id, target_ids)
        self.penalty_rate = penalty_rate
        self.compensation_rate = compensation_rate
    
    def is_byzantine(self, target, tree):
        if super().is_byzantine(target, tree):
            return True
        
        # check if it indirectly keeps disenfranchisement targets with low reputation
        targets_in_subtree = []
        pending = [target]
        while len(pending) != 0:
            current = pending.pop()
            pending += tree.children(current)

            if current.id in self.target_ids:
                targets_in_subtree.append(current.id)

        if len(targets_in_subtree) == 0:
            # no targets affected
            return False

        # check targets would not be favoured
        reps: dict = tree.get_reputations()

        # self and direct target would be penalised
        reps[self.id] *= self.penalty_rate
        reps[target.id] *= self.penalty_rate

        f = (tree.size()-1)//3
        
        low_scores = sorted(list(reps.values()))[:f]

        for i in targets_in_subtree:
            # prevents disenfranchisement target from rising above lowest f scores
            if reps[i] in low_scores and reps[i]*self.compensation_rate > low_scores[-1]:
                return True

        return False

# behaves correctly until becoming an inner node
class LeadershipSeizerNode(Node):
    def __init__(self, id):
        super().__init__(id)

    def is_byzantine(self, target, tree):
        return self in tree.get_inner_nodes()