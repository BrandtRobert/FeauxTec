from METECModel.pnidparser import PnIDParser
from METECModel.emissionstable import EmissionsTable
from typing import List
import networkx as nx


class PnIDModel:
    def __init__(self, volumes_file):
        self.graph, self.components = self._init_graph(volumes_file)

    @staticmethod
    def _init_graph(volumes_file):
        components: List = PnIDParser(volumes_file).read_json()
        nx_graph = nx.Graph()
        list(map(lambda comp: nx_graph.add_node(comp.get_full_name(), component=comp), components))
        PnIDModel._add_edges(nx_graph, components)
        return nx_graph, components

    @staticmethod
    def _add_edges(nx_graph, components):
        for component in components:
            # Don't let volumes draw edges since they will connect to closed valves
            if "VOL" in component.name:
                continue
            for neighbor in component.get_current_neighbors():
                nx_graph.add_edge(component.get_full_name(), neighbor)

    def are_connected(self, node_a: str, node_b: str):
        self.graph.has_path(node_a, node_b)

    def _get_downstream_volume(self, component):
        neighbors = component.get_current_neighbors()
        for n in neighbors:
            if 'VOL' in n:
                return n

    def _get_valve_states(self):
        valves = {}
        for node in self.graph.nodes():
            try:
                if 'EV' in node:
                    component = self.get_node_component(node)
                    suffix = component.name.split('_')[1][0]
                    # Valve that doesn't have a binary pos (a number 4 valve)
                    if 'binary_string_pos' not in component.data:
                        continue
                    if suffix in valves:
                        valves[suffix].append(component)
                    else:
                        valves[suffix] = [component]
            except KeyError:
                print(node)

        for k, valve_list in valves.items():
            binary_str = ['0'] * 3
            for valve in valve_list:
                pos = valve.data['binary_string_pos']
                binary_str[pos] = '1' if valve.current_state == 'open' else '0'
                data_file = valve.data['data_table']
                down_stream_vol = self._get_downstream_volume(valve)
            binary_str = ''.join(binary_str)
            valves[k] = (binary_str, data_file)
        return valves

    def get_emissions(self, inlet_pressure):
        valves: dict = self._get_valve_states()
        emissions_lookup = []
        for k, v in valves.items():
            valve_states, data_file = v
            emissions_lookup.append(EmissionsTable('../Resources/' + data_file)
                                    .get_emissions(inlet_pressure, valve_states))
        return emissions_lookup

    def change_node_state(self, node, new_state):
        current_component = self.get_node_component(node)
        current_neighbors = current_component.get_current_neighbors()
        for neighbor in current_neighbors:
            self.graph.remove_edge(current_component.get_full_name(), neighbor)
        current_component.current_state = new_state
        new_neighbors = current_component.get_current_neighbors()
        for neighbor in new_neighbors:
            self.graph.add_edge(current_component.get_full_name(), neighbor)

    def get_node_component(self, node):
        return self.graph.node[node]['component']


if __name__ == "__main__":
    model = PnIDModel('../Resources/volumes_CB_1W.json')
    model.change_node_state('CB_1W.EV_12', 'closed')
    model.change_node_state('CB_1W.EV_23', 'closed')
    print(model.get_emissions(50))
