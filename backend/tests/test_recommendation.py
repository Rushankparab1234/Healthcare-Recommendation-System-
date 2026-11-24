from types import SimpleNamespace

from ai_engine.recommendation.hybrid_ranker import rank_providers


def test_hybrid_ranking_uses_selected_specialty_location_consultation_and_preference():
    providers = [
        SimpleNamespace(
            id="match",
            name="Matching demo",
            specialty="Cardiology",
            location="Mumbai",
            consultation_type="video",
            availability_score=0.6,
        ),
        SimpleNamespace(
            id="location-mismatch",
            name="Other location",
            specialty="Cardiology",
            location="Pune",
            consultation_type="in-person",
            availability_score=1.0,
        ),
        SimpleNamespace(
            id="wrong-specialty",
            name="Unrelated demo",
            specialty="Neurology",
            location="Mumbai",
            consultation_type="video",
            availability_score=1.0,
        ),
    ]
    results = rank_providers(
        providers,
        specialty="Cardiology",
        location="Mumbai",
        consultation_type="video",
        preferences="video consultation",
    )
    assert [item["provider"].id for item in results] == ["match", "location-mismatch"]
    assert "Mumbai location" in results[0]["matched_attributes"]
    assert "video matches stated preference" in results[0]["matched_attributes"]


def test_ranker_does_not_fall_back_to_unrelated_specialties():
    provider = SimpleNamespace(
        id="neuro",
        name="Neurology demo",
        specialty="Neurology",
        location="Mumbai",
        consultation_type="video",
        availability_score=0.9,
    )
    assert rank_providers([provider], specialty="Cardiology") == []
