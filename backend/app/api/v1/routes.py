import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_engine.recommendation.hybrid_ranker import rank_providers
from ai_engine.safety.safety_engine import assess_safety
from ai_engine.symptom_nlp.processor import process_description
from app.core.security import create_access_token, hash_password, verify_password
from app.database.session import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models import (
    Feedback,
    PatientProfile,
    Provider,
    Recommendation,
    SavedProvider,
    SymptomAssessment,
    User,
)
from app.schemas import (
    AssistantRequest,
    FeedbackRequest,
    LoginRequest,
    PatientDashboardResponse,
    ProfileRequest,
    RecommendationRequest,
    RegisterRequest,
    SymptomAssessmentRequest,
    TokenResponse,
)
from app.services.knowledge import (
    answer_from_sources,
    get_article,
    list_articles,
    related_articles,
)

router = APIRouter(prefix="/api/v1")


def provider_response(provider: Provider) -> dict[str, Any]:
    is_demo = provider.is_demo
    return {
        "id": provider.id,
        "name": provider.name,
        "specialty": provider.specialty,
        "location": provider.location,
        "consultation_type": provider.consultation_type,
        "is_demo": is_demo,
        "verification_status": "synthetic demo — not verified" if is_demo else "verification not recorded",
        "qualification_information": (
            "Not provided; this synthetic demo record has no verified qualifications."
            if is_demo
            else "No qualification details recorded."
        ),
        "availability": {
            "demo_signal": provider.availability_score,
            "is_bookable": False,
            "description": "Synthetic ranking signal only; not real appointment availability.",
        },
    }


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected", "mode": "local-sqlite-or-configured-database"}


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().casefold()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role="patient",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from exc
    db.refresh(user)
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        full_name=user.full_name,
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().casefold()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        full_name=user.full_name,
    )


