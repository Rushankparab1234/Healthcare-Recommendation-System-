from ai_engine.safety.safety_engine import assess_safety
from ai_engine.symptom_nlp.processor import process_description


def test_emergency_warning_overrides_ranking():
    result = assess_safety("I have severe chest pain and cannot breathe", "severe")
    assert result["emergency"] is True
    assert result["normal_ranking_allowed"] is False


def test_negated_chest_pain_is_not_emergency():
    result = assess_safety("I do not have chest pain, but have a mild cough", "mild")
    assert result["emergency"] is False


def test_missing_description_is_incomplete():
    result = assess_safety("", "mild")
    assert result["status"] == "incomplete"
    assert result["normal_ranking_allowed"] is False


def test_nlp_preserves_uncertainty():
    result = process_description("persistent cough and wheezing")
    assert result["diagnosis"] is None
    assert result["normalized_phrases"] == ["cough", "wheezing"]
    assert result["explicit_specialties"] == []


def test_negated_symptom_is_not_extracted_as_positive():
    result = process_description("No cough, but I have a headache")
    assert result["normalized_phrases"] == ["headache"]
    assert result["negated_terms"] == ["cough"]


def test_specialty_requires_explicit_selection():
    symptom_only = process_description("I have a cough and wheezing for several days")
    selected = process_description("I have a cough and wheezing for several days", "Pulmonology")
    assert symptom_only["explicit_specialties"] == []
    assert selected["explicit_specialties"] == ["Pulmonology"]
