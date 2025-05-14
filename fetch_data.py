from datetime import datetime
import requests
import pandas as pd
import streamlit as st


@st.cache_data(ttl=60)
def fetch_info(station_name: str):
    url = "https://transport.opendata.ch/v1/stationboard"
    params = {
        "station": station_name,
        "limit": 20
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return pd.DataFrame(), f"Error fetching data: {response.status_code}"
    
    data = response.json()
    if "stationboard" not in data:
        return pd.DataFrame(), "No stationboard data available."

    rows = []
    for entry in data["stationboard"]:
        category = entry.get("category", "")
        number = entry.get("number", "")
        name = f"{category} {number}".strip()
        to = entry.get("to", "")
        stop = entry.get("stop", {})
        departure_raw = stop.get("departure", None)
        platform = stop.get("platform", "N/A")

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

    return pd.DataFrame(rows), None
