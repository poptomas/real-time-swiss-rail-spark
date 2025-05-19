import os
import shutil
import pickle
import requests
import zipfile
from datetime import datetime, timedelta
import streamlit as st
import networkx as nx
from data_loader import AbstractSBBDataLoader, SparkSBBDataLoader
from network_builder import SBBNetworkBuilder


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
            st.markdown(f"Latest dataset CSV already exists: {csv_path}")
            return csv_path, False

        file_path = os.path.join(self.data_dir, self.zip_filename)

        try:
            st.markdown(f"Downloading latest dataset from {self.base_url}")
            response = requests.get(self.base_url)
            response.raise_for_status()

            with open(file_path, "wb") as f:
                f.write(response.content)

            try:
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(self.data_dir)
                os.remove(file_path)
                st.markdown(f"Extracted and ready: {csv_path}")
                return csv_path, True
            except zipfile.BadZipFile:
                # Treat it as a CSV file with wrong extension
                corrected_path = file_path.replace(".zip", "")
                os.rename(file_path, corrected_path)
                st.markdown(f"Download was actually a CSV, renamed to: {corrected_path}")
                return corrected_path, True

        except Exception as e:
            st.error(f"Failed to fetch latest dataset ({e})")
            return None, False


def cleanup(data_dir: str):
    def delete_directory_contents(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # delete file or symlink
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    if os.path.exists(data_dir):
        delete_directory_contents(data_dir)


def load_or_build_graph(data_loader: AbstractSBBDataLoader):
    DATA_DIR = "/data" if isinstance(data_loader, SparkSBBDataLoader) else "./data"
    # cleanup(DATA_DIR)
    GRAPH_CACHE_PATH = os.path.join(DATA_DIR, "cached_graph.graphml")
    os.makedirs(DATA_DIR, exist_ok=True)

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
                st.markdown(f"Using fallback ISTDATEN file: {istdaten_csv_path}")
                break

    if not istdaten_csv_path or not os.path.exists(istdaten_csv_path):
        st.error("Could not fetch or locate ISTDATEN dataset.")
        return None

    if os.path.exists(GRAPH_CACHE_PATH) and not (stations_downloaded or istdaten_downloaded):
        st.markdown("Using cached graph.")
        return nx.read_graphml(GRAPH_CACHE_PATH)

    st.markdown("Rebuilding graph from scratch...")
    df = data_loader.load_istdaten(istdaten_csv_path)
    # DEBUG:
    #st.dataframe(df)
    if not stations_csv_path:
        st.error("Could not fetch or locate station metadata dataset.")
        return None

    stations = data_loader.load_didok(stations_csv_path, valid_bpuics=df["BPUIC"].unique())
    # DEBUG: 
    #st.dataframe(stations)
    builder = SBBNetworkBuilder(df, stations)
    G = builder.build_graph()

    nx.write_graphml(G, GRAPH_CACHE_PATH)
    st.markdown("Graph built and cached.")
    return G
