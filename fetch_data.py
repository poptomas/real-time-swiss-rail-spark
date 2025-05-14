from datetime import datetime
import requests
import pandas as pd
import streamlit as st


class SBBStationboardFetcher:
    BASE_URL = "https://transport.opendata.ch/v1/stationboard"
    LIMIT = 20

    def __init__(self, station_name):
        self.station_name = station_name
        self.raw_data = None

    def fetch(self):
        # Delegate to cached static method
        data, error = self._get_cached_data(self.station_name, self.LIMIT)
        if error or data is None:
            return pd.DataFrame(), None, error

        self.raw_data = data
        parsed_df = self._parse_stationboard(data)
        return parsed_df, data, None

    @staticmethod
    @st.cache_data(ttl=60)
    def _get_cached_data(station_name, limit):
        params = {
            "station": station_name,
            "limit": limit
        }
        response = requests.get(SBBStationboardFetcher.BASE_URL, params=params)
        if response.status_code != 200:
            return None, f"Error fetching data: {response.status_code}"
        return response.json(), None

    def _parse_stationboard(self, data):
        rows = []
        for entry in data.get("stationboard", []):
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

        return pd.DataFrame(rows)


def fetch_info(station_name):
    fetcher = SBBStationboardFetcher(station_name)
    return fetcher.fetch()
