from interfaces import ComponentBaseClass
from metecmodel.graph import GraphNode


class PressureTransducer(ComponentBaseClass, GraphNode):

    def __init__(self, name, neighbors, data={}, initial_pressure=50):
        ComponentBaseClass.__init__(self, name, data)
        GraphNode.__init__(self, name, neighbors)
        self.pressure = initial_pressure
        data['slope'] = float(data.get('slope', 1))
        data['offset'] = float(data.get('offset', 0))
        data['output_units'] = data.get('output_units', 'IN-DIA')
        data['min'] = data.get('min', 0)
        data['max'] = data.get('max', 0)

    def get_reading(self) -> float:
        return self.pressure

    def get_reading_voltage(self) -> float:
        reading = self.get_reading()
        reading = reading - self.data['offset']
        return reading / self.data['slope']
