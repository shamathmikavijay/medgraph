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


# =========================================================
# HELPER — GET ALL MEDICINES
# =========================================================

def get_all_medicines():
    """
    Return every medicine represented as a drug node
    in the current MedGraph knowledge graph.
    """

    medicines = []

    for _, data in G.nodes(data=True):
        if data.get("type") == "drug":
            name = (
                data.get("name")
                or data.get("drug_name")
            )

            if name:
                medicines.append(name)

    return sorted(
        set(medicines),
        key=str.lower
    )


# =========================================================
# EVIDENCE RELATIONSHIP SCORE
# =========================================================

def calculate_evidence_score(analysis):
    """
    Experimental evidence-coverage score.

    IMPORTANT:
    This measures evidence represented in MedGraph.
    It is NOT a clinical safety, risk, or compatibility score.
    """

    score = 0
    reasons = []

    relationship_type = analysis.get(
        "relationship_type"
    )

    shared_targets = analysis.get(
        "shared_targets",
        []
    )

    shared_conditions = analysis.get(
        "shared_conditions",
        []
    )

    # -----------------------------------------------------
    # SHARED BIOLOGICAL TARGET
    # -----------------------------------------------------

    if relationship_type == "shared_biological_target":
        score += 40

        reasons.append({
            "label": "Shared biological target",
            "points": 40
        })

    # -----------------------------------------------------
    # SHARED INDICATION
    # -----------------------------------------------------

    elif relationship_type == "shared_indication":
        score += 20

        reasons.append({
            "label": "Shared indication",
            "points": 20
        })

    # -----------------------------------------------------
    # ADDITIONAL SHARED TARGETS
    # -----------------------------------------------------

    if shared_targets:
        extra_targets = max(
            0,
            len(shared_targets) - 1
        )

        if extra_targets > 0:
            points = min(
                extra_targets * 5,
                15
            )

            score += points

            reasons.append({
                "label": "Additional shared targets",
                "points": points
            })

    # -----------------------------------------------------
    # MEDICINE A MECHANISM / ACTION EVIDENCE
    # -----------------------------------------------------

    has_a_evidence = any(
        target.get("drug_a_mechanism")
        or target.get("drug_a_relationship")
        for target in shared_targets
    )

    if has_a_evidence:
        score += 15

        reasons.append({
            "label": "Mechanism/action evidence for Medicine A",
            "points": 15
        })

    # -----------------------------------------------------
    # MEDICINE B MECHANISM / ACTION EVIDENCE
    # -----------------------------------------------------

    has_b_evidence = any(
        target.get("drug_b_mechanism")
        or target.get("drug_b_relationship")
        for target in shared_targets
    )

    if has_b_evidence:
        score += 15

        reasons.append({
            "label": "Mechanism/action evidence for Medicine B",
            "points": 15
        })

    # -----------------------------------------------------
    # UNIPROT EVIDENCE
    # -----------------------------------------------------

    has_uniprot = any(
        target.get("uniprot_accessions")
        for target in shared_targets
    )

    if has_uniprot:
        score += 10

        reasons.append({
            "label": "UniProt identifier available",
            "points": 10
        })

    # -----------------------------------------------------
    # SHARED INDICATION SUPPORT
    # -----------------------------------------------------

    if (
        relationship_type != "shared_indication"
        and shared_conditions
    ):
        score += 10

        reasons.append({
            "label": "Shared indication evidence",
            "points": 10
        })

    score = min(score, 100)

    # -----------------------------------------------------
    # HUMAN-READABLE STRENGTH
    # -----------------------------------------------------

    if score >= 75:
        strength = "Strong represented evidence"

    elif score >= 45:
        strength = "Moderate represented evidence"

    elif score > 0:
        strength = "Limited represented evidence"

    else:
        strength = "Insufficient represented evidence"

    return {
        "score": score,
        "max_score": 100,
        "strength": strength,
        "label": "MedGraph Evidence Score",
        "reasons": reasons,
        "disclaimer": (
            "This experimental score measures the amount of "
            "biological evidence represented in MedGraph. "
            "It does not determine whether two medicines are "
            "clinically safe, unsafe, compatible, or incompatible."
        )
    }


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="MedGraph API",
    description=(
        "Backend API for MedGraph - an explainable, "
        "condition-guided medicine relationship explorer."
    ),
    version="1.2.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "project": "MedGraph",
        "message": "MedGraph backend is running",
        "status": "online",
        "version": "1.2.0"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# CONDITIONS
