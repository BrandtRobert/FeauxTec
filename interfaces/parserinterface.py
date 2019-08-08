import abc
from typing import Dict


class ParserBaseClass(abc.ABC):

    def __init__(self, file_path):
        self.file_path = file_path

    @abc.abstractmethod
    def parse(self) -> Dict:
        pass

