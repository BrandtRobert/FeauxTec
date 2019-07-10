import abc
from .componentinterface import ComponentBaseClass
from typing import List


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
    def are_connected(self) -> bool:
        pass

    @abc.abstractmethod
    def set_valve(self, name, value) -> str:
        pass
