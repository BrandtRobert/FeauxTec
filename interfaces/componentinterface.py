import abc
from typing import Dict


class ComponentBaseClass(abc.ABC):

    def __init__(self, name: str, data: Dict):
        self.name = name
        self.data = data

    def get_full_name(self) -> str:
        return self.name

    @abc.abstractmethod
    def get_type(self) -> str:
        pass

    def __repr__(self) -> str:
        str(self)

    def __str__(self) -> str:
        return '{}\n{}'.format(self.name, self.data)