import json
import uuid
from datetime import datetime

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.database.session import SessionLocal, engine
from app.main import app
from app.models import Recommendation, SavedProvider, User
from fastapi.testclient import TestClient
from sqlalchemy import Text, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_registration_login_profile_and_recommendation():
    email = f"portfolio.{uuid.uuid4()}@example.com"
    password = "A-long-secure-password-123"
    register = client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Portfolio Test",
        "password": password,
    })
    assert register.status_code == 201
    registration_body = register.json()
    token = registration_body["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    duplicate = client.post("/api/v1/auth/register", json={
        "email": email.upper(),
        "full_name": "Portfolio Test",
        "password": password,
    })
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Email is already registered"

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    assert login.json()["full_name"] == "Portfolio Test"

    user_id = decode_access_token(token)["sub"]
    with SessionLocal() as db:
        persisted_user = db.get(User, user_id)
        assert persisted_user is not None
        assert persisted_user.email == email
        assert persisted_user.hashed_password != password
        assert verify_password(password, persisted_user.hashed_password)

    profile = client.put("/api/v1/patients/me", headers=headers, json={
        "age": 32,
        "location": "Mumbai",
        "preferences": "video consultation",
    })
    assert profile.status_code == 200

    assessment = client.post("/api/v1/symptoms/assess", headers=headers, json={
        "description": "I have had a persistent cough and wheezing for three days",
        "duration": "three days",
        "severity": "moderate",
        "onset": "gradual",
        "associated_symptoms": ["wheezing"],
        "relevant_medical_history": "None reported",
        "additional_context": "Symptoms began after a cold",
    })
    assert assessment.status_code == 200
    assert assessment.json()["symptom_processing"]["explicit_specialties"] == []

    recommendations = client.post("/api/v1/recommendations", headers=headers, json={
        "assessment_id": assessment.json()["assessment_id"],
        "requested_specialty": "Pulmonology",
        "location": "Mumbai",
    })
    assert recommendations.status_code == 200
    body = recommendations.json()
    assert body["emergency_override"] is False
    assert body["items"]
    assert all(item["specialty"] == "Pulmonology" for item in body["items"])

    save = client.post(
        f"/api/v1/providers/{body['items'][0]['provider_id']}/save",
        headers=headers,
    )
    assert save.status_code == 201
    dashboard = client.get("/api/v1/patients/me/dashboard", headers=headers)
    assert dashboard.status_code == 200
    dashboard_data = dashboard.json()
    assert dashboard_data["assessment_count"] == 1
    assert dashboard_data["recommendation_count"] == 1
    assert dashboard_data["saved_provider_count"] == 1
    assert dashboard_data["profile_completion"]["percentage"] > 0
    recent = dashboard_data["recent_recommendations"][0]
    assert recent["id"] == body["recommendation_id"]
    assert datetime.fromisoformat(recent["created_at"])
    assert recent["items"][0]["provider_name"] == body["items"][0]["provider_name"]
    assert recent["items"][0]["specialty"] == "Pulmonology"
    assert recent["items"][0]["rank"] == 1
    assert recent["items"][0]["explanation"] == body["items"][0]["explanation"]


def test_dashboard_normalizes_legacy_recommendation_objects():
    token = client.post("/api/v1/auth/register", json={
        "email": f"legacy-dashboard.{uuid.uuid4()}@example.com",
        "full_name": "Legacy Dashboard",
        "password": "A-long-secure-password-123",
    }).json()["access_token"]
    user_id = decode_access_token(token)["sub"]
    headers = {"Authorization": f"Bearer {token}"}
    legacy_result = {
        "specialties": [{"specialty": "Pulmonology", "match_strength": "indicative"}],
        "items": [{
            "rank": 1,
            "provider_id": "demo-pulmo-1",
            "provider_name": "LungCare Demo Practice",
            "specialty": "Pulmonology",
            "explanation": "Legacy ranked result.",
        }],
    }
    with SessionLocal() as db:
        recommendation = Recommendation(
            user_id=user_id,
            result_json=json.dumps(legacy_result),
        )
        db.add(recommendation)
        db.commit()
        recommendation_id = recommendation.id

    dashboard = client.get("/api/v1/patients/me/dashboard", headers=headers)
    assert dashboard.status_code == 200
    result = dashboard.json()
    assert result["assessment_count"] == 0
    assert result["recommendation_count"] == 1
    recommendation = result["recent_recommendations"][0]
    assert recommendation["id"] == recommendation_id
    assert recommendation["items"] == [{
        "provider_id": "demo-pulmo-1",
        "provider_name": "LungCare Demo Practice",
        "specialty": "Pulmonology",
        "rank": 1,
        "explanation": "Legacy ranked result.",
    }]


