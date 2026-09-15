import json
from pathlib import Path


# Location of Roshni's real ChEMBL indication dataset
DATA_FILE = Path(__file__).parent / "data" / "indications.json"


def load_indications():
    """
    Load the ChEMBL indication dataset.
    """
    if not DATA_FILE.exists():
        print(f"Warning: Dataset not found at {DATA_FILE}")
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError) as error:
        print(f"Error loading indications.json: {error}")
        return []


def get_conditions():
    """
    Return all unique conditions/indications.
    """
    data = load_indications()

    conditions = sorted({
        item["condition"]
        for item in data
        if item.get("condition")
    })

    return conditions


def get_medicines_for_condition(condition):
    """
    Return medicines associated with a selected condition.
    """
    data = load_indications()

    medicines = []

    for item in data:

        if item.get("condition", "").lower() == condition.lower():

            medicines.append({
                "drug_id": item.get("drug_id"),
                "drug_name": item.get("drug_name"),
                "mesh_id": item.get("mesh_id"),
                "mesh_heading": item.get("mesh_heading"),
                "efo_id": item.get("efo_id"),
                "efo_term": item.get("efo_term"),
                "max_phase_for_indication": item.get(
                    "max_phase_for_indication"
                ),
                "evidence_source": item.get(
                    "evidence_source",
                    "ChEMBL drug_indication"
                )
            })

    return medicines