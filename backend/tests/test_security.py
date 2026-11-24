from datetime import datetime, timedelta, timezone

import pytest
from app.core.config import Settings, get_settings
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from jose import jwt
from pydantic import SecretStr, ValidationError


def test_development_secret_is_random_and_passwords_use_argon2id():
    first = Settings(app_env="development", database_url="sqlite://", jwt_secret_key=None)
    second = Settings(app_env="development", database_url="sqlite://", jwt_secret_key=None)
    first_secret = first.jwt_secret_key.get_secret_value()
    assert len(first_secret) >= 32
    assert first_secret != second.jwt_secret_key.get_secret_value()

    encoded = hash_password("A-long-secure-password-123")
    assert encoded.startswith("$argon2id$")
    assert verify_password("A-long-secure-password-123", encoded)
    assert not verify_password("different-password", encoded)


def test_production_requires_strong_secret_and_explicit_https_cors():
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(app_env="production", database_url="sqlite://", jwt_secret_key=None)

    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(
            app_env="production",
            database_url="sqlite://",
            jwt_secret_key=SecretStr("s" * 48),
        )
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(
            app_env=" Production ",
            database_url="sqlite://",
            jwt_secret_key=SecretStr(" " * 48),
            cors_origins="https://healthwise.example.com",
        )

    valid = Settings(
        app_env="production",
        database_url="postgresql+psycopg://user:password@localhost/healthwise",
        jwt_secret_key=SecretStr("s" * 48),
        cors_origins="https://healthwise.example.com",
    )
    assert valid.allowed_cors_origins == ["https://healthwise.example.com"]


def test_tokens_require_subject_and_valid_expiration():
    settings = get_settings()
    secret = settings.jwt_secret_key.get_secret_value()
    missing_exp = jwt.encode(
        {"sub": "patient-id", "role": "patient"},
        secret,
        algorithm=settings.jwt_algorithm,
    )
    expired = jwt.encode(
        {
            "sub": "patient-id",
            "role": "patient",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        secret,
        algorithm=settings.jwt_algorithm,
    )
    for token in (missing_exp, expired):
        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_access_token(token)

    valid = decode_access_token(create_access_token("patient-id", "patient"))
    assert valid["sub"] == "patient-id"
