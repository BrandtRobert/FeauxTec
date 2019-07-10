from interfaces import ComponentBaseClass
from typing import List
from metecmodel.graph import GraphNode


class ElectricValve(ComponentBaseClass, GraphNode):

    def __init__(self, name, neighbors, data={}, initial_state='closed'):
        ComponentBaseClass.__init__(self, name, data)
        GraphNode.__init__(self, name, neighbors)
        self.state = initial_state

    def get_reading(self) -> str:
        return self.state

    def flip_valve(self) -> str:
        if self.state == 'closed':
            self.state = 'open'
        else:
            self.state = 'closed'
        return self.state

    def get_neighbors(self) -> List[str]:
        if self.state == 'open':
            return self.neighbors['open']
        else:
            return self.neighbors['closed']

