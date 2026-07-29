import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    telegram_bot_token: str
    telegram_chat_id: str
    telegram_timeout_seconds: int
    telegram_max_retries: int
    telegram_backoff_seconds: int
    alert_cooldown_seconds: int
    alert_debounce_seconds: int
    audit_log_path: str
    app_timezone: str
    log_level: str


def load_config() -> AppConfig:
    """
    Carga y valida la configuración centralizada desde variables de entorno.
    Usa valores seguros por defecto para timeouts y retries.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID son obligatorios.")

    try:
        timeout = int(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "10"))
    except ValueError:
        timeout = 10

    try:
        max_retries = int(os.getenv("TELEGRAM_MAX_RETRIES", "3"))
    except ValueError:
        max_retries = 3

    try:
        backoff = int(os.getenv("TELEGRAM_BACKOFF_SECONDS", "2"))
    except ValueError:
        backoff = 2

    try:
        cooldown = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))
    except ValueError:
        cooldown = 300

    try:
        debounce = int(os.getenv("ALERT_DEBOUNCE_SECONDS", "60"))
    except ValueError:
        debounce = 60

    return AppConfig(
        telegram_bot_token=token,
        telegram_chat_id=chat_id,
        telegram_timeout_seconds=timeout,
        telegram_max_retries=max_retries,
        telegram_backoff_seconds=backoff,
        alert_cooldown_seconds=cooldown,
        alert_debounce_seconds=debounce,
        audit_log_path=os.getenv("AUDIT_LOG_PATH", "audit.jsonl"),
        app_timezone=os.getenv("APP_TIMEZONE", "America/El_Salvador"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
