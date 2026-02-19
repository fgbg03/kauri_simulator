from node import Node 

class Tree:
    def __init__(self, nodes, m: int):
        self.nodes = tuple(nodes)
        self.fanout = m
    
    def size(self):
        return len(self.nodes)
    
    def size_inner_nodes(self):
        numInnerNodes = 0
        for n in self.nodes:
            if len(self.children(n)) == 0:
                break
            numInnerNodes += 1
        return numInnerNodes
    
    def get_reputations(self):
        reps = {}
        for n in self.nodes:
            reps[n.id] = n.get_reputation()
        return reps

    def node_at(self, idx):
        if idx >= len(self.nodes):
            return None
        return self.nodes[idx]
    
    def get_node(self, id):
        for n in self.nodes:
            if n.id == id:
                return n
        return None

    def index(self, node):
        return self.nodes.index(node)

    def root(self):
        return self.node_at(0)

    def is_root(self, node):
        return self.nodes[0] == node

    def parent(self, node):
        if node not in self.nodes:
            return None
        if self.is_root(node):
            return None
        idx = self.index(node)
        parentIdx = int((idx-1)/self.fanout)
        return self.nodes[parentIdx]
    
    def children(self, node):
        if node not in self.nodes:
            return None
        
        children = []
        idx = self.index(node)

        idxLevelStart = 0
        idxChildLevelStart = 0
        level = 0
        while True:
            idxLevelStart = idxChildLevelStart
            idxChildLevelStart += self.fanout**level

            if idx < idxChildLevelStart:
                break

            level+=1
        idxInLevel = idx - idxLevelStart

        for i in range(self.fanout):
            childIdx = idxChildLevelStart + idxInLevel*self.fanout + i
            if childIdx >= len(self.nodes):
                break
            children.append(self.node_at(childIdx))

        return children
    
    def levels(self):
        idx = len(self.nodes)-1
        idxLevelStart = 0
        idxChildLevelStart = 0
        level = 0
        while True:
            idxLevelStart = idxChildLevelStart
            idxChildLevelStart += self.fanout**level

            if idx < idxChildLevelStart:
                break

            level+=1
        return level+1
    
    def get_inner_nodes(self):
        return self.nodes[:self.size_inner_nodes()]

    def innerNodeRotations(self):
        trees = []
        numInnerNodes = self.size_inner_nodes()
        innerNodes = self.nodes[:numInnerNodes]
        leafNodes = self.nodes[numInnerNodes:]
        
        for i in range(numInnerNodes):
            innerRotation = innerNodes[i:] + innerNodes[:i]
            trees.append(Tree(innerRotation+leafNodes, self.fanout))

        return trees

    def __eq__(self, other):
        if not isinstance(other, Tree):
            return False
        
        if self.fanout != other.fanout:
            return False
        if self.size() != other.size():
            return False
        for i in range(self.size()):
            if self.node_at(i) != other.node_at(i):
                return False
        return True

    def __str__(self):
        return f"Tree {self.fanout} {self.nodes}"
    
    def __repr__(self):
        return f"Tree<{self.fanout},{self.nodes}>"
    
    def draw(self):
        vec = self.nodes
        fanout = self.fanout

        # Build levels (BFS)
        levels = []
        i = 0
        count = 1
        while i < len(vec):
            levels.append(vec[i:i + count])
            i += count
            count *= fanout

        # Horizontal spacing
        unit = 7

        # Compute positions
        positions = []
        width = fanout ** (len(levels) - 1)

        for depth, level in enumerate(levels):
            step = width // len(level)
            pos = [(i * step + step // 2) * unit for i in range(len(level))]
            positions.append(pos)

        # Draw
        for level, pos in zip(levels, positions):
            line = ""
            last = 0
            for x, val in zip(pos, level):
                line += " " * (x - last) + str(val)
                last = x + len(str(val))
            print(line.rstrip())

