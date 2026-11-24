def location_score(query_location: str | None, provider_location: str) -> float:
    if not query_location:
        return 0.5
    query = " ".join(query_location.casefold().split())
    provider = " ".join(provider_location.casefold().split())
    if query == provider:
        return 1.0
    if query in provider or provider in query:
        return 0.75
    return 0.0


def rank_providers(
    providers: list,
    specialty: str,
    location: str | None = None,
    consultation_type: str | None = None,
    preferences: str | None = None,
) -> list:
    ranked = []
    preference_text = (preferences or "").casefold()
    for provider in providers:
        if provider.specialty.casefold() != specialty.casefold():
            continue

        location_value = location_score(location, provider.location)
        consultation_matches = provider.consultation_type.lower() == (consultation_type or "").lower()
        consultation_value = 1.0 if not consultation_type or consultation_matches else 0.35
        availability = max(0.0, min(1.0, provider.availability_score))
        preference_value = (
            1.0
            if preference_text and provider.consultation_type.casefold() in preference_text
            else 0.5
        )
        weighted = (
            0.55
            + 0.20 * location_value
            + 0.10 * consultation_value
            + 0.10 * availability
            + 0.05 * preference_value
        )
        matched_attributes = [f"selected {provider.specialty} specialty"]
        if location_value == 1.0:
            matched_attributes.append(f"{provider.location} location")
        if consultation_matches and consultation_type:
            matched_attributes.append(f"{provider.consultation_type} consultation")
        if preference_value == 1.0:
            matched_attributes.append(f"{provider.consultation_type} matches stated preference")
        ranked.append({
            "provider": provider,
            "ranking_score": round(weighted, 4),
            "matched_attributes": matched_attributes,
            "explanation": (
                f"Ranked for the explicitly selected {specialty} specialty, location fit, "
                "consultation preference, and demo availability signal."
            ),
            "data_completeness": "demo data; availability is not bookable",
        })
    ranked.sort(key=lambda item: (-item["ranking_score"], item["provider"].name))
    return ranked
