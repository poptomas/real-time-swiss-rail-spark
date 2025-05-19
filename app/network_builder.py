import networkx as nx
import pandas as pd
import streamlit as st


class SBBNetworkBuilder:
    def __init__(self, df: pd.DataFrame, didok: pd.DataFrame):
        self.df = df.sort_values(["FAHRT_BEZEICHNER", "ABFAHRTSZEIT"])
        # Pre-index station metadata for fast lookup
        self.didok_lookup = didok.set_index("number")[["wgs84North", "wgs84East"]].to_dict("index")

    def build_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        all_groups = self.df.groupby("FAHRT_BEZEICHNER")

        for fahrt_id, group in all_groups:
            group = group.dropna(subset=["HALTESTELLEN_NAME", "BPUIC", "ABFAHRTSZEIT"])
            rows = list(group.itertuples(index=False))
            for i in range(1, len(rows)):
                prev, curr = rows[i - 1], rows[i]

                from_station = prev.HALTESTELLEN_NAME
                to_station = curr.HALTESTELLEN_NAME

                # Skip if station names are still malformed
                if not isinstance(from_station, str) or not isinstance(to_station, str):
                    continue

                from_meta = self.didok_lookup.get(prev.BPUIC)
                to_meta = self.didok_lookup.get(curr.BPUIC)

                if not from_meta or not to_meta:
                    continue

                # Add nodes with geo attributes
                G.add_node(from_station, name=from_station,
                        lat=from_meta["wgs84North"], lon=from_meta["wgs84East"])
                G.add_node(to_station, name=to_station,
                        lat=to_meta["wgs84North"], lon=to_meta["wgs84East"])

                # Add or update edge with weight
                current_weight = G[from_station][to_station]["weight"] if G.has_edge(from_station, to_station) else 0
                G.add_edge(from_station, to_station, weight=int(current_weight) + 1)

        return G
