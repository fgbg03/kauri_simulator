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

    def __eq__(self, other): 
        if not isinstance(other, Node):
            return False
        return self.id == other.id
    
    def __str__(self):
        char = self.id if self.id < 10 else chr(ord("A") + self.id-10)
        return f"Node {char}"
    
    def __repr__(self):
        return f"Node<{self.id}>"