from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from condition_lookup import (
    get_conditions,
    get_medicines_for_condition
)

from graph_engine import (
    analyze_drug_pair,
    get_graph_stats
)


# ---------------------------------------------------------
# CREATE FASTAPI APPLICATION
# ---------------------------------------------------------

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
# Allows the React frontend to communicate with FastAPI
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
# GET ALL CONDITIONS / INDICATIONS
# ---------------------------------------------------------

@app.get("/conditions")
def conditions():

    condition_list = get_conditions()

    return {
        "count": len(condition_list),
        "conditions": condition_list
    }


# ---------------------------------------------------------
# GET MEDICINES ASSOCIATED WITH A CONDITION
#
# Example:
# /medicines?condition=Hypertension
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

    return get_graph_stats()


# ---------------------------------------------------------
# ANALYZE TWO MEDICINES
#
# Example:
# /analyze?drug_a_id=CHEMBL24&drug_b_id=CHEMBL13
#
# This searches the knowledge graph for shared
# biological targets between the two medicines.
# ---------------------------------------------------------

@app.get("/analyze")
def analyze(
    drug_a_id: str,
    drug_b_id: str
):

    result = analyze_drug_pair(
        drug_a_id,
        drug_b_id
    )

    return result