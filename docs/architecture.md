# Architecture

HealthWise AI uses a modular monolith: the React client communicates with versioned FastAPI routers, the service and AI modules remain independent, and SQLAlchemy isolates persistence behind repositories in a later production phase.

```mermaid
flowchart LR
  User[User] --> UI[React TypeScript UI]
  UI --> API[FastAPI /api/v1]
  API --> Auth[JWT and RBAC]
  API --> Patient[Patient service]
  API --> Safety[Deterministic safety]
  API --> NLP[Symptom processor]
  API --> Rank[Hybrid provider ranker]
  API --> DB[(SQLite or PostgreSQL)]
  Rank --> Providers[Demo provider catalog]
  Safety --> Emergency[Urgent-care guidance]
```

Major external services are optional targets rather than mandatory local dependencies: PostgreSQL/pgvector, Redis, MLflow, and an external LLM.
