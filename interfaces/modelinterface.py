import abc
from .componentinterface import ComponentBaseClass
from typing import List, Dict


class ModelBaseClass(abc.ABC):

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_controller_box_emissions(self, name) -> List[float]:
        pass

    @abc.abstractmethod
    def get_component(self, name) -> ComponentBaseClass:
        pass

    @abc.abstractmethod
    def are_connected(self, node_a, node_b) -> bool:
        pass

    @abc.abstractmethod
    def set_valve(self, name, value) -> str:
        pass

    @abc.abstractmethod
    def calculate_flows(self, gashouse) -> Dict:
        pass