def test_saved_provider_persists_across_login_and_is_user_scoped():
    email = f"saved-owner.{uuid.uuid4()}@example.com"
    password = "A-long-secure-password-123"
    owner_token = client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Saved Provider Owner",
        "password": password,
    }).json()["access_token"]
    other_token = client.post("/api/v1/auth/register", json={
        "email": f"saved-other.{uuid.uuid4()}@example.com",
        "full_name": "Other Patient",
        "password": password,
    }).json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    provider_id = "demo-pulmo-1"

    saved = client.post(f"/api/v1/providers/{provider_id}/save", headers=owner_headers)
    assert saved.status_code == 201
    assert client.post(f"/api/v1/providers/{provider_id}/save", headers=owner_headers).status_code == 201
    with SessionLocal() as db:
        owner_id = decode_access_token(owner_token)["sub"]
        assert db.query(SavedProvider).filter_by(user_id=owner_id, provider_id=provider_id).count() == 1

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    relogin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    persisted = client.get("/api/v1/patients/me/dashboard", headers=relogin_headers).json()
    assert persisted["saved_providers"][0]["id"] == provider_id
    assert client.get("/api/v1/patients/me/dashboard", headers=other_headers).json()["saved_providers"] == []

    assert client.delete(f"/api/v1/providers/{provider_id}/save", headers=other_headers).status_code == 204
    assert client.get("/api/v1/patients/me/dashboard", headers=relogin_headers).json()["saved_provider_count"] == 1
    assert client.delete(f"/api/v1/providers/{provider_id}/save", headers=relogin_headers).status_code == 204
    after_logout_login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    final_headers = {"Authorization": f"Bearer {after_logout_login.json()['access_token']}"}
    assert client.get("/api/v1/patients/me/dashboard", headers=final_headers).json()["saved_provider_count"] == 0
    with SessionLocal() as db:
        assert db.query(SavedProvider).filter_by(user_id=owner_id, provider_id=provider_id).count() == 0


