from node import Node 

class Tree:
    def __init__(self, nodes, m: int):
        self.nodes = tuple(nodes)
        self.fanout = m
        self.positions = [0]*len(nodes)
        for i, n in enumerate(self.nodes):
            self.positions[n.id] = i
    
    def size(self):
        return len(self.nodes)
    
    def size_inner_nodes(self):
        return (self.size() - 1 + self.fanout - 1) // self.fanout
    
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
        if id >= len(self.positions):
            return None
        pos = self.positions[id]
        return self.node_at(pos)

    def index(self, node):
        if node.id >= len(self.positions):
            return None
        return self.positions[node.id]

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
        if node.id >= len(self.nodes):
            return None
        
        children = []
        idx = self.index(node)
        m = self.fanout

        chldrn_start = m*idx+1
        for i in range(m):
            chld_pos = chldrn_start + i
            c = self.node_at(chld_pos)
            if c is None:
                break
            children.append(c)

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
    
    def get_inner_nodes(self) -> tuple[Node]:
        return self.nodes[:self.size_inner_nodes()]
    
    def get_inner_nodes_by_level(self):
        by_level = []
        inner = self.get_inner_nodes()
        level = 0
        begin = 0
        end = 0
        m = self.fanout
        while begin < len(inner):
            end = begin + m**level
            by_level.append(inner[begin:end])
            begin = end
            level += 1
        return by_level

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

if __name__ == "__main__":
    print("Testing tree")
    t = Tree([Node(i) for i in range(100)], 10)
    print(f"Inner nodes: {t.get_inner_nodes()}")
    print()
    print(f"Inner nodes by level: {t.get_inner_nodes_by_level()}")