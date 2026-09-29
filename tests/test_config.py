import pytest
from backend.config import load, ConfigError

STRONG = "Zq8v1kP4nR7tW2yB9cX5mL3hJ6gF0dSa"


def test_unset_env_fails_closed_as_production():
    with pytest.raises(ConfigError) as e:
        load({})
    assert "APP_ENV=production" in str(e.value)


@pytest.mark.parametrize("salt", ["change-me", "", "short", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"])
def test_production_rejects_weak_salt(salt):
    with pytest.raises(ConfigError):
        load({"APP_ENV": "production", "PHONE_HASH_SALT": salt, "DATABASE_URL": "postgresql+psycopg://x/y"})


def test_production_requires_postgres_and_forbids_pii_debug():
    base = {"APP_ENV": "production", "PHONE_HASH_SALT": STRONG}
    with pytest.raises(ConfigError, match="PostgreSQL"):
        load({**base, "DATABASE_URL": "sqlite:///./x.db"})
    with pytest.raises(ConfigError, match="forbidden"):
        load({**base, "DATABASE_URL": "postgresql+psycopg://x/y", "CAPTURE_MODE": "full_body_pii_debug"})
    assert load({**base, "DATABASE_URL": "postgresql+psycopg://x/y"}).capture_mode == "metadata"


def test_error_message_never_contains_the_secret():
    weak = "abcdefgh12"          # too short, but distinctive
    with pytest.raises(ConfigError) as e:
        load({"APP_ENV": "production", "PHONE_HASH_SALT": weak, "DATABASE_URL": "postgresql://x"})
    assert weak not in str(e.value)


def test_development_rejects_placeholder_but_allows_sqlite():
    with pytest.raises(ConfigError):
        load({"APP_ENV": "development", "PHONE_HASH_SALT": "change-me"})
    s = load({"APP_ENV": "development", "PHONE_HASH_SALT": "dev-salt-7fK2pQ9xZ"})
    assert s.database_url.startswith("sqlite")


def test_test_env_allows_placeholders():
    assert load({"APP_ENV": "test"}).app_env == "test"