def test_research_consent_defaults_off_is_timestamped_and_not_required():
    token = client.post("/api/v1/auth/register", json={
        "email": f"consent.{uuid.uuid4()}@example.com",
        "full_name": "Consent Test",
        "password": "A-long-secure-password-123",
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/patients/me", headers=headers).json() is None
    profile = client.put("/api/v1/patients/me", headers=headers, json={"location": "Mumbai"})
    assert profile.status_code == 200
    stored = client.get("/api/v1/patients/me", headers=headers).json()
    assert stored["consent_research"] is False
    assert stored["consent_research_at"] is None

    assessment = client.post("/api/v1/symptoms/assess", headers=headers, json={
        "description": "A mild cough for several days",
    })
    assert assessment.status_code == 200

    opted_in = client.put("/api/v1/patients/me", headers=headers, json={"consent_research": True})
    assert opted_in.status_code == 200
    timestamp = opted_in.json()["profile"]["consent_research_at"]
    assert timestamp and datetime.fromisoformat(timestamp).tzinfo is not None
    opted_out = client.put("/api/v1/patients/me", headers=headers, json={"consent_research": False})
    assert opted_out.status_code == 200
    assert opted_out.json()["profile"]["consent_research_at"] is None
    stored = client.get("/api/v1/patients/me", headers=headers).json()
    assert stored["consent_research"] is False
    assert stored["consent_research_at"] is None


def test_analytics_role_is_checked_against_database_user():
    patient_token = client.post("/api/v1/auth/register", json={
        "email": f"role-patient.{uuid.uuid4()}@example.com",
        "full_name": "Patient Role",
        "password": "A-long-secure-password-123",
    }).json()["access_token"]
    assert client.get(
        "/api/v1/analytics",
        headers={"Authorization": f"Bearer {patient_token}"},
    ).status_code == 403

    with SessionLocal() as db:
        admin = User(
            email=f"role-admin.{uuid.uuid4()}@example.com",
            full_name="Admin Role",
            hashed_password=hash_password("A-long-secure-password-123"),
            role="admin",
        )
        db.add(admin)
        db.commit()
        admin_id = admin.id
    admin_token = create_access_token(admin_id, "admin")
    response = client.get("/api/v1/analytics", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200


def test_sqlite_integrity_constraints_and_uuid_storage():
    inspector = inspect(engine)
    assert any(index["unique"] for index in inspector.get_indexes("users") if index["name"] == "ix_users_email")
    assert inspector.get_pk_constraint("saved_providers")["constrained_columns"] == ["user_id", "provider_id"]
    assert any(
        "assessment_id" in foreign_key["constrained_columns"]
        for foreign_key in inspector.get_foreign_keys("recommendations")
    )
    assert any(
        index["name"] == "ix_recommendations_assessment_id"
        for index in inspector.get_indexes("recommendations")
    )
    assert inspector.get_unique_constraints("patient_profiles")
    assert isinstance(Recommendation.__table__.c.result_json.type, Text)
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []

    token = client.post("/api/v1/auth/register", json={
        "email": f"uuid-check.{uuid.uuid4()}@example.com",
        "full_name": "UUID Test",
        "password": "A-long-secure-password-123",
    }).json()["access_token"]
    assert str(uuid.UUID(decode_access_token(token)["sub"]))


def test_model_schema_compiles_for_postgresql_without_claiming_connection_support():
    sql = {
        table.name: str(CreateTable(table).compile(dialect=postgresql.dialect()))
        for table in Recommendation.metadata.sorted_tables
    }
    assert "FOREIGN KEY(assessment_id)" in sql["recommendations"]
    assert "consent_research_at" in sql["patient_profiles"]
    assert "result_json TEXT" in sql["recommendations"]


def test_symptoms_do_not_infer_specialty_and_ambiguous_needs_follow_up():
    registration = client.post("/api/v1/auth/register", json={
        "email": f"navigation.{uuid.uuid4()}@example.com",
        "full_name": "Navigation Test",
        "password": "A-long-secure-password-123",
    })
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    assessment = client.post("/api/v1/symptoms/assess", headers=headers, json={
        "description": "cough",
    })
    assert assessment.status_code == 200
    assert assessment.json()["needs_more_information"] is True
    result = client.post("/api/v1/recommendations", headers=headers, json={
        "description": "I have a cough and wheezing for several days",
    })
    assert result.status_code == 200
    assert result.json()["items"] == []
    assert result.json()["needs_more_information"] is True
    assert result.json()["specialties"] == []


def test_patient_dashboard_is_authenticated_and_scoped():
    first = client.post("/api/v1/auth/register", json={
        "email": f"dashboard1.{uuid.uuid4()}@example.com",
        "full_name": "Dashboard One",
        "password": "A-long-secure-password-123",
    }).json()["access_token"]
    second = client.post("/api/v1/auth/register", json={
        "email": f"dashboard2.{uuid.uuid4()}@example.com",
        "full_name": "Dashboard Two",
        "password": "A-long-secure-password-123",
    }).json()["access_token"]
    first_headers = {"Authorization": f"Bearer {first}"}
    second_headers = {"Authorization": f"Bearer {second}"}
    created = client.post("/api/v1/symptoms/assess", headers=first_headers, json={
        "description": "A persistent cough for several days",
    })
    assert created.status_code == 200
    assert client.get("/api/v1/patients/me/dashboard").status_code == 401
    first_dashboard = client.get("/api/v1/patients/me/dashboard", headers=first_headers).json()
    second_dashboard = client.get("/api/v1/patients/me/dashboard", headers=second_headers).json()
    assert first_dashboard["assessment_count"] == 1
    assert second_dashboard["assessment_count"] == 0
    cross_user_recommendation = client.post(
        "/api/v1/recommendations",
        headers=second_headers,
        json={"assessment_id": created.json()["assessment_id"], "requested_specialty": "Pulmonology"},
    )
    assert cross_user_recommendation.status_code == 404


def test_emergency_recommendation_has_no_normal_items():
    email = f"emergency.{uuid.uuid4()}@example.com"
    register = client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Emergency Test",
        "password": "A-long-secure-password-123",
    })
    token = register.json()["access_token"]
    response = client.post("/api/v1/recommendations",
        headers={"Authorization": f"Bearer {token}"},
        json={"description": "sudden chest pain and cannot breathe", "severity": "severe"},
    )
    assert response.status_code == 200
    assert response.json()["emergency_override"] is True
    assert response.json()["items"] == []


def test_registration_cors_allows_127_host():
    response = client.options(
        "/api/v1/auth/register",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_provider_search_detail_and_demo_verification_fields():
    search = client.get("/api/v1/providers", params={
        "search": "LungCare",
        "specialty": "Pulmonology",
        "location": "Mumbai",
        "consultation_type": "in-person",
    })
    assert search.status_code == 200
    assert len(search.json()) == 1
    provider = search.json()[0]
    assert provider["is_demo"] is True
    assert "not verified" in provider["verification_status"]
    assert provider["availability"]["is_bookable"] is False
    detail = client.get(f"/api/v1/providers/{provider['id']}")
    assert detail.status_code == 200
    assert "synthetic demo" in detail.json()["qualification_information"]
