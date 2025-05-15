import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="Basel SBB Stationboard", layout="wide")
st.title("🚆 Basel SBB Stationboard")

REFRESH_INTERVAL = 60  # seconds

@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_stationboard():
    url = "http://transport.opendata.ch/v1/stationboard"
    params = {
        "station": "Basel SBB",
        "limit": 20
    }
    response = requests.get(url, params=params)
    data = response.json()

    rows = []
    for entry in data["stationboard"]:
        category = entry.get("category", "")
        number = entry.get("number", "")
        name = f"{category} {number}".strip()
        to = entry.get("to", "")
        stop = entry.get("stop", {})
        departure_raw = stop.get("departure", None)
        platform = stop.get("platform", "N/A")

        # Format departure time
        if departure_raw:
            try:
                departure_dt = datetime.strptime(departure_raw, "%Y-%m-%dT%H:%M:%S%z")
                departure = departure_dt.strftime("%d %b %Y, %H:%M")
            except Exception:
                departure = departure_raw
        else:
            departure = "N/A"

        rows.append({
            "Train": name,
            "Destination": to,
            "Departure Time": departure,
            "Platform": platform
        })

    df = pd.DataFrame(rows)
    return df

# Display stationboard with auto-refresh
placeholder = st.empty()
countdown = st.empty()

while True:
    with placeholder.container():
        df = fetch_stationboard()
        st.subheader(f"Last updated at {pd.Timestamp.now().strftime('%H:%M:%S')}")
        st.dataframe(df, use_container_width=True)

    for remaining in range(REFRESH_INTERVAL, 0, -1):
        countdown.info(f"⏳ Refreshing in {remaining} seconds...")
        time.sleep(1)
    placeholder.empty()
    countdown.empty()
