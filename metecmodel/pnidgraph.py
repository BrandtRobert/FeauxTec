from metecmodel.graphparser import PnIDParser
from metecmodel.emissionstable import EmissionsTable
from metecmodel.component import Component
from typing import List, Tuple
import networkx as nx

"""
    Graph representation of the pnid system. Supports modification of valve states and calculation of emissions
    for GSH-1.CB-1W.
"""


class PnIdGraph:

    '''
        Parameters:
            volumes_file: a json file specifying the components and volumes in the system
                an example is found in ../Resources/volumes_CB_1W.json
            inlet_pressure: the pressure of gas following into the entry point of this gas system (in PSI)
            site_properties: other properties that may pertain to the system. One example is temperature.
    '''
    def __init__(self, volumes_file, inlet_pressure, site_properties={}):
        self.inlet_pressure = inlet_pressure
        self.site_properties = site_properties
        self.graph, self.components = self._init_graph(volumes_file) # relies on pressure and site props

    '''
        Creates the graph from a volumes file using the PnIDParser.
        Components retrieved from PnIDParser.read_json become nodes of the nx graph by using the full name of
        the device, for example: CB-1W.PT-1 and the component itself as an attribute of the node.
        Then the _add_edges method is called to link together nodes based on their current states and
        neighbors.
    '''
    def _init_graph(self, volumes_file) -> (nx.Graph, List[Component]):
        components: List = PnIDParser(volumes_file).read_json()
        # add ambient readings to our gauges
        for component in components:
            # PT is our pnid model tag for pressure transducer
            if component.get_type() == 'pressure-transducer':
                component.data['reading'] = self.inlet_pressure
            # TC is the model tag for thermocouple
            if component.get_type() == 'thermocouple':
                component.data['reading'] = self.site_properties.get('ambient_temperature', 0)
        nx_graph = nx.Graph()
        list(map(lambda comp: nx_graph.add_node(comp.get_full_name(), component=comp), components))
        PnIdGraph._add_edges(nx_graph, components)
        return nx_graph, components

    '''
        Adds edges to the graph by calling the get_current_neighbors on the component. This function
        determines current neighboring nodes based on the volumes json and the current state of the component.
    '''
    @staticmethod
    def _add_edges(nx_graph, components) -> None:
        for component in components:
            # Don't let volumes draw edges since they will connect to closed valves
            if component.get_type() == 'gas-volume':
                continue
            for neighbor in component.get_current_neighbors():
                nx_graph.add_edge(component.get_full_name(), neighbor)

    '''
        Is there a path between the two nodes, such that gas could flow?
    '''
    def are_connected(self, node_a: str, node_b: str) -> bool:
        self.graph.has_path(node_a, node_b)


    @staticmethod
    def _get_downstream_volume(component) -> Component:
        neighbors = component.get_current_neighbors()
        for n in neighbors:
            if component.get_type() == 'gas-volume':
                return n

    '''
        Gets the states of the electronic valves for this controller box.
        The valves are returned as a binary style string such that each valve
        is either 0 or 1 in the string depending on whether it is open or closed.
        For example: 
            EV_14 --> open
            EV_15 --> open
            EV_16 --> closed
            gives the string '110'
        
        This method is very specific to the 3 x 4 valve system.
        It relies on the fact that valves from the same group will have similar
        suffixes. For example: valves EV_14, and EV_15 are on the same line while 
        valves EV_24 and EV_25 on a line different from the previous two.
    '''
    def _get_valve_states(self) -> List[Tuple[str, str]]:
        valves = {}
        for node in self.graph.nodes():
            try:
                # Will only grab 2-way valves
                if self.get_node_component(node).get_type() == 'electronic-valve':
                    component = self.get_node_component(node)
                    suffix = component.name.split('_')[1][0]
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
                # This line was intended to change the value of the downstream volume based
                # on which valves are open and the pressure upstream
                #   down_stream_vol = self._get_downstream_volume(valve)
            binary_str = ''.join(binary_str)
            valves[k] = (binary_str, data_file)
        return valves

    '''
        Get the emissions for certain points of the control box based on the current state of the valves.
        Uses a reference table resource for determining the output based on the inlet pressure and valve states.
    '''
    def get_emissions(self) -> List[float]:
        valves: dict = self._get_valve_states()
        emissions_lookup = []
        for k, v in valves.items():
            valve_states, data_file = v
            emissions_lookup.append(EmissionsTable('../Resources/' + data_file)
                                    .get_emissions(self.inlet_pressure, valve_states))
        return emissions_lookup

    '''
        Handles the side effects of manipulating a nodes state. Mainly it's relevant for valves, as when they
        change state the path that gas can flow also changes. This method removes all current edges for the specified
        node and redraws new edges based on the nodes new state. 
    '''
    def change_node_state(self, node, new_state) -> None:
        current_component = self.get_node_component(node)
        current_neighbors = current_component.get_current_neighbors()
        for neighbor in current_neighbors:
            self.graph.remove_edge(current_component.get_full_name(), neighbor)
        current_component.current_state = new_state
        new_neighbors = current_component.get_current_neighbors()
        for neighbor in new_neighbors:
            self.graph.add_edge(current_component.get_full_name(), neighbor)

    '''
        Returns the component for a given node in the graph based on the fullname of that component.
        Allows you to look up properties by component name.
    '''
    def get_node_component(self, node) -> Component:
        return self.graph.node[node]['component']


'''
    Test main method
'''
if __name__ == "__main__":
    model = PnIdGraph('../Resources/volumes_CB_1W.json', 50)
    print(model.get_node_component('CB_1W.PT_1'))
    model.change_node_state('CB_1W.EV_12', 'closed')
    model.change_node_state('CB_1W.EV_23', 'closed')
    print(model.get_emissions())
