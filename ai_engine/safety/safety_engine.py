import re

EMERGENCY_TERMS = (
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "unconscious",
    "suicidal",
    "self harm",
    "severe bleeding",
    "stroke symptoms",
    "face drooping",
)

NEGATION_PATTERN = re.compile(r"\b(no|not|denies|without)\s+(?:[a-z]+\s){0,3}")


def assess_safety(description: str, severity: str | None = None) -> dict:
    text = (description or "").strip().lower()
    emergency_matches = []
    for term in EMERGENCY_TERMS:
        if term in text:
            prefix = text[max(0, text.find(term) - 30):text.find(term)]
            if not NEGATION_PATTERN.search(prefix):
                emergency_matches.append(term)
    if severity and severity.lower() == "critical":
        emergency_matches.append("critical severity")

    if emergency_matches:
        return {
            "status": "emergency",
            "emergency": True,
            "warning_signs": sorted(set(emergency_matches)),
            "guidance": "Seek emergency medical help immediately or call your local emergency number.",
            "normal_ranking_allowed": False,
        }
    if not text:
        return {
            "status": "incomplete",
            "emergency": False,
            "guidance": "Add a symptom description before requesting navigation recommendations.",
            "normal_ranking_allowed": False,
        }
    if len(text.split()) < 3:
        return {
            "status": "ambiguous",
            "emergency": False,
            "guidance": "This description is too brief for useful navigation. Add duration and associated symptoms.",
            "normal_ranking_allowed": False,
        }
    return {
        "status": "review",
        "emergency": False,
        "guidance": "Use these suggestions as healthcare navigation, not a diagnosis.",
        "normal_ranking_allowed": True,
    }
