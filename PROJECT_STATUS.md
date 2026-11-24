# HealthWise AI Project Status

## Current status

Runnable educational healthcare-navigation prototype. The UI and APIs are integrated for account creation/login, patient assessments, provider discovery, saved providers, a patient dashboard, and a source-linked knowledge center. This is not a diagnostic, treatment, clinical-triage, booking, or production patient-data system.

## Implemented and verified

- FastAPI versioned API, React/TypeScript/Vite client, SQLAlchemy persistence, JWT authentication, and Argon2 password hashing.
- Registration uses HTTP 201, duplicate email uses HTTP 409, and frontend validation/loading/success/error states are present. CORS allows both `localhost:5173` and `127.0.0.1:5173`.
- Authenticated dashboard counts, recent history, saved providers, profile completion, and recent activity are read from records scoped to the current user. Recommendations use typed response models and render provider, specialty, rank, date, and explanation fields.
- Structured assessments store description, duration, severity, onset, associated symptoms, relevant history, and context. Symptom extraction records terms and negations; it does not infer a diagnosis or specialty.
- Emergency keyword/severity overrides are separate from provider ranking. These are basic, unvalidated safety rules and are not a substitute for emergency services or clinical triage.
- Provider search filters by name, specialty, location, and consultation type. Save/unsave state persists across reload and login; the API client correctly handles the empty HTTP 204 response for removal. Every currently seeded provider and availability signal is explicitly synthetic, unverified, and not bookable.
- Research consent is opt-in, remains optional for normal use, and records/clears an explicit consent timestamp. Legacy consent decisions have no reconstructable historical timestamp.
- Ranking requires a specialty selected by the user (for example, one already suggested by their clinician); it filters to exact specialty and scores location, consultation type, stated preference, and demo availability.
- Knowledge center supports categories, search, article detail, source links, related articles, and loading/error states. Assistant answers are extractive passages from a small locally indexed MedlinePlus source collection, with citations and a no-relevant-source fallback. Retrieval is lexical, not semantic.
- Offline evaluation computes Precision@5, Recall@5, NDCG@5, MAP@5, and catalog coverage for baseline and hybrid rankings. The labeled cases and provider catalogue are synthetic preference fixtures, not clinical relevance or outcome data.
- Alembic revision `0002_consent_and_integrity` is applied to the canonical root SQLite database. SQLite foreign-key enforcement is enabled for application connections; the assessment reference is indexed and constrained.

## Verification results

- Backend/API/security/database tests: **30 passed**, with three framework deprecation warnings.
- Ruff: passed for `backend`, `ai_engine`, and `scripts`.
- Frontend tests: **8 passed** across 5 test files; TypeScript check and production build passed.
- `npm audit`: 0 vulnerabilities.
- Browser smoke flow on local Vite + FastAPI: registered and logged in a development test account, submitted an assessment, generated a recommendation, and verified dashboard totals and typed recommendation details. Provider save survived reload and logout/login; unsave removed the saved state without a UI error.
- Direct SQLite inspection and browser workflow confirmed persisted user/password hash, assessment, recommendation, and provider-save workflow. Backend tests verify provider removal and user isolation at the database/API level.
- The cough-source retrieval regression is verified: the cough question returns only the cough source, and an unrelated question returns no citations with the explicit fallback.
- PostgreSQL schema compilation tests passed, but no PostgreSQL server was available; PostgreSQL connection, migrations, and end-to-end persistence remain unverified.
- Synthetic ranking evaluation was run and saved to `data/processed/recommendation_evaluation.json`. It reports baseline P@5 0.25, R@5 0.625, NDCG@5 0.452, MAP@5 0.3792; hybrid P@5 0.4, R@5 1.0, NDCG@5 1.0, MAP@5 1.0; coverage 0.625 for both. These scores only demonstrate matching against the script's synthetic location/consultation labels.

## Audit and documentation

- Detailed implementation, partial, demo, missing, bug, security, and integration findings: [docs/functionality_audit.md](docs/functionality_audit.md).
- Ranking method and evaluation caveats: [docs/recommendation_engine.md](docs/recommendation_engine.md).
- The original registration failure was a CORS-origin mismatch: the frontend used `127.0.0.1`, which was absent from the backend allowlist.
- The dashboard object rendering came from a legacy recommendation payload with specialty objects. The API now normalizes historical records into typed display properties.
- The provider removal UI error came from parsing the empty body of an HTTP 204 response as JSON. The API client now handles 204 explicitly.
- Dashboard count discrepancies can occur when test records belong to other accounts; recommendations can also be requested without an assessment. Counts are intentionally per authenticated user, and the complete assessment-to-recommendation workflow is covered by tests.

## Phase 2.5 files changed

- Backend: `backend/app/api/v1/routes.py`, `backend/app/schemas.py`, `backend/app/models.py`, `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/dependencies/auth.py`, `backend/app/database/session.py`, `backend/migrations/env.py`, `backend/migrations/versions/0002_consent_and_integrity.py`.
- Backend tests: `backend/tests/conftest.py`, `backend/tests/test_api.py`, `backend/tests/test_security.py`.
- Frontend: `frontend/src/pages/DashboardPage.tsx`, `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/api.test.ts`, `frontend/src/pages/ProfilePage.tsx`, `frontend/src/pages/ProfilePage.test.tsx`, `frontend/src/pages/ProviderDirectory.test.tsx`.
- Configuration and documentation: `.env.example`, `docker-compose.yml`, `alembic.ini`, `README.md`, `PROJECT_STATUS.md`, `docs/functionality_audit.md`, `docs/database_design.md`.

## Known limitations and risks

- Local verification uses the repository-root `healthwise.db`, not PostgreSQL. PostgreSQL connectivity and persistence were not tested.
- Migration history is incomplete: `0002` covers consent/integrity changes, but a full baseline for all existing tables is still required; application startup also uses `Base.metadata.create_all`.
- No embedding model, vector database, or LLM is implemented. The knowledge collection is small and the refresh/ingestion workflow is local/manual.
- The ranking benchmark is synthetic and cannot establish clinical or production recommendation quality.
- Safety rules and the knowledge summaries require ongoing clinical/editorial review; symptom matching can miss or misread context.
- Development uses a random per-process JWT secret if none is configured. Production rejects missing/short secrets and non-HTTPS, wildcard, or malformed CORS origins; supply a securely managed secret and explicit HTTPS origins. Tokens must include expiration and subject claims.
- Browser-stored bearer tokens use `localStorage`; production should consider an XSS-resistant session design and add standard deployment controls such as rate limiting, email verification, password recovery, privacy/data-retention controls, and security headers.
- A secondary `backend\\healthwise.db` created by prior working-directory-dependent runs was left untouched. Select it explicitly through `DATABASE_URL` if its records are needed; it was not merged with the canonical database.
- No real provider verification, qualifications validation, appointment availability, booking, email verification, password reset, or clinical workflow is implemented.
- FastAPI's current startup hook emits a deprecation warning; migrate it to lifespan handlers in a future maintenance pass.

## Recommended next phase

1. Establish a complete Alembic baseline and add PostgreSQL-backed CI/integration testing; do not treat dialect compilation as database verification.
2. Obtain clinical review for safety signals, patient-facing wording, and the explicit specialty-navigation UX.
3. Expand sourced knowledge coverage and evaluate retrieval precision/abstention using reviewed queries; add embeddings only if a measured need justifies the dependency.
4. Replace synthetic providers with a vetted, consented provider data source and truthful eligibility/availability workflows.
5. Add production security, privacy, operational monitoring, backup, and data lifecycle controls before handling real patient information.
