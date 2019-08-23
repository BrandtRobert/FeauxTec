import networkx as nx
import json
from typing import Dict


class NetworkModel:

    def __init__(self, network_graph_path: str, labjacks: Dict):
        self.graph = nx.Graph()
        self.labjacks = labjacks
        self._add_nodes(network_graph_path)
        self.deleted_edges = []

    def _add_nodes(self, file):
        with open(file, 'r') as json_file:
            json_data = json.load(json_file)
            for item in json_data:
                node_name = item['name']
                neighbors = item['neighbors']
                for neighbor in neighbors:
                    self.graph.add_edge(node_name, neighbor)

    def disconnect_nodes(self, a, b):
        try:
            self.graph.remove_edge(a, b)
            self.deleted_edges.append((a, b))
            for _, labjack in self.labjacks.items():
                if not nx.has_path(self.graph, 'root', labjack.name):
                    labjack.inject_failures({'disconnected': True})
        except nx.NetworkXError:
            print('Edge does not exist')

    def network_connected(self, u, v):
        return nx.has_path(self.graph, u, v)

    def repair_edge(self, a, b):
        if (a, b) in self.deleted_edges:
            self.graph.add_edge(a, b)
            self.deleted_edges.remove((a, b))
            for _, labjack in self.labjacks.items():
                if nx.has_path(self.graph, 'root', labjack.name):
                    labjack.inject_failures({'disconnected': False})
        else:
            print('Edge was not previously removed')

    def reset_network(self):
        for edge in self.deleted_edges:
            self.repair_edge(*edge)
