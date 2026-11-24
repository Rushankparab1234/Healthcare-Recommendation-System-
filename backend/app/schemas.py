from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class ProfileRequest(BaseModel):
    age: int | None = Field(default=None, ge=0, le=130)
    sex: str | None = None
    location: str | None = None
    medical_history: str | None = None
    allergies: str | None = None
    preferences: str | None = None
    consent_research: bool = False


class DashboardRecommendationItem(BaseModel):
    provider_id: str | None = None
    provider_name: str
    specialty: str
    rank: int
    explanation: str


class DashboardRecommendation(BaseModel):
    id: str
    created_at: datetime
    items: list[DashboardRecommendationItem]


class PatientDashboardResponse(BaseModel):
    assessment_count: int
    recommendation_count: int
    saved_provider_count: int
    profile_completion: dict[str, int]
    recent_assessments: list[dict]
    recent_recommendations: list[DashboardRecommendation]
    saved_providers: list[dict]
    recent_activity: list[dict]


class SymptomAssessmentRequest(BaseModel):
    description: str = Field(min_length=3, max_length=2000)
    duration: str | None = Field(default=None, max_length=100)
    severity: Literal["mild", "moderate", "severe", "critical"] | None = None
    onset: str | None = Field(default=None, max_length=100)
    associated_symptoms: list[str] = Field(default_factory=list, max_length=20)
    relevant_medical_history: str | None = Field(default=None, max_length=2000)
    additional_context: str | None = Field(default=None, max_length=2000)

    @field_validator("associated_symptoms")
    @classmethod
    def limit_associated_symptoms(cls, values: list[str]) -> list[str]:
        if any(len(value) > 100 for value in values):
            raise ValueError("Associated symptom values must be 100 characters or fewer")
        return [value.strip() for value in values if value.strip()]


class RecommendationRequest(BaseModel):
    assessment_id: str | None = None
    description: str | None = Field(default=None, max_length=2000)
    severity: Literal["mild", "moderate", "severe", "critical"] | None = None
    requested_specialty: str | None = Field(default=None, min_length=2, max_length=100)
    location: str | None = Field(default=None, max_length=255)
    consultation_type: Literal["in-person", "video"] | None = None


class FeedbackRequest(BaseModel):
    recommendation_id: str
    useful: bool
    comment: str | None = Field(default=None, max_length=500)


class AssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
