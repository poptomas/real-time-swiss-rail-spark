import networkx as nx
import pandas as pd


class SBBNetworkBuilder:
    def __init__(self, df: pd.DataFrame, didok: pd.DataFrame):
        self.df = df.sort_values(["FAHRT_BEZEICHNER", "ABFAHRTSZEIT"])
        # Pre-index station metadata for fast lookup
        self.didok_lookup = didok.set_index("number")[["wgs84North", "wgs84East"]].to_dict("index")

    def build_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()

        for fahrt_id, group in self.df.groupby("FAHRT_BEZEICHNER"):
            group = group.dropna(subset=["HALTESTELLEN_NAME", "ABFAHRTSZEIT"])

            rows = list(group.itertuples(index=False))
            for i in range(1, len(rows)):
                prev, curr = rows[i - 1], rows[i]

                from_station = prev.HALTESTELLEN_NAME
                to_station = curr.HALTESTELLEN_NAME

                from_meta = self.didok_lookup.get(prev.BPUIC)
                to_meta = self.didok_lookup.get(curr.BPUIC)

                if not from_meta or not to_meta:
                    continue

                # Add nodes with geo attrs
                G.add_node(from_station, name=from_station,
                           lat=from_meta["wgs84North"], lon=from_meta["wgs84East"])
                G.add_node(to_station, name=to_station,
                           lat=to_meta["wgs84North"], lon=to_meta["wgs84East"])

                # Increment edge weight
                if G.has_edge(from_station, to_station):
                    G[from_station][to_station]["weight"] += 1
                else:
                    G.add_edge(from_station, to_station, weight=1)

        return G
