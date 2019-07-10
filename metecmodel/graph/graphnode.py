
class GraphNode:

    def __init__(self, name, neighbors):
        self.name = name
        self.neighbors = neighbors

    def get_neighbors(self):
        return self.neighbors
