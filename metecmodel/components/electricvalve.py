from interfaces import ComponentBaseClass
from typing import List
from metecmodel.graph import GraphNode


class ElectricValve(ComponentBaseClass, GraphNode):

    def __init__(self, name, neighbors, data={}, initial_state='closed', failure_rate=0):
        ComponentBaseClass.__init__(self, name, data)
        GraphNode.__init__(self, name, neighbors)
        self.state = initial_state
        self.failure_rate = failure_rate

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

    def get_reading_voltage(self):
        # Valve thinks it's closed because of a wasp nest or something
        if self.is_simulated_failure(self.failure_rate):
            print('failure occurred')
            return 1
        reading = self.get_reading()
        if reading is 'open':
            return 0
        else:
            return 1
