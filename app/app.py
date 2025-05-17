import argparse
from map_renderer import SBBMapRenderer  # This is your Folium-based renderer
from load_graph import load_or_build_graph
from ui_components import render_ui
from data_loader import SparkSBBDataLoader, PandasSBBDataLoader
import streamlit as st
st.set_page_config(layout="wide")

loader = PandasSBBDataLoader()

G = load_or_build_graph(loader)
renderer = SBBMapRenderer(G)
render_ui(renderer)