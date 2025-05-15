from pyvis.network import Network
import networkx as nx


class SBBGraphRenderer:
    def __init__(self, graph: nx.Graph):
        self.graph = graph

    def render(self, output_file="train_network.html", geo_layout=True):
        net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black")

        for node, data in self.graph.nodes(data=True):
            label = data.get("name", str(node))
            lat = data.get("lat")
            lon = data.get("lon")

            if geo_layout and lat and lon:
                x = lon * 10000
                y = lat * -10000  # Flip to make north-up
                net.add_node(node, label=label, title=label, x=x, y=y, physics=False)
            else:
                net.add_node(node, label=label, title=label)

        for u, v, data in self.graph.edges(data=True):
            net.add_edge(u, v, title=f"{data.get('weight', 1)}x trips")

        net.toggle_physics(not geo_layout)
        net.write_html(output_file)
        return output_file
    