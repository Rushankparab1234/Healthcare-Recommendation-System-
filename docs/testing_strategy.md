# Testing Strategy

The current backend tests cover:
- Emergency warning detection, negation, incomplete and ambiguous input
- Structured symptom parsing and the absence of symptom-to-specialty inference
- Registration, duplicate-email handling, Argon2 persistence, login, CORS, and protected routes
- Patient-scoped dashboard data, structured assessment, recommendation, provider save, and emergency override
- Provider search/detail and explicit demo/unverified metadata
- Knowledge ingestion, source citations, extractive response, no-source fallback, and source-specific relevance
- Ranking behavior and Precision@K, Recall@K, NDCG@K, MAP@K, and coverage

Frontend component tests cover dashboard API-backed values and knowledge-center rendering. A local browser smoke test covered registration/login, assessment/recommendation, provider search/save/detail, knowledge article navigation, and dashboard updates.

Known gaps: the test database is local SQLite rather than PostgreSQL; browser checks are a manual smoke flow, not an automated cross-browser E2E suite; migrations do not yet establish a versioned baseline for all tables; no clinical validation data exists. Before production, add PostgreSQL CI, isolated database fixtures, broader authorization and security tests, automated E2E flows, and reviewed evaluation datasets.
