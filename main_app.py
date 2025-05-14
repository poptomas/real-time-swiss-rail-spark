from map_renderer import SBBMapRenderer  # This is your Folium-based renderer
from load_graph import load_or_build_graph
from ui_components import render_ui

G = load_or_build_graph()
renderer = SBBMapRenderer(G)
render_ui(renderer)
