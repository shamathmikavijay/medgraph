from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from condition_lookup import (
    get_conditions,
    get_medicines_for_condition
)

from graph_engine import (
    G,
    analyze_medicines
)

from explanation_engine import generate_explanations


app = FastAPI(
    title="MedGraph API",
    description=(
        "Backend API for MedGraph - an explainable, "
        "condition-guided medicine interaction explorer."
    ),
    version="1.0.0"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.get("/")
def home():
    return {
        "project": "MedGraph",
        "message": "MedGraph backend is running",
        "status": "online"
    }


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ---------------------------------------------------------
# CONDITIONS
# ---------------------------------------------------------

@app.get("/conditions")
def conditions():

    condition_list = get_conditions()

    return {
        "count": len(condition_list),
        "conditions": condition_list
    }


# ---------------------------------------------------------
# MEDICINES FOR A CONDITION
# ---------------------------------------------------------

@app.get("/medicines")
def medicines(condition: str):

    medicine_list = get_medicines_for_condition(condition)

    return {
        "condition": condition,
        "count": len(medicine_list),
        "medicines": medicine_list
    }


# ---------------------------------------------------------
# KNOWLEDGE GRAPH STATISTICS
# ---------------------------------------------------------

@app.get("/graph/stats")
def graph_stats():

    drug_nodes = sum(
        1
        for _, data in G.nodes(data=True)
        if data.get("type") == "drug"
    )

    condition_nodes = sum(
        1
        for _, data in G.nodes(data=True)
        if data.get("type") == "condition"
    )

    target_nodes = sum(
        1
        for _, data in G.nodes(data=True)
        if data.get("type") == "target"
    )

    return {
        "drug_nodes": drug_nodes,
        "condition_nodes": condition_nodes,
        "target_nodes": target_nodes,
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges()
    }


# ---------------------------------------------------------
# ANALYZE TWO MEDICINES
# ---------------------------------------------------------

@app.get("/analyze")
def analyze(
    drug_a: str,
    drug_b: str
):

    # Step 1:
    # Analyze the medicines using the knowledge graph.
    analysis = analyze_medicines(
        drug_a,
        drug_b
    )

    # Step 2:
    # Generate evidence-grounded explanations.
    explanations = generate_explanations(
        analysis
    )

    # Step 3:
    # Add explanations to the graph analysis result.
    analysis["explanations"] = explanations

    # Step 4:
    # Send everything to the frontend.
    return analysis