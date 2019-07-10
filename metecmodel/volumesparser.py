from interfaces import ParserBaseClass, ComponentBaseClass
from json_minify import json_minify
from typing import Dict
import json


class VolumesParser(ParserBaseClass):

    def __init__(self, file_path):
        super().__init__(file_path)

    def parse(self) -> Dict:
        with open(self.file_path, 'r') as json_file:
            cleaned_str: str = json_minify(json_file.read())
            components_to_neighbors = {}
            for entry in json.loads(cleaned_str):
                key = entry['ITEM']
                states_list = entry['STATES']
                if len(states_list) == 1 and 'NORMAL' == states_list[0]['STATE']:
                    neighbors = states_list[0]['COMMON']
                else:
                    neighbors = {}
                    for obj in states_list:
                        neighbors[obj['STATE'].lower()] = obj['COMMON']
                components_to_neighbors[key] = neighbors
            return components_to_neighbors
