import folium
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import math


def weight_to_color(weight, max_weight):
    cmap = plt.get_cmap("RdYlGn_r")
    norm_ratio = np.sqrt(weight / max_weight)
    norm_ratio = min(max(norm_ratio, 0), 1)
    rgba = cmap(norm_ratio)

    # Ztmavení barvy
    dark_factor = 0.9  # čím menší, tím tmavší
    dark_rgba = tuple(channel * dark_factor for channel in rgba[:3])
    return f"#{int(dark_rgba[0]*255):02x}{int(dark_rgba[1]*255):02x}{int(dark_rgba[2]*255):02x}"


class SBBMapRenderer:
    def __init__(self, graph: nx.Graph):
        self.graph = graph

    def render_map(self, center_lat=46.8, center_lon=8.3, zoom_start=7):
        fmap = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start,
                          #tiles=" CartoDB_DarkMatter", control_scale=True)
                          tiles="Stadia_StamenTonerLite", control_scale=True)
                          #tiles="CartoDB_Positron", control_scale=True)

        # Calculate max weight for scaling
        max_weight = max((data.get("weight", 1) for _, _, data in self.graph.edges(data=True)), default=1)

        # Draw stations as points
        for node, data in self.graph.nodes(data=True):
            lat = data.get("lat")
            lon = data.get("lon")
            name = data.get("name", str(node))
            if lat is not None and lon is not None:
                folium.CircleMarker(
                    location=(lat, lon),
                    radius=2,
                    color="black",
                    fill=False,
                    fill_opacity=0.5,
                    tooltip=folium.Tooltip(
                        f"<b>{name}</b><br>Lat: {lat:.4f}<br>Lon: {lon:.4f}",
                        sticky=True
                    )
                ).add_to(fmap)

        # Draw edges with color and thickness scaled by weight
        for u, v, edge_data in self.graph.edges(data=True):
            u_data = self.graph.nodes[u]
            v_data = self.graph.nodes[v]
            if all(k in u_data for k in ("lat", "lon")) and all(k in v_data for k in ("lat", "lon")):
                weight = edge_data.get("weight", 1)
                color = weight_to_color(weight, max_weight)
                line_weight = 1 + 7 * math.sqrt(weight / max_weight)

                folium.PolyLine(
                    locations=[(u_data["lat"], u_data["lon"]), (v_data["lat"], v_data["lon"])],
                    weight=line_weight,
                    color=color,
                    opacity=0.6
                ).add_to(fmap)
        return fmap
