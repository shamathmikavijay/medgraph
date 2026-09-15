def generate_explanations(analysis):
    """
    Converts evidence retrieved by the MedGraph knowledge graph
    into simple and scientific explanations.

    This function does NOT determine clinical safety.
    It only explains relationships already found in the graph.
    """

    relationship_label = analysis.get(
        "relationship_label",
        "Insufficient evidence"
    )

    drug_a = analysis.get("drug_a", {})
    drug_b = analysis.get("drug_b", {})

    drug_a_name = drug_a.get("name", "Medicine A")
    drug_b_name = drug_b.get("name", "Medicine B")

    # ---------------------------------------------------------
    # CASE 1: SHARED BIOLOGICAL TARGET
    # ---------------------------------------------------------

    if analysis.get("relationship_type") == "shared_biological_target":

        targets = analysis.get("shared_targets", [])

        if not targets:
            return insufficient_evidence_explanation(
                drug_a_name,
                drug_b_name
            )

        simple_parts = []
        scientific_parts = []

        for target in targets:

            target_name = target.get(
                "target_name",
                "a biological target"
            )

            target_id = target.get("target_id", "Unknown")

            uniprot = target.get(
                "uniprot_accessions",
                []
            )

            action_a = target.get(
                "drug_a_relationship",
                "interacts with"
            )

            action_b = target.get(
                "drug_b_relationship",
                "interacts with"
            )

            mechanism_a = target.get(
                "drug_a_mechanism"
            )

            mechanism_b = target.get(
                "drug_b_mechanism"
            )

            uniprot_text = (
                ", ".join(uniprot)
                if uniprot
                else "not available"
            )

            simple_parts.append(
                f"{drug_a_name} and {drug_b_name} are biologically "
                f"connected because both are associated with "
                f"{target_name}. In the available ChEMBL evidence, "
                f"{drug_a_name} is described as {action_a.lower()} "
                f"and {drug_b_name} as {action_b.lower()} for this "
                f"target."
            )

            scientific_text = (
                f"{drug_a_name} ({drug_a.get('id', 'Unknown')}) and "
                f"{drug_b_name} ({drug_b.get('id', 'Unknown')}) share "
                f"the biological target {target_name} "
                f"({target_id}; UniProt: {uniprot_text}). "
                f"ChEMBL mechanism records classify the relationships "
                f"as {action_a} for {drug_a_name} and {action_b} for "
                f"{drug_b_name}."
            )

            if mechanism_a:
                scientific_text += (
                    f" {drug_a_name} mechanism: {mechanism_a}."
                )

            if mechanism_b:
                scientific_text += (
                    f" {drug_b_name} mechanism: {mechanism_b}."
                )

            scientific_parts.append(scientific_text)

        simple_explanation = (
            " ".join(simple_parts)
            + " This indicates a shared biological relationship in "
              "the current dataset, but does not by itself establish "
              "a clinical drug-drug interaction."
        )

        scientific_explanation = (
            " ".join(scientific_parts)
            + " The shared target provides an evidence-supported "
              "biological relationship between the two medicines. "
              "This result should not be interpreted as a clinical "
              "safety assessment."
        )

        return {
            "relationship_label": relationship_label,
            "simple_explanation": simple_explanation,
            "scientific_explanation": scientific_explanation,
            "explanation_source": "MedGraph evidence-grounded generator"
        }

    # ---------------------------------------------------------
    # CASE 2: SHARED INDICATION
    # ---------------------------------------------------------

    if analysis.get("relationship_type") == "shared_indication":

        conditions = analysis.get(
            "shared_conditions",
            []
        )

        condition_names = [
            item.get("condition_name")
            for item in conditions
            if item.get("condition_name")
        ]

        condition_text = (
            ", ".join(condition_names)
            if condition_names
            else "one or more indications"
        )

        return {
            "relationship_label": relationship_label,

            "simple_explanation": (
                f"{drug_a_name} and {drug_b_name} are both associated "
                f"with {condition_text} in the current dataset. "
                f"This shows that they share an indication, but it "
                f"does not establish that the medicines biologically "
                f"interact or that they are safe to take together."
            ),

            "scientific_explanation": (
                f"ChEMBL indication records associate "
                f"{drug_a_name} ({drug_a.get('id', 'Unknown')}) and "
                f"{drug_b_name} ({drug_b.get('id', 'Unknown')}) with "
                f"{condition_text}. This represents an indication-level "
                f"relationship rather than evidence of a direct "
                f"drug-drug interaction."
            ),

            "explanation_source": "MedGraph evidence-grounded generator"
        }

    # ---------------------------------------------------------
    # CASE 3: NO SUPPORTED RELATIONSHIP
    # ---------------------------------------------------------

    return insufficient_evidence_explanation(
        drug_a_name,
        drug_b_name
    )


def insufficient_evidence_explanation(drug_a_name, drug_b_name):

    return {
        "relationship_label": "Insufficient evidence",

        "simple_explanation": (
            f"MedGraph does not currently have enough evidence to "
            f"show a supported relationship between {drug_a_name} "
            f"and {drug_b_name}. This does not mean that no clinical "
            f"interaction exists."
        ),

        "scientific_explanation": (
            f"No supported shared biological target or indication "
            f"relationship between {drug_a_name} and {drug_b_name} "
            f"was identified in the current MedGraph knowledge graph. "
            f"Absence of a relationship in this dataset should not be "
            f"interpreted as evidence of clinical compatibility."
        ),

        "explanation_source": "MedGraph evidence-grounded generator"
    }