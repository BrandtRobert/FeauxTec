import networkx as nx


class PNIDGraph:

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node_name, neighbors):
        self.graph.add_node(node_name)
        # make sure that flow is one way through flow meters
        if 'FM' in node_name:
            list(neighbors).sort()
            self.graph.add_edge(neighbors[0], node_name)
            self.graph.add_edge(node_name, neighbors[1])
        elif 'VOL' not in node_name:
            for n in neighbors:
                self.graph.add_edge(node_name, n)
                # self.graph.add_edge(n, node_name)

    def are_connected(self, a, b):
        try:
            return nx.has_path(self.graph, a, b)
        except nx.exception.NodeNotFound:
            return False

    def redraw_edges(self, node_name, new_neighbors):
        for edge in list(self.graph.edges(node_name)):
            v = edge[1]
            self.graph.remove_edge(node_name, v)
        for n in new_neighbors:
            self.graph.add_edge(node_name, n)
            self.graph.add_edge(n, node_name)

    def save_graph(self, graph_file):
        # nx.write_graphml(self.graph, graph_file)
        nx.write_gml(self.graph, graph_file)