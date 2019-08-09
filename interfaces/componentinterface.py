import abc
from typing import Dict
import random


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

    def get_reading_voltage(self):
        return self.get_reading()

    def is_simulated_failure(self, fail_rate):
        val = random.uniform(0, 1)
        if val < fail_rate:
            return True
        else:
            return False

    def __repr__(self) -> str:
        str(self)

    def __str__(self) -> str:
        return '{} ### {}'.format(self.name, self.get_reading())
