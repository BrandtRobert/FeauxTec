from json_minify import json_minify
from metecmodel.component import Component
import json
from typing import List


class PnIDParser:

    def __init__(self, path):
        self.file_path = path

    '''
        Parses pnid json and returns a list of component objects. JSON entries go by the following format:
            {
                "item": "<obj-name>",
                "states": {
                    // set of valid states
                    "open": [<neighboring/connected objects when in this state>],
                    "close": [<neighboring/connected objects when in this state>]
                    // if the object only has one state then use the convention
                    "normal": [<neighboring objects>]
                },
                "current_state": <must be a state in "states">,
                "data": {
                    // any other relevant data pertaining to the object
                    reading: 12.5,
                    temperature: 45,
                    etc.
                }
            }
    '''
    def read_json(self) -> List[Component]:
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
