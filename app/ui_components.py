from streamlit_folium import st_folium
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from fetch_data import fetch_info
import datetime
import pandas as pd
from zoneinfo import ZoneInfo
import time


class SBBAppUI:
    REFRESH_INTERVAL_MS = 60 * 1000  # 60 seconds

    def __init__(self, renderer):
        self.renderer = renderer
        self.initialize_state()

    def initialize_state(self):
        if "render_step" not in st.session_state:
            st.session_state["render_step"] = 1
        else:
            st.session_state["render_step"] += 1

        if "last_station" not in st.session_state:
            st.session_state["last_station"] = "Basel SBB"
        if "last_fetch_time" not in st.session_state:
            st.session_state["last_fetch_time"] = 0
        if "stationboard_data" not in st.session_state:
            self.fetch_stationboard_data("Basel SBB")

    def fetch_stationboard_data(self, station):
        df, data, err = fetch_info(station)
        st.session_state["stationboard_data"] = df
        st.session_state["stationboard_error"] = err
        st.session_state["last_fetch_time"] = time.time()

    def render(self):
        # Autorefresh every 60 seconds
        st_autorefresh(interval=self.REFRESH_INTERVAL_MS, key="stationboard_autorefresh")

        st.title("SBB Rail Network")
        st.markdown("Explore the usage of the SBB rail network. Data is fetched in real-time from the Transport Data API.")
        st.markdown("Click on a station to see more information about its departures.")
        st.markdown("The map is updated automatically every single day, the data is fetched every minute.")

        col1, col2 = st.columns([2, 1])

        with col1:
            self.render_map()

        with col2:
            self.render_stationboard()

    def render_map(self):
        st.subheader("Rail Network Usage Heatmap")
        with st.spinner("Loading Map..."):
            fmap = self.renderer.render_map_up_to_step(step=st.session_state["render_step"], batch_size=4096)
            self.map_data = st_folium(fmap, width=1280, height=720)

    def render_stationboard(self):
        st.subheader("Stationboard Info")

        clicked_station = self.map_data.get("last_object_clicked_popup") or st.session_state.get("last_station", "Basel SBB")
        self.fetch_stationboard_data(clicked_station)

        df_stationboard = st.session_state.get("stationboard_data")
        err = st.session_state.get("stationboard_error")

        if err:
            st.error(err)
        elif df_stationboard is not None:
            st.subheader(f"Departures from {clicked_station}")
            st.dataframe(df_stationboard)

        last_updated = datetime.datetime.fromtimestamp(
            st.session_state.get("last_fetch_time", time.time()), tz=ZoneInfo("Europe/Zurich")
        ).strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"Last updated at: {last_updated}")


def render_ui(renderer):
    app = SBBAppUI(renderer)
    app.render()
