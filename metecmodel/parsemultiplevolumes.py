from interfaces import ParserBaseClass
from metecmodel import VolumesParser
from typing import List, Dict


class ParseMultipleVolumes(ParserBaseClass):

    def __init__(self, file_paths: List[str]):
        super().__init__(file_paths)

    def parse(self) -> Dict:
        master_dict: Dict = {}
        for path in self.file_path:
            master_dict.update(VolumesParser(path).parse())
        return master_dict
