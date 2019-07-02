"""
    This is a class built to contain data from entries in the JSON volumes file.
    Each component represents one object or gas volume node in the gas house system.
"""


class Component:

    def __init__(self, name: str, states: dict, current_state: str, data: dict, parent: str):
        self.name = name
        self.states = states
        self.current_state = current_state
        self.data = data
        self.parent = parent

    def __str__(self):
        outstr = self.get_full_name()
        states_str = ''
        if len(self.states.items()) > 0:
            for k, v in self.states.items():
                states_str += '  {}:{}\n'.format(k, v)
        data_str = ''
        if len((self.data.items())) > 0:
            for k, v in self.data.items():
                data_str += '  {}:{}\n'.format(k, v)
        return '"{}":\n  current_state: {}\n{}{}'.format(outstr, self.current_state, states_str, data_str)

    def __repr__(self):
        current_state = self.current_state
        data = self.data
        return 'name={} state={} data={}'.format(self.get_full_name(), current_state, data)

    def get_full_name(self):
        return self.parent + '.' + self.name

    def get_current_neighbors(self):
        try:
            return self.states[self.current_state]
        except KeyError:
            print(self.get_full_name())
            print(self.current_state)
            print(self.states)
            return []
