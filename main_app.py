import streamlit as st
from data_loader import PandasSBBDataLoader, SparkSBBDataLoader
from network_builder import SBBNetworkBuilder
from map_renderer import SBBMapRenderer  # This is your Folium-based renderer
from streamlit_folium import st_folium
from graph_filter import GraphFilter
import requests
import pandas as pd

def fetch_info(station_name):
    url = f"https://transport.opendata.ch/v1/stationboard"
    params = {
        "station": station_name,
        "limit": 10  # or more
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return pd.DataFrame(), f"Error fetching data: {response.status_code}"

    data = response.json()
    if "stationboard" not in data:
        return pd.DataFrame(), "No stationboard data available."

    departures = []
    for entry in data["stationboard"]:
        dep = entry.get("stop", {}).get("departure", "")
        to = entry.get("to", "")
        cat = entry.get("category", "")
        number = entry.get("number", "")
        operator = entry.get("operator", "")
        departures.append({
            "Time": dep,
            "To": to,
            "Category": cat,
            "Number": number,
            "Operator": operator,
        })

    return pd.DataFrame(departures), None

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

col1, col2 = st.columns([2, 1])  # Map takes 2/3 of the width, table 1/3

print(col1)
print(col2)

# Display map
#st.subheader("📍 Swiss Train Network Map")
overlay_css = "#<style> \
#.leaflet-container {\
#    filter: brightness(0.8) contrast(1.1) opacity(0.8);\
#}\
#</style>"
with col1:
    st.subheader("📍 Swiss Train Network Map")
    st.markdown(overlay_css, unsafe_allow_html=True)
    map_data = st_folium(fmap, width=900, height=700)

with col2:
    st.subheader("📋 Stationboard Information")
    clicked_station = None
    with open("debug_file.txt", "a") as file:
        if map_data and map_data.get("last_object_clicked_popup"):
            clicked_station = map_data["last_object_clicked_popup"]
            file.write(f"last clicked: {map_data}")
            file.write(f"last clicked: {map_data["last_object_clicked_popup"]}")
        if clicked_station:
            st.success(f"📍 Selected Station: {clicked_station}")
            df_stationboard, err = fetch_info(clicked_station)
            if err:
                file.write(err)
                st.error(err)
            else:
                file.write(df.to_string())
                st.dataframe(df_stationboard)
#st.markdown(overlay_css, unsafe_allow_html=True)
#st_folium(fmap, width=1280, height=768)