import os
import pickle
import streamlit as st
from data_loader import PandasSBBDataLoader, SparkSBBDataLoader
from network_builder import SBBNetworkBuilder


GRAPH_CACHE_PATH = "cached_graph.pkl"

def load_or_build_graph():
    if os.path.exists(GRAPH_CACHE_PATH):
        with open(GRAPH_CACHE_PATH, "rb") as f:
            return pickle.load(f)

    # Build graph from scratch
    data_loader = PandasSBBDataLoader()
    df = data_loader.load_istdaten("./data/2025-05-05_istdaten.csv")
    didok = data_loader.load_didok(
        "./data/actual_date-world-traffic_point-2025-05-12.csv",
        valid_bpuics=df["BPUIC"].unique()
    )
    builder = SBBNetworkBuilder(df, didok)
    G = builder.build_graph()

    # Save for future use
    with open(GRAPH_CACHE_PATH, "wb") as f:
        pickle.dump(G, f)

    return G