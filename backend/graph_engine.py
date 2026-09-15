import json
import os
import networkx as nx


# =========================================================
# 1. LOCATE DATA FOLDER
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


# =========================================================
# 2. LOAD JSON FILES
# =========================================================

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# =========================================================
# 3. LOAD DATASETS
# =========================================================

drugs = load_json("drugs.json")
indications = load_json("indications.json")
relationships = load_json("relationships.json")


# =========================================================
# 4. CREATE KNOWLEDGE GRAPH
# =========================================================

G = nx.Graph()


# =========================================================
# 5. ADD DRUG NODES
# =========================================================

for drug in drugs:

    drug_id = drug.get("chembl_id")
    drug_name = drug.get("name")

    if not drug_id or not drug_name:
        continue

    G.add_node(
        drug_id,
        type="drug",
        name=drug_name,
        max_phase=drug.get("max_phase"),
        molecule_type=drug.get("molecule_type"),
        first_approval=drug.get("first_approval"),
        oral=drug.get("oral"),
        parenteral=drug.get("parenteral"),
        topical=drug.get("topical"),
        black_box_warning=drug.get("black_box_warning"),
        evidence_source=drug.get("source", "ChEMBL")
    )


# =========================================================
# 6. ADD CONDITION / INDICATION NODES
# =========================================================

for record in indications:

    drug_id = record.get("drug_id")
    condition = record.get("condition")

    if not drug_id or not condition:
        continue

    if drug_id not in G:
        continue

    condition_id = "condition:" + condition.lower().strip()

    G.add_node(
        condition_id,
        type="condition",
        name=condition
    )

    G.add_edge(
        drug_id,
        condition_id,
        relationship="associated_with_indication",
        evidence_source=record.get(
            "evidence_source",
            "ChEMBL drug_indication"
        ),
        mesh_id=record.get("mesh_id"),
        mesh_heading=record.get("mesh_heading"),
        efo_id=record.get("efo_id"),
        efo_term=record.get("efo_term"),
        max_phase_for_indication=record.get(
            "max_phase_for_indication"
        )
    )


# =========================================================
# 7. ADD BIOLOGICAL TARGET NODES
# =========================================================

for record in relationships:

    drug_id = record.get("drug_id")
    target_id = record.get("target_id")

    if not drug_id or not target_id:
        continue

    if drug_id not in G:
        continue

    G.add_node(
        target_id,
        type="target",
        name=record.get("target_name"),
        target_type=record.get("target_type"),
        organism=record.get("target_organism"),
        uniprot_accessions=record.get(
            "uniprot_accessions",
            []
        )
    )

    G.add_edge(
        drug_id,
        target_id,
        relationship=record.get(
            "relationship",
            "TARGETS"
        ),
        mechanism_of_action=record.get(
            "mechanism_of_action"
        ),
        evidence_source=record.get(
            "evidence_source",
            "ChEMBL mechanism"
        ),
        mechanism_record_id=record.get(
            "mechanism_record_id"
        )
    )


# =========================================================
# 8. FIND DRUG BY NAME
# =========================================================

def find_drug_by_name(drug_name):

    search_name = drug_name.lower().strip()

    for node_id, data in G.nodes(data=True):

        if data.get("type") != "drug":
            continue

        name = data.get("name")

        if name and name.lower().strip() == search_name:
            return node_id

    return None


# =========================================================
# 9. FIND DRUGS FOR CONDITION / INDICATION
# =========================================================

def find_drugs_for_condition(condition_name):

    search_name = condition_name.lower().strip()

    matched_drugs = []

    for node_id, data in G.nodes(data=True):

        if data.get("type") != "condition":
            continue

        condition = data.get("name")

        if not condition:
            continue

        if search_name in condition.lower():

            for neighbour in G.neighbors(node_id):

                neighbour_data = G.nodes[neighbour]

                if neighbour_data.get("type") == "drug":

                    matched_drugs.append({
                        "drug_id": neighbour,
                        "drug_name": neighbour_data.get("name"),
                        "condition": condition
                    })

    # Remove duplicates
    unique_drugs = {}

    for drug in matched_drugs:
        unique_drugs[drug["drug_id"]] = drug

    return list(unique_drugs.values())


# =========================================================
# 10. FIND SHARED BIOLOGICAL TARGETS
# =========================================================

