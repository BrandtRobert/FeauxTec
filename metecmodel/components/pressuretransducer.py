from interfaces import ComponentBaseClass
from metecmodel.graph import GraphNode
import random


class PressureTransducer(ComponentBaseClass, GraphNode):

    def __init__(self, name, neighbors, data={}, initial_pressure=50, failure_rate=0, failure_type='random'):
        ComponentBaseClass.__init__(self, name, data)
        GraphNode.__init__(self, name, neighbors)
        self.pressure = initial_pressure
        self.failure_rate = failure_rate
        self.failure_type = failure_type
        data['slope'] = float(data.get('slope', 1))
        data['offset'] = float(data.get('offset', 0))
        data['output_units'] = data.get('output_units', 'IN-DIA')
        data['min'] = data.get('min', 0)
        data['max'] = data.get('max', 0)

    def get_reading(self) -> float:
        return self.pressure

    def get_reading_voltage(self) -> float:
        if self.is_simulated_failure(self.failure_rate):
            if self.failure_type == 'random':
                return random.uniform(-10, 10)
            if self.failure_type == 'dead':
                return 0
            if self.failure_type == 'NaN':
                return float('NaN')
        reading = self.get_reading()
        reading = reading - self.data['offset']
        return reading / self.data['slope']
