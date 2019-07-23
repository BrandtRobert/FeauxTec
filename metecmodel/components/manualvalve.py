from interfaces import ComponentBaseClass
from metecmodel.graph import GraphNode
from typing import List


class ManualValve(ComponentBaseClass, GraphNode):

    def __init__(self, name, neighbors, data={}, initial_state='open'):
        ComponentBaseClass.__init__(self, name, data)
        GraphNode.__init__(self, name, neighbors)
        self.state = initial_state

    def get_reading(self) -> str:
        return self.state

    def flip_valve(self) -> str:
        if self.state == 'closed':
            self.state = 'open'
        elif self.state == 'a':
            self.state = 'b'
        elif self.state == 'b':
            self.state = 'a'
        elif self.state == 'open':
            self.state = 'closed'
        return self.state

    def get_neighbors(self) -> List[str]:
        return self.neighbors[self.state]
