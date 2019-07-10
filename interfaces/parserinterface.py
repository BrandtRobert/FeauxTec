import abc
from typing import List
from interfaces import ComponentBaseClass


class ParserBaseClass(abc.ABC):

    def __init__(self, file_path: str):
        self.file_path = file_path

    @abc.abstractmethod
    def parse(self) -> List[ComponentBaseClass]:
        pass

