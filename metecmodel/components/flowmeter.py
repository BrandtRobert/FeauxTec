from typing import List
from interfaces import ComponentBaseClass
from metecmodel.graph import GraphNode


class FlowMeter(ComponentBaseClass, GraphNode):
    def __init__(self, name, neighbors, data={}, initial_flow=20):
        ComponentBaseClass.__init__(self, name, data)
        GraphNode.__init__(self, name, neighbors)
        self.flow = initial_flow
        data['slope'] = float(data.get('slope', 1))
        data['offset'] = float(data.get('offset', 0))
        data['output_units'] = data.get('output_units', 'IN-DIA')
        data['min'] = data.get('min', 0)
        data['max'] = data.get('max', 0)

    def get_reading(self) -> float:
        return self.flow

