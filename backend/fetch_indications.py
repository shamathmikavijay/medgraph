import json
import os
import requests
import time

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DRUGS_FILE = os.path.join(DATA_DIR, "drugs.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "relationships.json")


# ---------------------------------------------------------
# LOAD OUR 500 MEDICINES
# ---------------------------------------------------------

with open(DRUGS_FILE, "r", encoding="utf-8") as file:
    drugs = json.load(file)

drug_lookup = {
    drug["chembl_id"]: drug["name"]
    for drug in drugs
}

drug_ids = set(drug_lookup.keys())

print(f"Loaded {len(drug_ids)} medicines.")
print("Fetching ChEMBL mechanism records...")
print()


# ---------------------------------------------------------
# FETCH ALL MECHANISMS PAGE BY PAGE
# ---------------------------------------------------------

mechanism_records = []

limit = 1000
offset = 0

while True:

    print(f"Fetching mechanism page at offset {offset}...")

    try:
        response = requests.get(
            f"{BASE_URL}/mechanism.json",
            params={
                "limit": limit,
                "offset": offset
            },
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        records = data.get("mechanisms", [])

        if not records:
            break

        for item in records:

            drug_id = item.get("molecule_chembl_id")

            if drug_id not in drug_ids:
                continue

            target_id = item.get("target_chembl_id")

            if not target_id:
                continue

            mechanism_records.append({
                "drug_id": drug_id,
                "drug_name": drug_lookup.get(drug_id),
                "relationship": item.get("action_type") or "TARGETS",
                "target_id": target_id,
                "mechanism_of_action": item.get("mechanism_of_action"),
                "mechanism_record_id": item.get("mec_id"),
                "evidence_source": "ChEMBL mechanism"
            })

        page_meta = data.get("page_meta", {})

        if not page_meta.get("next"):
            break

        offset += limit
        time.sleep(0.15)

    except requests.RequestException as error:
        print(f"Mechanism request failed: {error}")
        break


print()
print(
    f"Found {len(mechanism_records)} mechanism records "
    f"for our medicines."
)


# ---------------------------------------------------------
# COLLECT UNIQUE TARGET IDs
# ---------------------------------------------------------

target_ids = sorted({
    item["target_id"]
    for item in mechanism_records
})

print(f"Unique ChEMBL targets to retrieve: {len(target_ids)}")
print()


# ---------------------------------------------------------
# FETCH EACH UNIQUE TARGET ONLY ONCE
# ---------------------------------------------------------

targets = {}

for number, target_id in enumerate(target_ids, start=1):

    if number == 1 or number % 25 == 0:
        print(
            f"Fetching target {number}/{len(target_ids)}..."
        )

    try:
        response = requests.get(
            f"{BASE_URL}/target/{target_id}.json",
            timeout=30
        )

        response.raise_for_status()
        target = response.json()

        accessions = []

        for component in target.get("target_components", []):

            accession = component.get("accession")

            if accession:
                accessions.append(accession)

        targets[target_id] = {
            "target_name": target.get("pref_name"),
            "target_type": target.get("target_type"),
            "organism": target.get("organism"),
            "uniprot_accessions": sorted(set(accessions))
        }

        time.sleep(0.05)

    except requests.RequestException as error:

        print(f"  Could not fetch {target_id}: {error}")

        targets[target_id] = {
            "target_name": None,
            "target_type": None,
            "organism": None,
            "uniprot_accessions": []
        }


# ---------------------------------------------------------
# COMBINE MECHANISM + TARGET INFORMATION
# ---------------------------------------------------------

relationships = []

for item in mechanism_records:

    target = targets.get(
        item["target_id"],
        {}
    )

    relationships.append({
        "drug_id": item["drug_id"],
        "drug_name": item["drug_name"],

        "relationship": item["relationship"],

        "target_id": item["target_id"],
        "target_name": target.get("target_name"),
        "target_type": target.get("target_type"),
        "target_organism": target.get("organism"),

        "uniprot_accessions":
            target.get("uniprot_accessions", []),

        "mechanism_of_action":
            item["mechanism_of_action"],

        "mechanism_record_id":
            item["mechanism_record_id"],

        "evidence_source":
            item["evidence_source"]
    })


# ---------------------------------------------------------
# REMOVE DUPLICATES
# ---------------------------------------------------------

unique = {}

for item in relationships:

    key = (
        item["drug_id"],
        item["target_id"],
        item["relationship"],
        item["mechanism_of_action"]
    )

    unique[key] = item

relationships = list(unique.values())


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        relationships,
        file,
        indent=2,
        ensure_ascii=False
    )


# ---------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------

drugs_with_relationships = {
    item["drug_id"]
    for item in relationships
}

unique_targets = {
    item["target_id"]
    for item in relationships
}

uniprot_ids = {
    accession
    for item in relationships
    for accession in item["uniprot_accessions"]
}


print()
print("--------------------------------------")
print("RELATIONSHIP DATASET COMPLETE")
print("--------------------------------------")
print(f"Medicines searched: {len(drug_ids)}")
print(
    f"Medicines with mechanism data: "
    f"{len(drugs_with_relationships)}"
)
print(
    f"Unique biological targets: "
    f"{len(unique_targets)}"
)
print(
    f"Unique UniProt accessions: "
    f"{len(uniprot_ids)}"
)
print(
    f"Drug-target/mechanism relationships: "
    f"{len(relationships)}"
)
print()
print(f"Saved to: {OUTPUT_FILE}")
print("--------------------------------------")