# Database Design

The SQLAlchemy schema contains users, patient profiles, symptom assessments, recommendations, feedback, providers, and a user/provider saved-provider join table. Patient routes scope assessment, recommendation, and saved-provider data to the authenticated user. The canonical local SQLite database is repository-root `healthwise.db`, independent of the process working directory. PostgreSQL is configurable, and schema compilation is tested, but PostgreSQL connectivity and migrations have not been integration-tested.

```mermaid
erDiagram
  USERS ||--o| PATIENT_PROFILES : has
  USERS ||--o{ SYMPTOM_ASSESSMENTS : creates
  USERS ||--o{ RECOMMENDATIONS : receives
  RECOMMENDATIONS ||--o{ FEEDBACK : has
  SYMPTOM_ASSESSMENTS o|--o{ RECOMMENDATIONS : informs
  USERS ||--o{ SAVED_PROVIDERS : saves
  PROVIDERS ||--o{ SAVED_PROVIDERS : saved
  USERS {
    string id PK
    string email
    string full_name
    string hashed_password
    string role
  }
  PATIENT_PROFILES {
    string id PK
    string user_id FK
    int age
    string location
    boolean research_consent
    datetime research_consent_at
  }
  SYMPTOM_ASSESSMENTS {
    string id PK
    string user_id FK
    datetime created_at
  }
  RECOMMENDATIONS {
    string id PK
    string user_id FK
    string assessment_id FK
    datetime created_at
  }
  PROVIDERS {
    string id PK
    string name
    string specialty
    string location
  }
  SAVED_PROVIDERS {
    string user_id PK, FK
    string provider_id PK, FK
    datetime saved_at
  }
```

Revision `0001_saved_providers` creates the saved-provider table. Revision `0002_consent_and_integrity` adds the opt-in consent timestamp and an indexed assessment foreign key for recommendations; it is applied to the canonical SQLite database. SQLite application connections enable foreign-key enforcement. Existing consent timestamps cannot be reconstructed, so legacy values are left null rather than assigned invented dates.

UUID identifiers are stored as strings, and structured payloads use JSON-serialized text for SQLite/PostgreSQL portability. A PostgreSQL-dialect schema compilation test checks DDL generation, not server behavior. A full migration baseline for the pre-existing tables remains incomplete; startup also uses `Base.metadata.create_all`. A separate `backend\\healthwise.db` created by earlier working-directory-dependent runs was retained and not merged into the canonical database.
