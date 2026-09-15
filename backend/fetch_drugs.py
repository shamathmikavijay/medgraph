import requests
import json
import os

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__),
    "data"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "drugs.json"
)

all_drugs = []

limit = 100
offset = 0

TARGET_COUNT = 500

print("Fetching real clinical/approved medicines from ChEMBL...")
print()


while len(all_drugs) < TARGET_COUNT:

    print(
        f"Fetching page starting at offset {offset} "
        f"({len(all_drugs)}/{TARGET_COUNT} collected)..."
    )

    url = f"{BASE_URL}/molecule.json"

    params = {
        "max_phase__gte": 3,
        "limit": limit,
        "offset": offset
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        molecules = data.get("molecules", [])

        if not molecules:
            print("No more records returned.")
            break


        for molecule in molecules:

            chembl_id = molecule.get(
                "molecule_chembl_id"
            )

            name = molecule.get("pref_name")

            # We want medicines with useful readable names
            if not chembl_id or not name:
                continue


            record = {
                "chembl_id": chembl_id,
                "name": name,
                "max_phase": molecule.get(
                    "max_phase"
                ),
                "molecule_type": molecule.get(
                    "molecule_type"
                ),
                "first_approval": molecule.get(
                    "first_approval"
                ),
                "oral": molecule.get("oral"),
                "parenteral": molecule.get(
                    "parenteral"
                ),
                "topical": molecule.get("topical"),
                "black_box_warning": molecule.get(
                    "black_box_warning"
                ),
                "source": "ChEMBL"
            }

            all_drugs.append(record)

            if len(all_drugs) >= TARGET_COUNT:
                break


        offset += limit


    except requests.RequestException as error:

        print(f"ChEMBL request failed: {error}")
        break


# Remove duplicate ChEMBL IDs

unique_drugs = {}

for drug in all_drugs:
    unique_drugs[drug["chembl_id"]] = drug

all_drugs = list(unique_drugs.values())


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        all_drugs,
        file,
        indent=2,
        ensure_ascii=False
    )


print()
print("--------------------------------------")
print(f"Saved {len(all_drugs)} real medicines.")
print(f"File: {OUTPUT_FILE}")
print("--------------------------------------")