import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_engine.evaluation.ranking_metrics import (
    coverage_at_k,
    map_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from ai_engine.recommendation.hybrid_ranker import rank_providers


@dataclass(frozen=True)
class SyntheticProvider:
    id: str
    name: str
    specialty: str
    location: str
    consultation_type: str
    availability_score: float
    is_demo: bool = True


specialties = ["Cardiology", "Dermatology", "General Medicine", "Pulmonology"]
locations = ["Bengaluru", "Mumbai"]
consultation_types = ["in-person", "video"]
providers = [
    SyntheticProvider(
        id=f"synthetic-{specialty.lower().replace(' ', '-')}-{location.lower()}-{consultation}-{availability_index}",
        name=f"Synthetic {specialty} Demo {location} {consultation} {availability_index}",
        specialty=specialty,
        location=location,
        consultation_type=consultation,
        availability_score=0.55 + availability_index * 0.35,
    )
    for specialty in specialties
    for location in locations
    for consultation in consultation_types
    for availability_index in range(2)
]
cases = [
    {"specialty": specialty, "location": location, "consultation_type": consultation}
    for specialty, location, consultation in [
        ("Cardiology", "Mumbai", "video"),
        ("Dermatology", "Bengaluru", "in-person"),
        ("General Medicine", "Mumbai", "in-person"),
        ("Pulmonology", "Bengaluru", "video"),
    ]
]


def evaluate() -> dict:
    baseline_rankings = []
    hybrid_rankings = []
    case_metrics = []
    for case in cases:
        candidates = [provider for provider in providers if provider.specialty == case["specialty"]]
        # This synthetic preference label is not clinical relevance or treatment effectiveness.
        relevant = {
            provider.id for provider in candidates
            if provider.location == case["location"]
            and provider.consultation_type == case["consultation_type"]
        }
        baseline = sorted(candidates, key=lambda provider: provider.name)
        hybrid = rank_providers(
            candidates,
            case["specialty"],
            case["location"],
            case["consultation_type"],
        )
        baseline_ids = [provider.id for provider in baseline]
        hybrid_ids = [item["provider"].id for item in hybrid]
        baseline_rankings.append(baseline_ids)
        hybrid_rankings.append(hybrid_ids)
        case_metrics.append({
            "case": case,
            "relevant_count": len(relevant),
            "baseline": _metrics(baseline_ids, relevant),
            "hybrid": _metrics(hybrid_ids, relevant),
        })
    return {
        "methodology": "Synthetic provider-preference matching only; not clinical relevance or health outcomes.",
        "k": 5,
        "catalog_size": len(providers),
        "cases": case_metrics,
        "aggregate": {
            "baseline": _aggregate(case_metrics, "baseline"),
            "hybrid": _aggregate(case_metrics, "hybrid"),
        },
        "coverage_at_5": {
            "baseline": coverage_at_k(baseline_rankings, len(providers), 5),
            "hybrid": coverage_at_k(hybrid_rankings, len(providers), 5),
        },
    }


def _metrics(ranking: list[str], relevant: set[str]) -> dict[str, float]:
    return {
        "precision_at_5": precision_at_k(ranking, relevant, 5),
        "recall_at_5": recall_at_k(ranking, relevant, 5),
        "ndcg_at_5": ndcg_at_k(ranking, relevant, 5),
        "map_at_5": map_at_k(ranking, relevant, 5),
    }


def _aggregate(cases_data: list[dict], method: str) -> dict[str, float]:
    keys = ("precision_at_5", "recall_at_5", "ndcg_at_5", "map_at_5")
    return {
        key: round(sum(case[method][key] for case in cases_data) / len(cases_data), 4)
        for key in keys
    }


if __name__ == "__main__":
    result = evaluate()
    output = ROOT / "data" / "processed" / "recommendation_evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
