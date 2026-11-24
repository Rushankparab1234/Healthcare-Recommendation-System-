import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.v1.routes import router
from app.core.config import get_settings
from app.database.session import Base, SessionLocal, engine
from app.models import Provider

settings = get_settings()
app = FastAPI(
    title="HealthWise AI API",
    version="1.0.0",
    description="Healthcare navigation API. Educational use only; not a diagnostic or prescribing system.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

Base.metadata.create_all(bind=engine)


def seed_demo_providers() -> None:
    db = SessionLocal()
    try:
        demo_providers = [
            Provider(id="demo-general-1", name="Harbor General Clinic", specialty="General Medicine",
                     location="Mumbai", consultation_type="in-person", is_demo=True, availability_score=0.86),
            Provider(id="demo-cardio-1", name="Riverheart Demo Clinic", specialty="Cardiology",
                     location="Mumbai", consultation_type="video", is_demo=True, availability_score=0.78),
            Provider(id="demo-neuro-1", name="Clearview Neurology Demo", specialty="Neurology",
                     location="Pune", consultation_type="in-person", is_demo=True, availability_score=0.81),
            Provider(id="demo-ortho-1", name="MotionCare Demo Center", specialty="Orthopedics",
                     location="Mumbai", consultation_type="in-person", is_demo=True, availability_score=0.88),
            Provider(id="demo-derma-1", name="Dermacare Demo Practice", specialty="Dermatology",
                     location="Bengaluru", consultation_type="video", is_demo=True, availability_score=0.83),
            Provider(id="demo-gastro-1", name="Digestive Health Demo", specialty="Gastroenterology",
                     location="Mumbai", consultation_type="video", is_demo=True, availability_score=0.77),
            Provider(id="demo-pulmo-1", name="LungCare Demo Practice", specialty="Pulmonology",
                     location="Mumbai", consultation_type="in-person", is_demo=True, availability_score=0.84),
        ]
        existing_ids = {row[0] for row in db.query(Provider.id).all()}
        db.add_all(provider for provider in demo_providers if provider.id not in existing_ids)
        db.commit()
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
seed_demo_providers()


@app.on_event("startup")
def startup() -> None:
    seed_demo_providers()
