from graph_engine import G


# =========================================================
# FIND ALL MEDICINE PAIRS THAT SHARE BIOLOGICAL TARGETS
# =========================================================

drug_nodes = [
    node
    for node, data in G.nodes(data=True)
    if data.get("type") == "drug"
]

connected_pairs = []


# Compare every pair of medicines
for i in range(len(drug_nodes)):

    for j in range(i + 1, len(drug_nodes)):

        drug_a = drug_nodes[i]
        drug_b = drug_nodes[j]

        # Get biological targets of Drug A
        targets_a = {
            neighbour
            for neighbour in G.neighbors(drug_a)
            if G.nodes[neighbour].get("type") == "target"
        }

        # Get biological targets of Drug B
        targets_b = {
            neighbour
            for neighbour in G.neighbors(drug_b)
            if G.nodes[neighbour].get("type") == "target"
        }

        # Find shared biological targets
        shared_targets = targets_a.intersection(targets_b)

        if shared_targets:

            connected_pairs.append({
                "drug_a_id": drug_a,
                "drug_a_name": G.nodes[drug_a].get("name"),

                "drug_b_id": drug_b,
                "drug_b_name": G.nodes[drug_b].get("name"),

                "shared_targets": list(shared_targets),

                "shared_target_count": len(shared_targets)
            })


# =========================================================
# SORT PAIRS
# =========================================================

connected_pairs.sort(
    key=lambda pair: pair["shared_target_count"],
    reverse=True
)


# =========================================================
# PRINT TOP 20 PAIRS
# =========================================================

print()
print("MEDGRAPH - MEDICINE PAIRS WITH SHARED TARGETS")
print("================================================")

for pair in connected_pairs[:20]:

    print()

    print(
        pair["drug_a_name"],
        "+",
        pair["drug_b_name"]
    )

    print(
        "Shared biological targets:",
        pair["shared_target_count"]
    )

    for target_id in pair["shared_targets"]:

        target_name = G.nodes[target_id].get("name")

        print(
            "   ->",
            target_name,
            f"({target_id})"
        )


# =========================================================
# TOTAL
# =========================================================

print()
print("========================================")

print(
    "Total connected medicine pairs:",
    len(connected_pairs)
)