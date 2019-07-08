import pandas as pd

"""
    In memory reference to a prerecord emissions table. The emissions table is specified in:
    './Resources/CB_1W/emissions_<electronic_valve_name>..._<electronic_valve_name>.csv'
"""


class EmissionsTable:

    def __init__(self, file_path):
        self.table = self._parse_emissions_table(file_path)

    @staticmethod
    def _parse_emissions_table(path) -> pd.DataFrame:
        df = pd.read_csv(path, sep='\s+').set_index('p')
        return df

    def get_emissions(self, inlet_pressure, valve_states) -> float:
        return self.table.loc[inlet_pressure, valve_states]