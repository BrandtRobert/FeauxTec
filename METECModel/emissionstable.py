import pandas as pd


class EmissionsTable:

    def __init__(self, file_path):
        self.table = self._parse_emissions_table(file_path)

    def _parse_emissions_table(self, path):
        df = pd.read_csv(path, sep='\s+').set_index('p')
        return df

    def get_emissions(self, inlet_pressure, valve_states):
        return self.table.loc[inlet_pressure, valve_states]