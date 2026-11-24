# HealthWise AI Functionality Audit

## Scope and evidence

Reviewed the React/TypeScript pages and API client, FastAPI routes and schemas, SQLAlchemy models, Alembic configuration, safety/symptom/ranking modules, knowledge ingestion/retrieval, and their tests. Findings are based on implementation plus the test and local-browser checks listed below; a visible page alone is not treated as proof of backend functionality.

## Feature status

| Area | Status | Evidence / limitation |
|---|---|---|
| Registration and login | Implemented for local development | FastAPI validates inputs, hashes passwords with Argon2, stores users, returns JWTs; duplicate email is HTTP 409. Browser registration and a subsequent login succeeded. Production requires an environment-provided secret of at least 32 characters and explicit HTTPS CORS origins. No email verification, password reset, or rate limiting. |
| CORS and API URL | Implemented for the two local Vite origins | API URL follows the page protocol/hostname unless `VITE_API_URL` is set. Backend allows `localhost:5173` and `127.0.0.1:5173`; the registration failure was caused by the latter origin being absent from the CORS allowlist. |
| Patient dashboard | Implemented | Counts, recent assessments/recommendations, saved providers, profile completion, and recent activity are fetched from the authenticated dashboard endpoint and filtered by the current user ID. Recent recommendations have typed provider, specialty, rank, date, and explanation fields; workflow tests verify the test account's records. |
| Symptom assessment | Partially implemented | Form captures description, duration, severity, onset, associated symptoms, relevant history, and context. Lightweight phrase extraction and local negation handling are implemented; it does not diagnose. This is not a validated clinical NLP model; negation/context parsing has limited rules. |
| Emergency safety | Partially implemented / unvalidated | Deterministic keyword and critical-severity checks run separately and before ordinary ranking. Unit tests cover selected emergency, negated, incomplete, and ambiguous examples. The rules are not clinically reviewed and cannot safely establish that an emergency is absent. |
| Provider recommendation | Implemented as a synthetic demo ranker | Exact specialty eligibility plus transparent weighted ranking for location, consultation, profile preference, and synthetic availability. The user must choose an explicit specialty; symptoms do not produce specialty recommendations. No clinical suitability or treatment claim is made. |
| Ranking evaluation | Implemented for synthetic fixtures only | Script computes Precision@5, Recall@5, NDCG@5, MAP@5, coverage, and baseline/hybrid comparison. Labels encode location/consultation preference and do not measure clinical relevance or outcomes. |
| Provider discovery | Implemented against demo catalogue | Search, specialty/location/consultation filters, details, save/unsave, and availability/qualification/verification disclosures. All currently seeded entries are synthetic, unverified, and non-bookable. There is no live provider feed, booking, or credential verification. |
| Healthcare assistant | Partially implemented | Local source retrieval, extractive passages, source links, deterministic safety override, and a no-relevant-source fallback. Retrieval is lexical and based on only three locally indexed source summaries. No embedding model, vector store, or LLM is used. A live test found irrelevant citations caused by the generic publisher name contributing to lexical scores; excluding that token fixed the case, and the final test and browser retest returned only the cough source. |
| Knowledge center | Implemented for a small local corpus | Category filtering, search, article detail, source attribution, related articles, and loading/error states use `/api/v1/knowledge`. Three MedlinePlus-linked educational summaries are present. HTML extraction/chunk/index scripts exist; source refresh is manual, not scheduled or monitored. |
| Persistence and migrations | Partially implemented | SQLAlchemy models and local SQLite persistence cover users, profiles, assessments, recommendations, feedback, providers, and saved providers. Revisions `0001_saved_providers` and `0002_consent_and_integrity` are applied, but other tables still lack a complete Alembic baseline and are created with `Base.metadata.create_all`. PostgreSQL schema compilation is tested; no PostgreSQL server was available for connection or migration tests. |
| UI states/accessibility | Implemented in reviewed flows, not fully audited | Auth, assessment, provider, dashboard, assistant, and knowledge views use loading/error/empty/status messaging and semantic labels in reviewed flows. Responsive styling exists; a complete device/browser accessibility audit has not been run. |

