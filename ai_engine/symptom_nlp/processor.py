import re

SYMPTOM_TERMS = (
    "abdominal pain",
    "back pain",
    "blurred vision",
    "chest pain",
    "cough",
    "diarrhea",
    "difficulty breathing",
    "dizziness",
    "fatigue",
    "fever",
    "headache",
    "itching",
    "joint pain",
    "nausea",
    "palpitations",
    "rash",
    "shortness of breath",
    "sore throat",
    "wheezing",
)

SPECIALTY_TERMS = (
    "Cardiology",
    "Dermatology",
    "Gastroenterology",
    "General Medicine",
    "Mental Health",
    "Neurology",
    "Ophthalmology",
    "Orthopedics",
    "Pulmonology",
)

NEGATION_WORDS = {"no", "not", "never", "without", "denies", "denied"}


def _is_negated(text: str, start: int) -> bool:
    preceding_text = text[max(0, start - 60):start]
    preceding_text = re.split(r"[,;.!?]|\b(?:but|however|although|and)\b", preceding_text)[-1]
    preceding = re.findall(r"[a-z']+", preceding_text)
    window = preceding[-3:]
    return any(word in NEGATION_WORDS or word in {"don't", "doesn't", "didn't"} for word in window)


def process_description(description: str, requested_specialty: str | None = None) -> dict:
    text = description.lower().strip()
    mentions = []
    negated = []
    for term in SYMPTOM_TERMS:
        for match in re.finditer(rf"(?<!\w){re.escape(term)}(?!\w)", text):
            entry = {"phrase": term}
            if _is_negated(text, match.start()):
                negated.append(entry)
            else:
                mentions.append(entry)

    explicit_specialties = []
    requested = (requested_specialty or "").strip()
    for specialty in SPECIALTY_TERMS:
        if requested.casefold() == specialty.casefold():
            explicit_specialties = [specialty]
            break
        pattern = rf"(?<!\w){re.escape(specialty.lower())}(?!\w)"
        if re.search(pattern, text):
            explicit_specialties.append(specialty)

    return {
        "normalized_phrases": sorted({item["phrase"] for item in mentions}),
        "negated_terms": sorted({item["phrase"] for item in negated}),
        "explicit_specialties": sorted(set(explicit_specialties)),
        "diagnosis": None,
        "uncertainty": "Symptoms are recorded as stated. No diagnosis or specialty is inferred from symptoms.",
    }
