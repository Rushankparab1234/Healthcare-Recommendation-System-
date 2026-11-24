# HealthWise AI

HealthWise AI is a full-stack healthcare navigation portfolio project. It accepts structured symptom descriptions, applies deterministic safety checks, and ranks clearly labeled synthetic providers only after a specialty has been explicitly selected. It does not diagnose, prescribe, or replace a licensed professional.

## Implemented in this repository
- React + TypeScript responsive interface.
- FastAPI versioned API with JWT and Argon2 authentication.
- SQLite local database and configurable PostgreSQL SQLAlchemy URL; PostgreSQL has not been integration-tested.
- Patient profile, symptom assessment, provider discovery, recommendation, feedback, and knowledge endpoints.
- Deterministic emergency override and lightweight symptom phrase normalization.
- Transparent weighted provider ranking with explanations.
- Reproducible synthetic provider and interaction data.
- Pytest API and safety tests.
- Docker Compose configuration for local infrastructure.

## Technology
- Frontend: React, TypeScript, Vite
- Backend: FastAPI, Pydantic, SQLAlchemy
- ML/NLP: curated rules, TF-IDF-ready scikit-learn dependency, transparent weighted ranking
- Database: SQLite for local development; PostgreSQL + pgvector target in Docker
- Cache target: Redis
- Tracking target: MLflow
- Deployment: Docker Compose and GitHub Actions templates

## Quick start
### Backend
```powershell
cd C:\AI-Projects\Healthcare-Recommendation-System
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --app-dir backend --reload --port 8000
```

### Frontend
```powershell
cd C:\AI-Projects\Healthcare-Recommendation-System\frontend
npm.cmd run dev
```

Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.

## Configuration
Copy `.env.example` to `.env`. Never commit real secrets. SQLite defaults to the repository-root `healthwise.db`, independent of the launch directory. Development generates a per-process random JWT secret when none is set; production requires a secure `JWT_SECRET_KEY` of at least 32 characters and explicit HTTPS `CORS_ORIGINS`.

The Compose setup requires `POSTGRES_PASSWORD`, `DATABASE_URL`, and `JWT_SECRET_KEY` to be supplied through the environment or an uncommitted `.env` file. PostgreSQL support is configured but remains unverified until the PostgreSQL integration suite runs.

## Synthetic data
Generate reproducible data with:
```powershell
.venv\Scripts\python.exe scripts\generate_synthetic_data.py
```
The generated CSV files are synthetic and must not be interpreted as real patients, providers, or clinical ground truth.

## Safety
Emergency rules are an initial, unvalidated engineering baseline. They require independent human medical review. The application bypasses normal ranking and shows urgent-care guidance when an emergency warning sign is detected.

## Known future work
A production LLM/RAG integration, pgvector ingestion, Redis caching, MLflow promotion workflows, collaborative filtering experiment, formal migrations, and real provider verification require additional external configuration and validation.
