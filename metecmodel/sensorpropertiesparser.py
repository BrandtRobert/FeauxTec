from typing import Dict
from interfaces import ParserBaseClass
from interfaces import ComponentBaseClass
import csv


class SensorPropertiesParser(ParserBaseClass):

    def __init__(self, file_path: str):
        super().__init__(file_path)

    def parse(self) -> Dict:
        items = {}
        with open(self.file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                items[row['name']] = row
        return items


