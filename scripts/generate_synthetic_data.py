import csv
import json
from pathlib import Path
from random import Random

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "synthetic"
OUTPUT.mkdir(parents=True, exist_ok=True)
random = Random(SEED)

specialties = ["General Medicine", "Cardiology", "Neurology", "Pulmonology", "Dermatology", "Orthopedics"]
locations = ["Mumbai", "Pune", "Bengaluru"]

with (OUTPUT / "providers.csv").open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["provider_id", "name", "specialty", "location", "consultation_type", "is_demo"],
    )
    writer.writeheader()
    for index in range(30):
        writer.writerow({
            "provider_id": f"synthetic-provider-{index:03}",
            "name": f"Synthetic {specialties[index % len(specialties)]} Practice {index}",
            "specialty": specialties[index % len(specialties)],
            "location": locations[index % len(locations)],
            "consultation_type": "video" if index % 2 else "in-person",
            "is_demo": True,
        })

with (OUTPUT / "interactions.csv").open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["user_id", "provider_id", "interaction", "label"])
    writer.writeheader()
    for user in range(20):
        for provider in range(30):
            if random.random() < 0.22:
                label = 1 if random.random() < 0.7 else 0
                writer.writerow({
                    "user_id": f"synthetic-user-{user:03}",
                    "provider_id": f"synthetic-provider-{provider:03}",
                    "interaction": "view" if label == 0 else "save",
                    "label": label,
                })

(OUTPUT / "manifest.json").write_text(json.dumps({
    "seed": SEED,
    "synthetic": True,
    "provider_count": 30,
    "patient_profile_count": 20,
    "clinical_ground_truth": False,
}, indent=2), encoding="utf-8")
print(f"Generated reproducible synthetic data in {OUTPUT}")
