import streamlit as st
from data_loader import PandasSBBDataLoader, SparkSBBDataLoader
from network_builder import SBBNetworkBuilder
from map_renderer import SBBMapRenderer  # This is your Folium-based renderer
from streamlit_folium import st_folium
from graph_filter import GraphFilter


st.set_page_config(layout="wide")
st.title("🚆 Swiss Train Network - Folium Map Viewer")

# Load data
data_loader = PandasSBBDataLoader()
df = data_loader.load_istdaten("./data/2025-05-05_istdaten.csv")
didok = data_loader.load_didok("./data/actual_date-world-traffic_point-2025-05-12.csv", valid_bpuics=df["BPUIC"].unique())

# Build network graph
builder = SBBNetworkBuilder(df, didok)
G = builder.build_graph()

# Add Sidebar Search
search_query = st.sidebar.text_input("🔍 Search Station Name (optional)", "")
filtered_G = GraphFilter.filter_nodes_by_name(G, search_query)

renderer = SBBMapRenderer(filtered_G)
fmap = renderer.render_map()

# Display map
st.subheader("📍 Swiss Train Network Map")
overlay_css = """
<style>
.leaflet-container {
    filter: brightness(0.8) contrast(1.1) opacity(0.8);
}
</style>
"""
st.markdown(overlay_css, unsafe_allow_html=True)
st_folium(fmap, width=1280, height=768)