@router.get("/users/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}


@router.get("/patients/me")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if profile is None:
        return None
    return {
        "age": profile.age,
        "sex": profile.sex,
        "location": profile.location,
        "medical_history": profile.medical_history,
        "allergies": profile.allergies,
        "preferences": profile.preferences,
        "consent_research": profile.consent_research,
        "consent_research_at": (
            _utc_datetime(profile.consent_research_at).isoformat()
            if profile.consent_research_at
            else None
        ),
    }


@router.put("/patients/me")
def update_profile(payload: ProfileRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if profile is None:
        profile = PatientProfile(user_id=user.id)
        db.add(profile)
    updates = payload.model_dump(exclude_unset=True)
    if "consent_research" in updates:
        if updates["consent_research"]:
            if not profile.consent_research or profile.consent_research_at is None:
                profile.consent_research_at = datetime.now(timezone.utc)
        else:
            profile.consent_research_at = None
    for field, value in updates.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return {
        "status": "saved",
        "profile": {
            **updates,
            "consent_research": profile.consent_research,
            "consent_research_at": (
                _utc_datetime(profile.consent_research_at).isoformat()
                if profile.consent_research_at
                else None
            ),
        },
    }


@router.post("/symptoms/assess")
def assess_symptoms(
    payload: SymptomAssessmentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    description = payload.description.strip()
    safety_text = " ".join([description, *payload.associated_symptoms])
    safety = assess_safety(safety_text, payload.severity)
    nlp = process_description(" ".join([description, *payload.associated_symptoms]))
    assessment = SymptomAssessment(
        user_id=user.id,
        description=description,
        duration=payload.duration,
        severity=payload.severity,
        is_emergency=safety["emergency"],
        result_json=json.dumps({
            "safety": safety,
            "symptom_processing": nlp,
            "structured_context": {
                "onset": payload.onset,
                "associated_symptoms": payload.associated_symptoms,
                "relevant_medical_history": payload.relevant_medical_history,
                "additional_context": payload.additional_context,
            },
        }),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return {
        "assessment_id": assessment.id,
        "safety": safety,
        "symptom_processing": nlp,
        "needs_more_information": safety["status"] in {"incomplete", "ambiguous"},
        "follow_up": (
            "Add more detail about the concern and its duration before continuing."
            if safety["status"] in {"incomplete", "ambiguous"}
            else None
        ),
    }


@router.post("/recommendations")
def get_recommendations(
    payload: RecommendationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessment = None
    if payload.assessment_id:
        assessment = db.get(SymptomAssessment, payload.assessment_id)
        if assessment is None or assessment.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        description = assessment.description
        severity = assessment.severity
        assessment_result = json.loads(assessment.result_json)
        safety = assessment_result["safety"]
    else:
        description = (payload.description or "").strip()
        severity = payload.severity
        safety = assess_safety(description, severity)

    nlp = process_description(description, payload.requested_specialty)
    specialties = [payload.requested_specialty.strip()] if payload.requested_specialty else []

    if safety["emergency"]:
        return {
            "safety": safety,
            "items": [],
            "specialties": [],
            "emergency_override": True,
            "needs_more_information": False,
        }
    if safety["status"] in {"incomplete", "ambiguous"}:
        return {
            "safety": safety,
            "items": [],
            "specialties": specialties,
            "emergency_override": False,
            "needs_more_information": True,
            "follow_up": "Please add more detail before requesting provider navigation.",
        }
    if not specialties:
        return {
            "safety": safety,
            "items": [],
            "specialties": [],
            "emergency_override": False,
            "needs_more_information": True,
            "follow_up": (
                "HealthWise does not infer a specialty from symptoms. "
                "Choose a specialty already suggested by your healthcare professional, "
                "or discuss your concern with one."
            ),
        }

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    location = payload.location or (profile.location if profile else None)
    consultation_type = payload.consultation_type
    preferences = profile.preferences if profile else None
    providers = db.query(Provider).filter(Provider.is_demo.is_(True)).all()
    ranked_items = []
    for specialty in specialties:
        ranked_items.extend(
            rank_providers(
                providers,
                specialty,
                location,
                consultation_type,
                preferences,
            )
        )
    ranked_items.sort(key=lambda item: (-item["ranking_score"], item["provider"].name))

    result_items = [
        {
            "rank": index,
            "provider_id": item["provider"].id,
            "provider_name": item["provider"].name,
            "specialty": item["provider"].specialty,
            "location": item["provider"].location,
            "consultation_type": item["provider"].consultation_type,
            "is_demo": item["provider"].is_demo,
            "verification_status": "synthetic demo — not verified",
            "qualification_information": "Not provided; this synthetic demo record has no verified qualifications.",
            "availability": provider_response(item["provider"])["availability"],
            "ranking_score": item["ranking_score"],
            "matched_attributes": item["matched_attributes"],
            "explanation": item["explanation"],
            "data_completeness": item["data_completeness"],
        }
        for index, item in enumerate(ranked_items[:10], start=1)
    ]
    result_json = json.dumps({
        "specialties": specialties,
        "items": result_items,
        "safety": safety,
    })
    recommendation = Recommendation(
        user_id=user.id,
        assessment_id=assessment.id if assessment else None,
        result_json=result_json,
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return {
        "recommendation_id": recommendation.id,
        "specialties": specialties,
        "items": result_items,
        "safety": safety,
        "emergency_override": False,
        "needs_more_information": not result_items,
        "follow_up": (
            "No matching demo providers are available for this explicitly selected specialty."
            if not result_items
            else None
        ),
        "limitations": nlp["uncertainty"],
    }


@router.get("/providers")
def list_providers(
    search: str | None = Query(default=None, max_length=100),
    specialty: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=255),
    consultation_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
):
    query = db.query(Provider)
    if search:
        query = query.filter(Provider.name.ilike(f"%{search.strip()}%"))
    if specialty:
        query = query.filter(Provider.specialty.ilike(f"%{specialty}%"))
    if location:
        query = query.filter(Provider.location.ilike(f"%{location}%"))
    if consultation_type:
        query = query.filter(Provider.consultation_type.ilike(f"%{consultation_type}%"))
    providers = query.order_by(Provider.name).limit(100).all()
    return [provider_response(item) for item in providers]


@router.get("/specialties")
def list_specialties(db: Session = Depends(get_db)):
    names = (
        db.query(Provider.specialty)
        .filter(Provider.is_demo.is_(True))
        .distinct()
        .order_by(Provider.specialty)
        .all()
    )
    return [{"name": name, "source": "demo provider catalogue"} for (name,) in names]


@router.get("/providers/{provider_id}")
def provider_detail(provider_id: str, db: Session = Depends(get_db)):
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return provider_response(provider)


@router.post("/providers/{provider_id}/save", status_code=status.HTTP_201_CREATED)
def save_provider(
    provider_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    existing = db.get(SavedProvider, {"user_id": user.id, "provider_id": provider_id})
    if existing is None:
        db.add(SavedProvider(user_id=user.id, provider_id=provider_id))
        db.commit()
    return {"status": "saved", "provider_id": provider_id}


@router.delete("/providers/{provider_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def unsave_provider(
    provider_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved = db.get(SavedProvider, {"user_id": user.id, "provider_id": provider_id})
    if saved is not None:
        db.delete(saved)
        db.commit()


@router.get("/patients/me/dashboard", response_model=PatientDashboardResponse)
def patient_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    assessments = (
        db.query(SymptomAssessment)
        .filter(SymptomAssessment.user_id == user.id)
        .order_by(SymptomAssessment.created_at.desc())
        .limit(5)
        .all()
    )
    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.id)
        .order_by(Recommendation.created_at.desc())
        .limit(5)
        .all()
    )
    saved = (
        db.query(SavedProvider, Provider)
        .join(Provider, SavedProvider.provider_id == Provider.id)
        .filter(SavedProvider.user_id == user.id)
        .order_by(SavedProvider.saved_at.desc())
        .limit(20)
        .all()
    )
    profile_fields = ("age", "sex", "location", "medical_history", "allergies", "preferences")
    completed_fields = sum(
        1 for field in profile_fields
        if profile and getattr(profile, field) not in (None, "")
    )
    recent_assessments = [
        {
            "id": item.id,
            "created_at": _utc_datetime(item.created_at).isoformat(),
            "severity": item.severity,
            "emergency": item.is_emergency,
            "symptoms": json.loads(item.result_json)["symptom_processing"]["normalized_phrases"],
        }
        for item in assessments
    ]
    recent_recommendations = []
    for item in recommendations:
        result = json.loads(item.result_json)
        result_items = []
        for index, result_item in enumerate(result.get("items") or [], start=1):
            if not isinstance(result_item, dict):
                continue
            provider_name = result_item.get("provider_name")
            specialty = result_item.get("specialty")
            if not isinstance(provider_name, str) or not provider_name:
                continue
            if not isinstance(specialty, str) or not specialty:
                specialty = "Specialty not recorded"
            rank = result_item.get("rank")
            if not isinstance(rank, int) or isinstance(rank, bool):
                rank = index
            explanation = result_item.get("explanation")
            if not isinstance(explanation, str) or not explanation:
                explanation = "No ranking explanation was recorded."
            provider_id = result_item.get("provider_id")
            result_items.append({
                "provider_id": provider_id if isinstance(provider_id, str) else None,
                "provider_name": provider_name,
                "specialty": specialty,
                "rank": rank,
                "explanation": explanation,
            })
        recent_recommendations.append({
            "id": item.id,
            "created_at": _utc_datetime(item.created_at).isoformat(),
            "items": result_items,
        })
    activity = [
        {"type": "assessment", "id": item["id"], "created_at": item["created_at"]}
        for item in recent_assessments
    ] + [
        {"type": "recommendation", "id": item["id"], "created_at": item["created_at"]}
        for item in recent_recommendations
    ]
    activity.sort(key=lambda item: item["created_at"], reverse=True)
    return {
        "assessment_count": db.query(SymptomAssessment).filter(SymptomAssessment.user_id == user.id).count(),
        "recommendation_count": db.query(Recommendation).filter(Recommendation.user_id == user.id).count(),
        "saved_provider_count": db.query(SavedProvider).filter(SavedProvider.user_id == user.id).count(),
        "profile_completion": {
            "completed": completed_fields,
            "total": len(profile_fields),
            "percentage": round(100 * completed_fields / len(profile_fields)),
        },
        "recent_assessments": recent_assessments,
        "recent_recommendations": recent_recommendations,
        "saved_providers": [provider_response(provider) for _, provider in saved],
        "recent_activity": activity[:10],
    }


@router.post("/feedback")
def submit_feedback(
    payload: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recommendation_id = payload.recommendation_id
    recommendation = db.get(Recommendation, recommendation_id)
    if recommendation is None or recommendation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    feedback = Feedback(
        recommendation_id=recommendation_id,
        useful=payload.useful,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    return {"status": "recorded"}


@router.post("/assistant")
def assistant(payload: AssistantRequest, user: User = Depends(get_current_user)):
    question = payload.question.strip()
    safety = assess_safety(question)
    if safety["emergency"]:
        return {
            "answer": safety["guidance"],
            "sources": [],
            "retrieval_status": "emergency-safety",
            "generation": "deterministic-safety",
            "caution": "This is not a clinical assessment.",
        }
    if not question:
        raise HTTPException(status_code=422, detail="Question is required")
    response = answer_from_sources(question)
    return {
        **response,
        "caution": "General health education only; not a diagnosis or treatment recommendation.",
    }


@router.get("/knowledge")
def knowledge(
    search: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=100),
):
    return list_articles(search, category)


@router.get("/knowledge/categories")
def knowledge_categories():
    return sorted({article["category"] for article in list_articles()})


@router.get("/knowledge/{article_id}")
def knowledge_article(article_id: str):
    article = get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge article not found")
    return {**article, "related_articles": related_articles(article_id)}


@router.get("/analytics")
def analytics(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "users": db.query(User).count(),
        "providers": db.query(Provider).count(),
        "assessments": db.query(SymptomAssessment).count(),
        "recommendations": db.query(Recommendation).count(),
        "feedback": db.query(Feedback).count(),
        "demo_content": True,
    }