def find_shared_targets(drug_a_name, drug_b_name):

    drug_a = find_drug_by_name(drug_a_name)
    drug_b = find_drug_by_name(drug_b_name)

    if not drug_a or not drug_b:
        return []

    targets_a = {
        neighbour
        for neighbour in G.neighbors(drug_a)
        if G.nodes[neighbour].get("type") == "target"
    }

    targets_b = {
        neighbour
        for neighbour in G.neighbors(drug_b)
        if G.nodes[neighbour].get("type") == "target"
    }

    shared = targets_a.intersection(targets_b)

    results = []

    for target_id in sorted(shared):

        target_data = G.nodes[target_id]

        edge_a = G.edges[drug_a, target_id]
        edge_b = G.edges[drug_b, target_id]

        results.append({
            "target_id": target_id,
            "target_name": target_data.get("name"),
            "target_type": target_data.get("target_type"),
            "organism": target_data.get("organism"),
            "uniprot_accessions": target_data.get(
                "uniprot_accessions",
                []
            ),

            "drug_a_relationship": edge_a.get(
                "relationship"
            ),

            "drug_b_relationship": edge_b.get(
                "relationship"
            ),

            "drug_a_mechanism": edge_a.get(
                "mechanism_of_action"
            ),

            "drug_b_mechanism": edge_b.get(
                "mechanism_of_action"
            ),

            "drug_a_evidence_source": edge_a.get(
                "evidence_source"
            ),

            "drug_b_evidence_source": edge_b.get(
                "evidence_source"
            ),

            "drug_a_mechanism_record_id": edge_a.get(
                "mechanism_record_id"
            ),

            "drug_b_mechanism_record_id": edge_b.get(
                "mechanism_record_id"
            )
        })

    return results


# =========================================================
# 11. ANALYZE TWO MEDICINES
# =========================================================

