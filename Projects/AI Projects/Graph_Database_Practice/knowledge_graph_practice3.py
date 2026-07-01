import os
import networkx as nx
import pandas as pd


def build_knowledge_graph(csv_path):
    # 1. Initialize our Directed Graph
    G = nx.DiGraph()

    # Verify if file exists
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Please create the file first.")
        return None

    # 2. Read the flat data
    df = pd.read_csv(csv_path)

    # 3. Dynamically inject edges and properties into the graph topology
    for _, row in df.iterrows():
        G.add_edge(
            row["Source"],
            row["Target"],
            relation=row["Relationship"],
            category=row["Category"],
        )

    print(
        f"Successfully synchronized! Graph contains {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.\n"
    )
    return G


def query_astrology_engine(G):
    print("==================================================")
    print("          ASTROLOGY KNOWLEDGE ENGINE QUERY        ")
    print("==================================================\n")

    # Operation 1: Direct Successors (Out-neighbors)
    target_node = "Sun"
    if G.has_node(target_node):
        connections = list(G.successors(target_node))
        print(f"[DIRECT SUCCESSORS] Everything tied to {target_node}:")
        print(f"-> {connections}\n")

    # Operation 2: Relationship Edge Filtering
    print(f"[EDGE FILTERING] What is Jupiter explicitly a Karaka for?")
    jupiter_karakas = [
        target
        for source, target, data in G.edges(data=True)
        if source == "Jupiter" and data.get("relation") == "IS_KARAKA_FOR"
    ]
    print(f"-> {jupiter_karakas}\n")

    # Operation 3: Path Convergence (Set Intersection for Yogas/Combinations)
    print(f"[CROSS-REFERENCING] Finding overlap between 5th House & Jupiter:")
    if G.has_node("5th House") and G.has_node("Jupiter"):
        fifth_house_significations = set(G.successors("5th House"))
        jupiter_significations = set(G.successors("Jupiter"))

        shared_factors = fifth_house_significations.intersection(
            jupiter_significations
        )
        print(f"-> Connected via: {list(shared_factors)}\n")


# Run the engine
if __name__ == "__main__":
    # Path to your spreadsheet
    csv_file = "astrology_rules.csv"

    # Build and query
    astro_graph = build_knowledge_graph(csv_file)
    if astro_graph:
        query_astrology_engine(astro_graph)