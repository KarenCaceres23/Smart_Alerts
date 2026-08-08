import pytest

from src.smart_alerts.config import load_config


def test_config_incomplete(monkeypatch):
    """Test 2: Configuración incompleta lanza ValueError."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID son obligatorios."):
        load_config()


def test_config_defaults(monkeypatch):
    """Test defaults for timeout, retries, backoff."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")

    # We clear other variables to trigger defaults
    monkeypatch.delenv("TELEGRAM_TIMEOUT_SECONDS", raising=False)

    config = load_config()
    assert config.telegram_timeout_seconds == 10
    assert config.telegram_max_retries == 3
    assert config.telegram_backoff_seconds == 2
    assert config.alert_cooldown_seconds == 300
    assert config.app_timezone == "America/El_Salvador"
