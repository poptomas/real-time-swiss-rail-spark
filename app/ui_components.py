from streamlit_folium import st_folium
import streamlit as st
from fetch_data import fetch_info
import time
import datetime


class SBBAppUI:
    REFRESH_INTERVAL = 60

    def __init__(self, renderer):
        self.renderer = renderer
        self.now = time.time()
        self.initialize_state()

    def initialize_state(self):
        if "render_step" not in st.session_state:
            st.session_state["render_step"] = 1
        else:
            st.session_state["render_step"] += 1

        if "last_station" not in st.session_state:
            st.session_state["last_station"] = None
        if "last_fetch_time" not in st.session_state:
            st.session_state["last_fetch_time"] = 0
        if "stationboard_data" not in st.session_state:
            st.session_state["stationboard_data"] = None
            st.session_state["stationboard_error"] = None

    def render(self):
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
        fmap = self.renderer.render_map_up_to_step(step=st.session_state["render_step"], batch_size=2000)
        self.map_data = st_folium(fmap, width=1280, height=720)

    def render_stationboard(self):
        st.subheader("Stationboard Info")

        clicked_station = self.map_data.get("last_object_clicked_popup") or st.session_state.get("last_station") or "Basel SBB"
        print(clicked_station)
        time_since_last_fetch = self.now - st.session_state["last_fetch_time"]
        station_changed = clicked_station != st.session_state["last_station"]

        if station_changed or time_since_last_fetch >= self.REFRESH_INTERVAL:
            st.session_state["last_station"] = clicked_station
            with st.spinner(f"Fetching departures for {clicked_station}..."):
                df_stationboard, data, err = fetch_info(clicked_station)
                st.session_state["stationboard_data"] = df_stationboard
                st.session_state["stationboard_error"] = err
                st.session_state["stationboard_json"] = data
                st.session_state["last_fetch_time"] = self.now

        df_stationboard = st.session_state["stationboard_data"]
        err = st.session_state["stationboard_error"]
        data = st.session_state["stationboard_json"]
        if err:
            st.error(err)
        elif df_stationboard is not None:
            st.subheader(f"Departures from {clicked_station}")
            st.dataframe(df_stationboard)
            # DEBUG: st.json(data, expanded=False)

        last_updated = datetime.datetime.fromtimestamp(st.session_state["last_fetch_time"]).strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"Last updated at: {last_updated}")


def render_ui(renderer):
    app = SBBAppUI(renderer)
    app.render()