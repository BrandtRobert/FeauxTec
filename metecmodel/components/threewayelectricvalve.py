from interfaces import ComponentBaseClass
from typing import List
from metecmodel.graph import GraphNode


class ThreeWayElectricValve(ComponentBaseClass, GraphNode):

    def __init__(self, name, neighbors, data={}, initial_state='a'):
        ComponentBaseClass.__init__(self, name, data)
        GraphNode.__init__(self, name, neighbors)
        self.state = initial_state

    def get_reading(self) -> str:
        self.state

    def flip_valve(self) -> str:
        if self.state == 'a':
            self.state = 'b'
        else:
            self.state = 'a'
        return self.state

    def get_neighbors(self) -> List[str]:
        if self.state == 'a':
            return self.neighbors['a']
        else:
            return self.neighbors['b']

