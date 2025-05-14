import os
import pickle
import requests
import zipfile
from datetime import datetime, timedelta
import streamlit as st

from data_loader import PandasSBBDataLoader, SparkSBBDataLoader
from network_builder import SBBNetworkBuilder

GRAPH_CACHE_PATH = "cached_graph.pkl"
DATA_DIR = "./data"


class RemoteCSVDownloader:
    def __init__(self, base_url: str, zip_template: str, data_dir: str, use_yesterday: bool = False):
        self.base_url = base_url
        self.zip_template = zip_template
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        date_obj = datetime.now() - timedelta(days=1) if use_yesterday else datetime.now()
        self.date_str = date_obj.strftime("%Y-%m-%d")
        self.zip_filename = self.zip_template.format(date=self.date_str)
        self.csv_filename = self.zip_filename.replace(".zip", "")

    def get_local_csv_path(self) -> str:
        return os.path.join(self.data_dir, self.csv_filename)

    def ensure_latest_csv_available(self) -> (str, bool):
        csv_path = self.get_local_csv_path()
        if os.path.exists(csv_path):
            print(f"Latest dataset CSV already exists: {csv_path}")
            return csv_path, False

        file_path = os.path.join(self.data_dir, self.zip_filename)

        try:
            print(f"Downloading latest dataset from {self.base_url}")
            response = requests.get(self.base_url)
            response.raise_for_status()

            with open(file_path, "wb") as f:
                f.write(response.content)

            # Check if the downloaded file is actually a zip or mislabeled CSV
            try:
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(self.data_dir)
                os.remove(file_path)
                print(f"Extracted and ready: {csv_path}")
                return csv_path, True
            except zipfile.BadZipFile:
                # Treat it as a CSV file with wrong extension
                corrected_path = file_path.replace(".zip", "")
                os.rename(file_path, corrected_path)
                print(f"Download was actually a CSV, renamed to: {corrected_path}")
                return corrected_path, True

        except Exception as e:
            print(f"Failed to fetch latest dataset ({e})")
            return None, False


def load_or_build_graph():
    stations_downloader = RemoteCSVDownloader(
        base_url="https://data.opentransportdata.swiss/en/dataset/traffic-points-actual-date/permalink",
        zip_template="actual_date-world-traffic_point-{date}.csv.zip",
        data_dir=DATA_DIR,
        use_yesterday=False
    )
    ist_downloader = RemoteCSVDownloader(
        base_url="https://data.opentransportdata.swiss/en/dataset/istdaten/permalink",
        zip_template="{date}_istdaten.csv.zip",
        data_dir=DATA_DIR,
        use_yesterday=True
    )

    stations_csv_path, stations_downloaded = stations_downloader.ensure_latest_csv_available()
    istdaten_csv_path, istdaten_downloaded = ist_downloader.ensure_latest_csv_available()

    # fallback to any local ISTDATEN CSV file if download failed
    if istdaten_csv_path is None:
        for f in sorted(os.listdir(DATA_DIR), reverse=True):
            if f.endswith("_istdaten.csv"):
                istdaten_csv_path = os.path.join(DATA_DIR, f)
                print(f"Using fallback ISTDATEN file: {istdaten_csv_path}")
                break

    if not istdaten_csv_path or not os.path.exists(istdaten_csv_path):
        st.error("Could not fetch or locate ISTDATEN dataset.")
        return None

    if os.path.exists(GRAPH_CACHE_PATH) and not (stations_downloaded or istdaten_downloaded):
        with open(GRAPH_CACHE_PATH, "rb") as f:
            print("Using cached graph.")
            return pickle.load(f)

    print("Rebuilding graph from scratch...")
    data_loader = PandasSBBDataLoader()
    df = data_loader.load_istdaten(istdaten_csv_path)

    if not stations_csv_path:
        st.error("Could not fetch or locate station metadata dataset.")
        return None

    stations = data_loader.load_didok(stations_csv_path, valid_bpuics=df["BPUIC"].unique())
    builder = SBBNetworkBuilder(df, stations)
    G = builder.build_graph()

    with open(GRAPH_CACHE_PATH, "wb") as f:
        pickle.dump(G, f)

    print("Graph built and cached.")
    return G