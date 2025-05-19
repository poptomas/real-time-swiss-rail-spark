import folium
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import math
from branca.colormap import LinearColormap
from functools import lru_cache
import streamlit as st


API_KEY = "fd958bd8542a4d2f80e81546ebd00507"
#tile_layer = "https://{s}.tile.thunderforest.com/spinal-map/{z}/{x}/{y}{r}.png?apikey=fd958bd8542a4d2f80e81546ebd00507"
tile_layer="https://tile.osm.ch/switzerland/{z}/{x}/{y}.png"
attribution ="<a href=https://static1.thegamerimages.com/wordpress/wp-content/uploads/2025/02/kingdomcomedeliverance2henrymeme-1.jpg?q=70&fit=crop&w=1140&h=&dpr=1/>Click me</a>"

map_layer = folium.TileLayer(tiles=tile_layer, attr=attribution, name="diablo tiles")

def weight_to_color(weight, max_weight):
    cmap = plt.get_cmap("RdYlGn_r")  # back to original for edge coloring
    norm_ratio = np.sqrt(weight / max_weight)
    norm_ratio = min(max(norm_ratio, 0), 1)
    rgba = cmap(norm_ratio)
    dark_factor = 0.9
    dark_rgba = tuple(channel * dark_factor for channel in rgba[:3])
    return f"#{int(dark_rgba[0]*255):02x}{int(dark_rgba[1]*255):02x}{int(dark_rgba[2]*255):02x}"


class SBBMapRenderer:
    def __init__(self, graph: nx.Graph):
        self.graph = graph

    def render_map(self, center_lat=46.8, center_lon=8.3, zoom_start=7):
        return self.render_map_up_to_step(step=None, center_lat=center_lat, center_lon=center_lon, zoom_start=zoom_start)

    @lru_cache(maxsize=2)
    def render_map_up_to_step(self, step=None, batch_size=500, center_lat=46.8, center_lon=8.3, zoom_start=7):
        fmap = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start,
                          #tiles="Stadia_StamenTonerLite", control_scale=True, prefer_canvas=True)
                          tiles=map_layer,
                          control_scale=True, prefer_canvas=True)

        max_weight = max((data.get("weight", 1) for _, _, data in self.graph.edges(data=True)), default=1)
        # DEBUG:
        # st.markdown(max_weight)
        sqrt = math.sqrt

        edge_batches = list(self._batch_edges(batch_size))
        total_steps = len(edge_batches) if step is None else step

        # Always render all nodes (stations)
        for node, data in self.graph.nodes(data=True):
            lat = data.get("lat")
            lon = data.get("lon")
            name = data.get("name", str(node))
            if lat is not None and lon is not None:
                folium.CircleMarker(
                    location=(lat, lon),
                    radius=4,
                    color="black",
                    fill=True,
                    fill_color="white",
                    fill_opacity=1,
                    tooltip=folium.Tooltip(f"<b>{name}</b><br>Lat: {lat:.4f}<br>Lon: {lon:.4f}", sticky=True),
                    popup=folium.Popup(name, parse_html=True)
                ).add_to(fmap)

        for i, batch in enumerate(edge_batches):
            if i >= total_steps:
                break
            for u, v, edge_data in batch:
                u_data = self.graph.nodes[u]
                v_data = self.graph.nodes[v]
                if all(k in u_data for k in ("lat", "lon")) and all(k in v_data for k in ("lat", "lon")):
                    weight = edge_data.get("weight", 1)
                    if weight < 0.01 * max_weight:
                        continue
                    color = weight_to_color(weight, max_weight)
                    line_weight = 1 + 5 * sqrt(weight / max_weight)  # more visible difference
                    folium.PolyLine(
                        locations=[(u_data["lat"], u_data["lon"]), (v_data["lat"], v_data["lon"])],
                        weight=line_weight,
                        color=color,
                        opacity=0.7
                    ).add_to(fmap)

        self._add_colormap_legend(fmap, max_weight)
        return fmap

    def _batch_edges(self, batch_size):
        edges = list(self.graph.edges(data=True))
        for i in range(0, len(edges), batch_size):
            yield edges[i:i+batch_size]

    def _add_colormap_legend(self, fmap, max_weight):

        colormap = LinearColormap(
            colors=["#006837", "#ffffbf", "#a50026"],  # inverted for legend only
            vmin=1,
            vmax=max_weight,
            caption="Railway used today"
        )

        thresholds = np.linspace(1, max_weight, num=11)
        colormap = colormap.to_step(index=thresholds)
        colormap.add_to(fmap)