import networkx as nx


class GraphFilter:
    @staticmethod
    def filter_nodes_by_name(graph: nx.Graph, search_query: str) -> nx.Graph:
        if not search_query:
            return graph

        query = search_query.strip().lower()
        matching_nodes = {
            node for node, data in graph.nodes(data=True)
            if query in data.get("name", "").lower()
        }

        return graph.subgraph(matching_nodes).copy()
