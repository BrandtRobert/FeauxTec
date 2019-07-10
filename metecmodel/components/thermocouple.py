from interfaces import ComponentBaseClass
from metecmodel.graph import GraphNode


class Thermocouple(ComponentBaseClass, GraphNode):

    def __init__(self, name, neighbors, data={}, initial_temp=75):
        ComponentBaseClass.__init__(self, name, data)
        GraphNode.__init__(self, name, neighbors)
        self.temperature = initial_temp
        data['slope'] = float(data.get('slope', 1))
        data['offset'] = float(data.get('offset', 0))
        data['output_units'] = data.get('output_units', 'IN-DIA')
        data['min'] = data.get('min', 0)
        data['max'] = data.get('max', 0)

    def get_reading(self) -> float:
        return self.temperature
