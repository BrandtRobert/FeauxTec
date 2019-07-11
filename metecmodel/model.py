from metecmodel import SensorPropertiesParser, VolumesParser, ControllerBox
from metecmodel.components import *
from typing import Dict, List
from interfaces import ModelBaseClass, ComponentBaseClass
from logger import Logger
from metecmodel.graph import PNIDGraph
import threading


class Model(ModelBaseClass):

    instances = 0

    def __init__(self, sensor_properties: str, volumes_file: str,
                 initial_pressure=20, initial_temperature=75, initial_flow=15):
        self.initial_pressure = initial_pressure
        self.initial_temperature = initial_temperature
        self.initial_flow = initial_flow
        self.lock = threading.RLock()
        self.logger = Logger('ModelLogger-1', '../logger/logs/model_log.txt')
        self._init_model(sensor_properties, volumes_file)
        self.instances = self.instances + 1

    def _create_component(self, name, info, neighbors) -> ComponentBaseClass:
        if info['item_type'] == 'Electric Valve':
            if 'a' in neighbors:
                component = ThreeWayElectricValve(name, neighbors, info)
            else:
                component = ElectricValve(name, neighbors, info)
        elif info['item_type'] == 'Pressure Transducer':
            component = PressureTransducer(name, neighbors, info, initial_pressure=self.initial_pressure)
        elif info['item_type'] == 'Thermocouple':
            component = Thermocouple(name, neighbors, info, initial_temp=self.initial_temperature)
        elif info['item_type'] == 'Flow Meter':
            component = FlowMeter(name, neighbors, info, initial_flow=self.initial_flow)
        else:
            return None
        return component

    def _init_graph(self, volumes):
        self.graph = PNIDGraph()
        for item, neighbors in volumes.items():
            # If there is a component use that to add to the graph
            try:
                component = self.get_component(item)
            except KeyError:
                component = None
            if component:
                self.graph.add_node(component.get_full_name(), component.get_neighbors())
            else:
                # If not add it manually, manual valves will be set to open by default
                if 'MV' in item:
                    if 'open' in neighbors:
                        current_neighbors = neighbors['open']
                    if 'a' in neighbors:
                        current_neighbors = neighbors['a']
                else:
                    current_neighbors = neighbors
                self.graph.add_node(item, current_neighbors)

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
        self._init_graph(items_to_dict)

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
            self.logger.debug('Request for emissions on controller box {}'.format(cb_name))
            if cb_name in self.controller_boxes:
                cb: ControllerBox = self.controller_boxes[cb_name]
                return cb.get_emissions(self.initial_pressure)
            else:
                raise KeyError('{} not in model'.format(cb_name))

    def set_valve(self, name, value) -> str:
        valve: ElectricValve = self.get_component(name)
        if value != valve.get_reading():
            valve.flip_valve()
            self.logger.debug('Flipping valve {} now {}'.format(name, valve.get_reading()))
            self.graph.redraw_edges(name, valve.get_neighbors())
        return valve.get_reading()

    def are_connected(self, node_a, node_b) -> bool:
        return self.graph.are_connected(node_a, node_b)

    def calculate_flows(self, gashouse) -> Dict:
        self.logger.debug('Requesting flows for {}'.format(gashouse))
        if gashouse == 'GSH-1':
            gsh_1_boxes = ['CB-1W', 'CB-2W', 'CB-1T', 'CB-2T', 'CB-1S', 'CB-2S']
            total_emissions = 0
            for box in gsh_1_boxes:
                total_emissions = total_emissions + sum(self.get_controller_box_emissions(box))
            emissions_in_slpm = total_emissions * 0.47
            gsh_1_flow_meters = ['FM-1', 'FM-2', 'FM-3', 'FM-4']
            flow_dict = {}
            for meter in gsh_1_flow_meters:
                component = self.get_component('GSH-1.' + meter)
                component.flow = emissions_in_slpm
                flow_dict['GSH-1.' + meter] = component.get_reading()
            self.logger.debug('Returning flows {}'.format(flow_dict))
            return flow_dict
        else:
            return {}

    def change_model_pressure(self, new_pressure):
        for name, cb in self.controller_boxes.items():
            for _, component in cb.components.items():
                if component.get_type() is 'PressureTransducer':
                    component.pressure = new_pressure

    def change_model_temperature(self, new_temp):
        for name, cb in self.controller_boxes.items():
            for _, component in cb.components.items():
                if component.get_type() is 'Thermocouple':
                    component.pressure = new_temp


if __name__ == '__main__':
    m = Model('../Resources/sensor_properties.csv', '../Resources/GSH-1-volumes.json', initial_pressure=50)
    print(m.get_component('CB-1S.EV-14'))
    print(m.get_controller_box_emissions('CB-1T'))
    print(m.are_connected('GSH-1.MV-15', 'GSH-1.VOL-21'))
    print(m.are_connected('GSH-1.MV-16', 'CB-1W.VOL-1'))
    print(m.are_connected('GSH-1.MV-16', 'CB-1W.VOL-5'))
    m.set_valve('CB-1W.EV-21', 'open')
    print(m.are_connected('GSH-1.MV-16', 'CB-1W.VOL-5'))
