from interfaces import ComponentBaseClass
from .emissionstable import EmissionsTable
from metecmodel.components import ElectricValve
from typing import Dict
from logger import set_up_logger


class ControllerBox:

    three_by_four_styles = ['W', 'S']
    two_by_five_styles = ['T']

    def __init__(self, name: str, components: Dict = {}):
        self.name = name
        self.components = components
        self.logger = set_up_logger('ModelLogger', '../logger/logs/model_log.txt')

    def get_name(self):
        return self.name

    def add_component(self, component: ComponentBaseClass):
        self.components[component.get_full_name()] = component

    def get_component(self, name) -> ComponentBaseClass:
        return self.components.get(name, None)

    def _get_valves_and_file(self, rows, valves):
        valve_file = []
        for row in rows:
            binary_str = ['0'] * len(valves)
            for valve in valves:
                valve_name = '{}.EV-{}{}'.format(self.get_name(), row, valve)
                component: ElectricValve = self.get_component(valve_name)
                if component.get_reading() is 'open':
                    binary_str[valve-1] = '1'
            valve_str = ''.join(binary_str)
            file = 'emissions_{}_{}_row{}.csv'.format(len(rows), len(valves) + 1, row)
            valve_file.append((valve_str, file))
            self.logger.debug('Evaluating emissions for row %s and valve states %s', row, valve_str)
        return valve_file

    def get_emissions(self, inlet_pressure):
        if self.name[-1] in self.three_by_four_styles:
            valves_files = self._get_valves_and_file(range(1, 4), range(1, 4))
        elif self.name[-1] in self.two_by_five_styles:
            valves_files = self._get_valves_and_file(range(1, 3), range(1, 5))
        else:
            return 0
        emissions = []
        for valve_states, file in valves_files:
            emissions.append(EmissionsTable('../Resources/Emissions/' + file).get_emissions(inlet_pressure, valve_states))
        return emissions
