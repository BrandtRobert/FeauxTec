from interfaces import ComponentBaseClass
from metecmodel.graph import GraphNode
import random


class FlowMeter(ComponentBaseClass, GraphNode):
    def __init__(self, name, neighbors, data={}, initial_flow=20, failure_rate=0, failure_type='random'):
        ComponentBaseClass.__init__(self, name, data)
        GraphNode.__init__(self, name, neighbors)
        self.flow = initial_flow
        self.failure_rate = failure_rate
        self.failure_type = failure_type
        data['slope'] = float(data.get('slope', 1))
        data['offset'] = float(data.get('offset', 0))
        data['output_units'] = data.get('output_units', 'IN-DIA')
        data['min'] = data.get('min', 0)
        data['max'] = data.get('max', 0)

    def get_reading(self) -> float:
        if self.is_simulated_failure(self.failure_rate):
            if self.failure_type == 'random':
                return random.uniform(-100, 100)
            if self.failure_type == 'dead':
                return 0
        if self.flow == 0:
            return 0.001
        else:
            return self.flow

