from interfaces import ComponentBaseClass
from typing import Dict


class Component(ComponentBaseClass):

    def get_reading(self):
        return 0.0

    def __init__(self, name: str, initialization_dict: Dict, data: Dict):
        super().__init__(name, data)
        self.reader = initialization_dict.get('reader', '')
        self.type = initialization_dict.get('item_type', '')
        self.pin = initialization_dict.get('pin', '')
        data['slope'] = float(initialization_dict.get('slope', 1))
        data['offset'] = float(initialization_dict.get('offset', 0))
        data['output_units'] = initialization_dict.get('output_units', 'IN-DIA')
        data['min'] = initialization_dict.get('min', 0)
        data['max'] = initialization_dict.get('max', 0)

    def get_type(self) -> str:
        return self.type

    def get_prefix(self) -> str:
        return self.name.split('.')[0]

    def change_state(self, state: Dict):
        if self.get_type() == 'Electric Valve' and 'state' not in state:
            raise Exception('Illegal state {} for component with type {}'.format(state, self.get_type()))
        elif self.get_type() in ['Thermocouple', 'Flow Meter', 'Pressure Transducer']:
            raise Exception('Attempting to modify state of read only device {}'.format(self.get_type()))
        else:
            for k, v in state.items():
                self.data[k] = v