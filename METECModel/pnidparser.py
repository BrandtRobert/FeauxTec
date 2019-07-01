from json_minify import json_minify
from METECModel.component import Component
import json


class PnIDParser:

    def __init__(self, path):
        self.file_path = path

    def read_json(self):
        try:
            with open(self.file_path, 'r') as file_handle:
                cleaned_json: str = json_minify(file_handle.read())
                component_list = []
                # Remember that the data is a list of json objects
                for entry in json.loads(cleaned_json):
                    item_str = entry['item']
                    parent, name = item_str.split('.')
                    states = entry['states']
                    data = entry['data']
                    current_state = entry['current_state']
                    component_list.append(Component(name, states, current_state, data, parent))
            return component_list
        except IOError:
            print('Error when reading input file')
            exit(1)
