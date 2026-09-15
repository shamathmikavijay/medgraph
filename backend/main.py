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


app = FastAPI(
    title="MedGraph API",
    description=(
        "Backend API for MedGraph - an explainable, "
        "condition-guided medicine interaction explorer."
    ),
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "project": "MedGraph",
        "message": "MedGraph backend is running",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/conditions")
def conditions():
    condition_list = get_conditions()

    return {
        "count": len(condition_list),
        "conditions": condition_list
    }


@app.get("/medicines")
def medicines(condition: str):
    medicine_list = get_medicines_for_condition(condition)

    return {
        "condition": condition,
        "count": len(medicine_list),
        "medicines": medicine_list
    }


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


@app.get("/analyze")
def analyze(
    drug_a: str,
    drug_b: str
):
    return analyze_medicines(
        drug_a,
        drug_b
    )