import json
from pathlib import Path

import networkx as nx


# ---------------------------------------------------------
# DATA FILE
# ---------------------------------------------------------

RELATIONSHIPS_FILE = (
    Path(__file__).parent / "data" / "relationships.json"
)


# ---------------------------------------------------------
# LOAD CHemBL RELATIONSHIP DATA
# ---------------------------------------------------------

def load_relationships():
    """
    Load drug-target/mechanism relationships collected
    from ChEMBL.
    """

    if not RELATIONSHIPS_FILE.exists():
        print(
            f"Warning: relationships.json not found at "
            f"{RELATIONSHIPS_FILE}"
        )
        return []

    try:
        with open(
            RELATIONSHIPS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError) as error:
        print(f"Error loading relationships.json: {error}")
        return []


# ---------------------------------------------------------
# BUILD KNOWLEDGE GRAPH
# ---------------------------------------------------------

def build_graph():
    """
    Build a NetworkX graph containing:

    Drug ---- biological relationship ---- Target
    """

    data = load_relationships()

    graph = nx.Graph()

    for item in data:

        drug_id = item.get("drug_id")
        drug_name = item.get("drug_name")

        target_id = item.get("target_id")
        target_name = item.get("target_name")

        relationship = item.get(
            "relationship",
            "TARGETS"
        )

        if not drug_id or not target_id:
            continue

        drug_node = f"drug:{drug_id}"
        target_node = f"target:{target_id}"

        # -----------------------------
        # DRUG NODE
        # -----------------------------

        graph.add_node(
            drug_node,
            node_type="drug",
            id=drug_id,
            name=drug_name
        )

        # -----------------------------
        # TARGET NODE
        # -----------------------------

        graph.add_node(
            target_node,
            node_type="target",
            id=target_id,
            name=target_name,
            target_type=item.get("target_type"),
            organism=item.get("target_organism"),
            uniprot_accessions=item.get(
                "uniprot_accessions",
                []
            )
        )

        # -----------------------------
        # DRUG → TARGET EDGE
        # -----------------------------

        graph.add_edge(
            drug_node,
            target_node,
            relationship=relationship,
            mechanism_of_action=item.get(
                "mechanism_of_action"
            ),
            mechanism_record_id=item.get(
                "mechanism_record_id"
            ),
            evidence_source=item.get(
                "evidence_source",
                "ChEMBL mechanism"
            )
        )

    return graph


# ---------------------------------------------------------
# CREATE GRAPH ONCE
# ---------------------------------------------------------

GRAPH = build_graph()


# ---------------------------------------------------------
# FIND DRUG NODE
# ---------------------------------------------------------

def find_drug_node(drug_id):
    node = f"drug:{drug_id}"

    if GRAPH.has_node(node):
        return node

    return None


# ---------------------------------------------------------
# GET TARGETS FOR ONE DRUG
# ---------------------------------------------------------

def get_drug_targets(drug_id):

    drug_node = find_drug_node(drug_id)

    if not drug_node:
        return []

    targets = []

    for neighbor in GRAPH.neighbors(drug_node):

        node_data = GRAPH.nodes[neighbor]
        edge_data = GRAPH.edges[drug_node, neighbor]

        if node_data.get("node_type") != "target":
            continue

        targets.append({
            "target_id": node_data.get("id"),
            "target_name": node_data.get("name"),
            "target_type": node_data.get("target_type"),
            "organism": node_data.get("organism"),
            "uniprot_accessions": node_data.get(
                "uniprot_accessions",
                []
            ),
            "relationship": edge_data.get(
                "relationship"
            ),
            "mechanism_of_action": edge_data.get(
                "mechanism_of_action"
            ),
            "mechanism_record_id": edge_data.get(
                "mechanism_record_id"
            ),
            "evidence_source": edge_data.get(
                "evidence_source"
            )
        })

    return targets


# ---------------------------------------------------------
# COMPARE TWO MEDICINES
# ---------------------------------------------------------

def analyze_drug_pair(drug_a_id, drug_b_id):
    """
    Compare two medicines using their biological targets.

    This detects shared biological targets from the
    ChEMBL mechanism dataset.

    It does NOT determine whether the medicines are
    clinically safe or unsafe to take together.
    """

    node_a = find_drug_node(drug_a_id)
    node_b = find_drug_node(drug_b_id)

    if not node_a or not node_b:
        return {
            "relationship_label": "Insufficient evidence",
            "message": (
                "Mechanism/target evidence for one or both "
                "medicines was not found in the current dataset."
            ),
            "shared_targets": [],
            "paths": []
        }

    targets_a = set(GRAPH.neighbors(node_a))
    targets_b = set(GRAPH.neighbors(node_b))

    shared_target_nodes = targets_a.intersection(targets_b)

    shared_targets = []
    paths = []

    for target_node in shared_target_nodes:

        target_data = GRAPH.nodes[target_node]

        edge_a = GRAPH.edges[node_a, target_node]
        edge_b = GRAPH.edges[node_b, target_node]

        shared_targets.append({
            "target_id": target_data.get("id"),
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
            "evidence_source": "ChEMBL mechanism"
        })

        paths.append({
            "nodes": [
                GRAPH.nodes[node_a].get("name"),
                target_data.get("name"),
                GRAPH.nodes[node_b].get("name")
            ],
            "type": "shared_target"
        })

    if shared_targets:

        relationship_label = "Direct biological relationship"

        message = (
            "Both medicines connect to at least one shared "
            "biological target in the current ChEMBL "
            "mechanism dataset."
        )

    else:

        relationship_label = "Limited evidence"

        message = (
            "Both medicines have mechanism records in the "
            "dataset, but no shared biological target was "
            "identified in the current graph."
        )

    return {
        "drug_a": {
            "drug_id": drug_a_id,
            "drug_name": GRAPH.nodes[node_a].get("name")
        },
        "drug_b": {
            "drug_id": drug_b_id,
            "drug_name": GRAPH.nodes[node_b].get("name")
        },
        "relationship_label": relationship_label,
        "message": message,
        "shared_target_count": len(shared_targets),
        "shared_targets": shared_targets,
        "paths": paths
    }


# ---------------------------------------------------------
# GRAPH STATISTICS
# ---------------------------------------------------------

def get_graph_stats():

    drug_nodes = [
        node
        for node, data in GRAPH.nodes(data=True)
        if data.get("node_type") == "drug"
    ]

    target_nodes = [
        node
        for node, data in GRAPH.nodes(data=True)
        if data.get("node_type") == "target"
    ]

    return {
        "drug_nodes": len(drug_nodes),
        "target_nodes": len(target_nodes),
        "total_nodes": GRAPH.number_of_nodes(),
        "total_edges": GRAPH.number_of_edges()
    }


# ---------------------------------------------------------
# TEST WHEN RUN DIRECTLY
# ---------------------------------------------------------

if __name__ == "__main__":

    print("MedGraph Knowledge Graph")
    print("------------------------")

    stats = get_graph_stats()

    print(f"Drug nodes: {stats['drug_nodes']}")
    print(f"Target nodes: {stats['target_nodes']}")
    print(f"Total nodes: {stats['total_nodes']}")
    print(f"Total edges: {stats['total_edges']}")