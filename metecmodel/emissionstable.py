import pandas as pd
import numpy as np

"""
    In memory reference to a prerecord emissions table. The emissions table is specified in:
    './Resources/Emissions/emissions_<electronic_valve_name>..._<electronic_valve_name>.csv'
"""


class EmissionsTable:

    def __init__(self, file_path):
        self.table = self._parse_emissions_table(file_path)

    @staticmethod
    def _parse_emissions_table(path) -> pd.DataFrame:
        df = pd.read_csv(path, sep='\s+').set_index('p')
        return df

    def _linear_interpolate(self, inlet_pressure, valve_states):
        next_row = np.searchsorted(self.table.index, inlet_pressure)
        previous_row = next_row - 1
        next_index = self.table.index[next_row]
        previous_index = self.table.index[previous_row]
        next_value = self.table.loc[next_index, valve_states]
        previous_value = self.table.loc[previous_index, valve_states]
        linear_slope = (next_value - previous_value) / (next_index - previous_index)
        linear_offset = (next_value - linear_slope * next_index)
        return linear_slope * inlet_pressure + linear_offset

    def get_emissions(self, inlet_pressure, valve_states) -> float:
        try:
            return self.table.loc[inlet_pressure, valve_states]
        except KeyError:
            # if it's not in the table we need to interpolate it
            return self._linear_interpolate(inlet_pressure, valve_states)