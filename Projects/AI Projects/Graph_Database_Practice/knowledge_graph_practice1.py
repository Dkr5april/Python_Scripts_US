import matplotlib.pyplot as plt
import networkx as nx

# 1. Initialize an empty Directed Graph
B = nx.DiGraph()

# 2. Add our static nodes (The Entities)
# We can give them a 'type' attribute to keep things organized
nodes = [
    ("Simha", {"type": "Rashi"}),
    ("Sun", {"type": "Graha"}),
    ("5th House", {"type": "Bhava"}),
    ("Father", {"type": "Signification"}),
    ("Intelligence", {"type": "Signification"}),
]
B.add_nodes_from(nodes)

# 3. Add our edges (The Karakatvas / Static Rules)
edges = [
    ("Sun", "Simha", "RULES"),
    ("Sun", "Father", "IS_KARAKA_FOR"),
    ("5th House", "Intelligence", "SIGNIFIES"),
]

# In networkx, we add relationships with a specific label
for source, target, relation in edges:
    B.add_edge(source, target, relation=relation)

# 4. Draw the Graph so you can see it
plt.figure(figsize=(8, 6))
pos = nx.spring_layout(B, seed=42)  # Layout for positioning nodes

# Draw nodes, edges, and text labels
nx.draw_networkx_nodes(B, pos, node_size=2000, node_color="skyblue")
nx.draw_networkx_labels(B, pos, font_size=10, font_weight="bold")
nx.draw_networkx_edges(
    B, pos, arrowstyle="->", arrowsize=20, edge_color="gray"
)

# Draw the relationship names (RULES, IS_KARAKA_FOR, etc.)
edge_labels = nx.get_edge_attributes(B, "relation")
nx.draw_networkx_edge_labels(B, pos, edge_labels=edge_labels, font_size=9)

plt.title("Your First Static Astrology Knowledge Graph", fontsize=14)
plt.axis("off")
plt.show()