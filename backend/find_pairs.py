from graph_engine import GRAPH


print("\nMedGraph - Supported Medicine Pairs")
print("-----------------------------------")

found = 0

drug_nodes = [
    node
    for node, data in GRAPH.nodes(data=True)
    if data.get("node_type") == "drug"
]

for i in range(len(drug_nodes)):
    for j in range(i + 1, len(drug_nodes)):

        drug_a = drug_nodes[i]
        drug_b = drug_nodes[j]

        targets_a = set(GRAPH.neighbors(drug_a))
        targets_b = set(GRAPH.neighbors(drug_b))

        shared = targets_a.intersection(targets_b)

        if shared:

            a = GRAPH.nodes[drug_a]
            b = GRAPH.nodes[drug_b]

            target_names = [
                GRAPH.nodes[target].get("name")
                for target in shared
            ]

            print()
            print(
                f"{a.get('name')} ({a.get('id')})"
            )
            print(
                f"   <--> {b.get('name')} ({b.get('id')})"
            )
            print(
                f"   Shared target(s): "
                f"{', '.join(target_names)}"
            )

            found += 1

            if found == 10:
                break

    if found == 10:
        break


if found == 0:
    print("No shared-target medicine pairs found.")