# =========================================================

@app.get("/conditions")
def conditions():

    condition_list = get_conditions()

    return {
        "count": len(condition_list),
        "conditions": condition_list
    }


# =========================================================
# MEDICINES
#
# /medicines
#       -> ALL medicines
#
# /medicines?condition=...
#       -> medicines associated with that indication
# =========================================================

@app.get("/medicines")
def medicines(condition: str | None = None):

    if condition and condition.strip():

        medicine_list = get_medicines_for_condition(
            condition.strip()
        )

    else:

        medicine_list = get_all_medicines()

    return {
        "condition": condition,
        "count": len(medicine_list),
        "medicines": medicine_list
    }


# =========================================================
# GRAPH STATISTICS
# =========================================================

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


# =========================================================
# ANALYZE TWO MEDICINES
# =========================================================

@app.get("/analyze")
def analyze(
    drug_a: str,
    drug_b: str
):

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    drug_a = drug_a.strip()
    drug_b = drug_b.strip()

    if drug_a.lower() == drug_b.lower():
        return {
            "relationship_label": "Insufficient evidence",
            "relationship_type": "same_medicine",
            "message": (
                "Please select two different medicines "
                "for relationship analysis."
            ),
            "drug_a": {
                "name": drug_a
            },
            "drug_b": {
                "name": drug_b
            },
            "shared_targets": [],
            "shared_conditions": [],
            "graph": {
                "nodes": [],
                "edges": []
            },
            "explanations": {
                "relationship_label": "Insufficient evidence",
                "simple_explanation": (
                    "Select two different medicines to explore "
                    "a biological relationship."
                ),
                "scientific_explanation": (
                    "A pairwise relationship analysis requires "
                    "two distinct medicine entities."
                ),
                "explanation_source": (
                    "MedGraph evidence-grounded generator"
                )
            },
            "evidence_score": {
                "score": 0,
                "max_score": 100,
                "strength": "Insufficient represented evidence",
                "label": "MedGraph Evidence Score",
                "reasons": [],
                "disclaimer": (
                    "This experimental score measures biological "
                    "evidence represented in MedGraph and is not "
                    "a clinical safety score."
                )
            }
        }

    # -----------------------------------------------------
    # GRAPH ANALYSIS
    # -----------------------------------------------------

    analysis = analyze_medicines(
        drug_a,
        drug_b
    )

    # -----------------------------------------------------
    # EXPLANATION ENGINE
    # -----------------------------------------------------

    analysis["explanations"] = (
        generate_explanations(
            analysis
        )
    )

    # -----------------------------------------------------
    # EVIDENCE SCORE
    # -----------------------------------------------------

    analysis["evidence_score"] = (
        calculate_evidence_score(
            analysis
        )
    )

    # -----------------------------------------------------
    # ADVERSE-EFFECT DATA STATUS
    #
    # Current MedGraph data does not contain a validated
    # pair-specific adverse-event dataset, so we explicitly
    # report that instead of inferring an effect.
    # -----------------------------------------------------

    analysis["adverse_effect_evidence"] = {
        "available": False,
        "status": "Not represented in current dataset",
        "message": (
            "MedGraph currently does not contain validated "
            "pair-specific adverse-effect evidence for this "
            "analysis. A shared biological target should not "
            "be interpreted as proof of a particular side effect."
        )
    }

    return analysis