def analyze_medicines(drug_a_name, drug_b_name):

    drug_a = find_drug_by_name(drug_a_name)
    drug_b = find_drug_by_name(drug_b_name)

    # -----------------------------------------------------
    # Check whether medicines exist
    # -----------------------------------------------------

    if not drug_a or not drug_b:

        missing = []

        if not drug_a:
            missing.append(drug_a_name)

        if not drug_b:
            missing.append(drug_b_name)

        return {
            "found": False,
            "relationship_label": "Insufficient evidence",
            "relationship_type": "medicine_not_found",
            "missing_medicines": missing,
            "message": (
                "One or both medicines were not found "
                "in the current MedGraph dataset."
            )
        }

    # -----------------------------------------------------
    # Look for shared biological targets
    # -----------------------------------------------------

    shared_targets = find_shared_targets(
        drug_a_name,
        drug_b_name
    )

    if shared_targets:

        graph_nodes = [
            {
                "id": drug_a,
                "name": G.nodes[drug_a].get("name"),
                "type": "drug"
            },
            {
                "id": drug_b,
                "name": G.nodes[drug_b].get("name"),
                "type": "drug"
            }
        ]

        graph_edges = []

        for target in shared_targets:

            target_id = target["target_id"]

            graph_nodes.append({
                "id": target_id,
                "name": target["target_name"],
                "type": "target",
                "target_type": target["target_type"],
                "organism": target["organism"],
                "uniprot_accessions": target[
                    "uniprot_accessions"
                ]
            })

            graph_edges.append({
                "source": drug_a,
                "target": target_id,
                "relationship": target[
                    "drug_a_relationship"
                ],
                "mechanism_of_action": target[
                    "drug_a_mechanism"
                ],
                "evidence_source": target[
                    "drug_a_evidence_source"
                ],
                "mechanism_record_id": target[
                    "drug_a_mechanism_record_id"
                ]
            })

            graph_edges.append({
                "source": drug_b,
                "target": target_id,
                "relationship": target[
                    "drug_b_relationship"
                ],
                "mechanism_of_action": target[
                    "drug_b_mechanism"
                ],
                "evidence_source": target[
                    "drug_b_evidence_source"
                ],
                "mechanism_record_id": target[
                    "drug_b_mechanism_record_id"
                ]
            })

        return {
            "found": True,

            "relationship_label":
                "Direct biological relationship",

            "relationship_type":
                "shared_biological_target",

            "drug_a": {
                "id": drug_a,
                "name": G.nodes[drug_a].get("name")
            },

            "drug_b": {
                "id": drug_b,
                "name": G.nodes[drug_b].get("name")
            },

            "shared_target_count": len(shared_targets),

            "shared_targets": shared_targets,

            "graph": {
                "nodes": graph_nodes,
                "edges": graph_edges
            },

            "message": (
                "These medicines share one or more "
                "biological targets represented in the "
                "ChEMBL-derived knowledge graph. "
                "This represents a biological connection "
                "and does not by itself establish a "
                "clinical drug-drug interaction."
            )
        }

    # -----------------------------------------------------
    # Look for shared indications
    # -----------------------------------------------------

    conditions_a = {
        neighbour
        for neighbour in G.neighbors(drug_a)
        if G.nodes[neighbour].get("type") == "condition"
    }

    conditions_b = {
        neighbour
        for neighbour in G.neighbors(drug_b)
        if G.nodes[neighbour].get("type") == "condition"
    }

    shared_conditions = conditions_a.intersection(
        conditions_b
    )

    if shared_conditions:

        condition_results = []

        graph_nodes = [
            {
                "id": drug_a,
                "name": G.nodes[drug_a].get("name"),
                "type": "drug"
            },
            {
                "id": drug_b,
                "name": G.nodes[drug_b].get("name"),
                "type": "drug"
            }
        ]

        graph_edges = []

        for condition_id in sorted(shared_conditions):

            condition_name = G.nodes[
                condition_id
            ].get("name")

            condition_results.append({
                "condition_id": condition_id,
                "condition_name": condition_name
            })

            graph_nodes.append({
                "id": condition_id,
                "name": condition_name,
                "type": "condition"
            })

            edge_a = G.edges[
                drug_a,
                condition_id
            ]

            edge_b = G.edges[
                drug_b,
                condition_id
            ]

            graph_edges.append({
                "source": drug_a,
                "target": condition_id,
                "relationship": edge_a.get(
                    "relationship"
                ),
                "evidence_source": edge_a.get(
                    "evidence_source"
                ),
                "mesh_id": edge_a.get("mesh_id"),
                "efo_id": edge_a.get("efo_id")
            })

            graph_edges.append({
                "source": drug_b,
                "target": condition_id,
                "relationship": edge_b.get(
                    "relationship"
                ),
                "evidence_source": edge_b.get(
                    "evidence_source"
                ),
                "mesh_id": edge_b.get("mesh_id"),
                "efo_id": edge_b.get("efo_id")
            })

        return {
            "found": True,

            "relationship_label":
                "Limited evidence",

            "relationship_type":
                "shared_indication",

            "drug_a": {
                "id": drug_a,
                "name": G.nodes[drug_a].get("name")
            },

            "drug_b": {
                "id": drug_b,
                "name": G.nodes[drug_b].get("name")
            },

            "shared_conditions":
                condition_results,

            "graph": {
                "nodes": graph_nodes,
                "edges": graph_edges
            },

            "message": (
                "Both medicines are associated with one "
                "or more of the same indications in the "
                "current dataset. A shared indication "
                "does not establish a biological or "
                "clinical drug-drug interaction."
            )
        }

    # -----------------------------------------------------
    # No supported relationship
    # -----------------------------------------------------

    return {
        "found": False,

        "relationship_label":
            "Insufficient evidence",

        "relationship_type":
            "no_supported_relationship",

        "drug_a": {
            "id": drug_a,
            "name": G.nodes[drug_a].get("name")
        },

        "drug_b": {
            "id": drug_b,
            "name": G.nodes[drug_b].get("name")
        },

        "graph": {
            "nodes": [],
            "edges": []
        },

        "message": (
            "Insufficient evidence in the current "
            "knowledge graph to establish a supported "
            "relationship between these medicines."
        )
    }


# =========================================================
# 12. GRAPH STATISTICS
# =========================================================

def print_graph_statistics():

    drug_nodes = [
        node
        for node, data in G.nodes(data=True)
        if data.get("type") == "drug"
    ]

    condition_nodes = [
        node
        for node, data in G.nodes(data=True)
        if data.get("type") == "condition"
    ]

    target_nodes = [
        node
        for node, data in G.nodes(data=True)
        if data.get("type") == "target"
    ]

    print()
    print("MEDGRAPH KNOWLEDGE GRAPH")
    print("--------------------------------------")
    print("Total nodes:", G.number_of_nodes())
    print("Total edges:", G.number_of_edges())
    print("Drug nodes:", len(drug_nodes))
    print("Condition nodes:", len(condition_nodes))
    print("Target nodes:", len(target_nodes))
    print("--------------------------------------")


# =========================================================
# 13. TEST ANALYSIS
# =========================================================

if __name__ == "__main__":

    print_graph_statistics()

    print()
    print("TESTING MEDICINE ANALYSIS")
    print("======================================")

    result = analyze_medicines(
        "CHLORPROMAZINE",
        "OLANZAPINE"
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )