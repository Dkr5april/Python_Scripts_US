import networkx as nx

# 1. Create the Graph and add a lot more data (Starting to get messy)
B = nx.DiGraph()

edges = [
    ("Sun", "Simha", "RULES"),
    ("Sun", "Father", "IS_KARAKA_FOR"),
    ("Sun", "Government", "IS_KARAKA_FOR"),
    ("Sun", "Soul", "IS_KARAKA_FOR"),
    ("Jupiter", "Dhanus", "RULES"),
    ("Jupiter", "Meena", "RULES"),
    ("Jupiter", "Children", "IS_KARAKA_FOR"),
    ("Jupiter", "Wealth", "IS_KARAKA_FOR"),
    ("5th House", "Intelligence", "SIGNIFIES"),
    ("5th House", "Children", "SIGNIFIES"),
]

for source, target, relation in edges:
    B.add_edge(source, target, relation=relation)

# 2. THE SOLUTION: Instead of drawing it, we QUERY it programmatically!

print("--- ORBITING THE SUN ---")
# Find everything directly connected to the Sun
sun_connections = list(B.successors("Sun"))
print(f"The Sun is directly connected to: {sun_connections}")

print("\n--- FINDING MEANINGS ---")
# Ask the database: What specifically is Jupiter a karaka for?
jupiter_karakas = [
    target
    for source, target, rel in B.edges(data="relation")
    if source == "Jupiter" and rel == "IS_KARAKA_FOR"
]
print(f"Jupiter is the Karaka for: {jupiter_karakas}")

print("\n--- CROSS-REFERENCING (The Power of Graphs) ---")
# Find what connects BOTH the 5th House and Jupiter
# (This is how you will eventually find Yogas automatically!)
shared = set(B.successors("5th House")).intersection(set(B.successors("Jupiter")))
print(f"The common factor between 5th House and Jupiter is: {list(shared)}")