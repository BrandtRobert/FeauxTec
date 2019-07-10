from metecmodel import SensorPropertiesParser, VolumesParser, ControllerBox
from metecmodel.components import *
from typing import Dict, List
from interfaces import ModelBaseClass, ComponentBaseClass
from logger import set_up_logger
import threading


class Model(ModelBaseClass):

    def __init__(self, sensor_properties: str, volumes_file: str,
                 initial_pressure=20, initial_temperature=75, initial_flow=15):
        self.initial_pressure = initial_pressure
        self.initial_temperature = initial_temperature
        self.initial_flow = initial_flow
        self._init_model(sensor_properties, volumes_file)
        self.lock = threading.RLock()
        self.logger = set_up_logger('ModelLogger', '../logger/logs/model_log.txt')

    @staticmethod
    def _create_component(name, info, neighbors) -> ComponentBaseClass:
        if info['item_type'] == 'Electric Valve':
            if 'a' in neighbors:
                component = ThreeWayElectricValve(name, neighbors, info)
            else:
                component = ElectricValve(name, neighbors, info)
        elif info['item_type'] == 'Pressure Transducer':
            component = PressureTransducer(name, neighbors, info)
        elif info['item_type'] == 'Thermocouple':
            component = Thermocouple(name, neighbors, info)
        elif info['item_type'] == 'Flow Meter':
            component = FlowMeter(name, neighbors, info)
        else:
            return None
        return component

    def _init_model(self, sensor_properties_file, volumes_file):
        csv_rows: Dict[ComponentBaseClass] = SensorPropertiesParser(sensor_properties_file).parse()
        items_to_dict: Dict = VolumesParser(volumes_file).parse()
        controller_boxes = {}
        for name, info in csv_rows.items():
            if name in items_to_dict:
                component = self._create_component(name, info, items_to_dict[name])
                if component.get_prefix() in controller_boxes:
                    cb: ControllerBox = controller_boxes[component.get_prefix()]
                    cb.add_component(component)
                else:
                    cb = ControllerBox(component.get_prefix(), components={component.get_full_name(): component})
                    controller_boxes[component.get_prefix()] = cb
        self.controller_boxes = controller_boxes

    def get_component(self, name: str) -> ComponentBaseClass:
        with self.lock:
            prefix = name.split('.')[0]
            if prefix in self.controller_boxes:
                cb: ControllerBox = self.controller_boxes[prefix]
                return cb.get_component(name)
            else:
                raise KeyError('{} not in model'.format(name))

    def get_controller_box_emissions(self, cb_name) -> List[float]:
        with self.lock:
            self.logger.debug('Request for emissions on controller box %s', cb_name)
            if cb_name in self.controller_boxes:
                cb: ControllerBox = self.controller_boxes[cb_name]
                return cb.get_emissions(self.initial_pressure)
            else:
                raise KeyError('{} not in model'.format(cb_name))

    def set_valve(self, name, value) -> str:
        valve: ElectricValve = self.get_component(name)
        if value != valve.get_reading():
            valve.flip_valve()
            self.logger.debug('Flipping valve %s now %s', name, valve.get_reading())
            # redraw edges
        return valve.get_reading()

    def are_connected(self) -> bool:
        return True


if __name__ == '__main__':
    m = Model('../Resources/sensor_properties.csv', '../Resources/GSH-1-volumes.json', initial_pressure=50)
    print(m.get_component('CB-1S.EV-14'))
    print(m.get_controller_box_emissions('CB-1T'))