## Bugs and root causes

1. **Registration reported “Failed to fetch” on `127.0.0.1:5173`.** The frontend origin was not included in the backend CORS allowlist, so the browser rejected the preflight request. Both local origins are now allowed, and the API URL is host-aware. The frontend displays actionable fetch errors and registration progress/success/error states.
2. **Dashboard rendered `[object Object]` for legacy recommendation data.** Historic records can contain specialty objects; the endpoint now normalizes records into typed display properties and UI tests cover that legacy shape.
3. **Dashboard counts appeared inconsistent with records from other test runs.** Counts are filtered by authenticated user ID, so records owned by other test accounts are correctly excluded. Recommendation requests may omit assessment IDs, so a recommendation count need not always equal assessment count. A same-user assessment-to-recommendation workflow test checks consistent totals.
4. **Provider removal showed an error despite successful deletion.** The server returned HTTP 204 with an empty body, while the API helper attempted JSON parsing. It now treats 204 as an empty successful result; persistence and reload behavior are tested.
5. **Assistant returned irrelevant citations for a specific cough question.** A lexical query included the publisher name “MedlinePlus,” shared by every indexed article, and the retrieval scorer gave non-cough documents non-zero relevance. Excluding that token is covered by a regression assertion; the cough query returns only its source and unrelated questions abstain without citations.
6. **Symptom phrases previously drove unsupported specialty mappings.** Assessment processing now extracts phrases without mapping them to specialties; recommendation requires a user-selected specialty.
7. **Knowledge navigation used a browser alert.** It now routes to a browsable knowledge center and article detail pages.

## Security and integration findings

- Passwords are Argon2-hashed; tokens are signed JWTs; protected patient data and feedback use user ownership checks. Tests cover authentication and dashboard isolation.
- Development generates a random per-process JWT secret if none is configured. Production rejects missing or short secrets and requires explicit HTTPS CORS origins. JWT decoding requires expiration and subject claims.
- Bearer tokens are stored in browser `localStorage`, which is exposed to same-origin script execution. A production deployment needs a deliberate XSS-resistant session strategy plus CSP and related browser controls.
- The code has no visible account rate limiting, email verification, password reset, medical-data retention/deletion workflow, encrypted database-at-rest setup, or structured security/audit logging. Do not treat the local SQLite setup as suitable for real patient data.
- Safety rules are simple string matches and are not a validated triage instrument. They can miss important context or misinterpret language.
- SQLite application connections enable foreign keys; recommendations have an indexed assessment foreign key. Migration history is still incomplete. PostgreSQL dialect schema compilation passes, but PostgreSQL connectivity, migrations, runtime constraints, backups, concurrency, and transaction recovery remain unverified.
- Provider, qualifications, availability, and ranking evaluation data are synthetic. Do not describe providers as real or the ranking as clinically validated.

## Test and manual verification record

- Backend suite: 30 passed, with three framework deprecation warnings.
- Frontend tests: 8 passed across 5 files; TypeScript check and production build passed; `npm audit` reported zero vulnerabilities.
- Ruff passed for `backend`, `ai_engine`, and `scripts`.
- Local browser flow verified registration, a separate login, assessment submission, explicit-specialty recommendation, provider search/save/detail, knowledge listing/article detail, dashboard updates, a single-source cough answer, and a no-source fallback with no citations.
- Direct local SQLite checks and browser workflow verified account/password-hash, assessment, recommendation, provider-save persistence, reload/login retention, and provider removal.
- PostgreSQL was not available; the dialect compilation test is not a substitute for PostgreSQL integration testing.

## Recommended follow-up

1. Create and test a complete Alembic baseline; exercise CI against PostgreSQL before deployment.
3. Review safety behavior, patient-facing content, and specialty-selection language with qualified clinicians.
4. Expand the sourced knowledge set and evaluate relevant retrieval/abstention using a reviewed query set; adopt embeddings only if measured retrieval needs justify them.
5. Replace demo provider data with a lawful, vetted source before implementing live availability or booking.
6. Address production secret management, browser session security, rate limiting, privacy/data lifecycle, deployment headers, monitoring, and operational backups before accepting real health data.
