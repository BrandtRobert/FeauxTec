import abc
from typing import Dict


class ComponentBaseClass(abc.ABC):

    def __init__(self, name: str, data: Dict):
        self.name = name
        self.data = data

    def get_full_name(self) -> str:
        return self.name

    def get_prefix(self):
        return self.name.split('.')[0]

    def get_type(self):
        return self.__class__.__name__

    @abc.abstractmethod
    def get_reading(self):
        pass

    def __repr__(self) -> str:
        str(self)

    def __str__(self) -> str:
        return '{} ### {}'.format(self.name, self.get_reading())
