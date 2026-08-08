import os
import re
from dataclasses import dataclass, field


@dataclass
class AppConfig:
    telegram_bot_token: str
    telegram_chat_id: str
    telegram_timeout_seconds: int = field(default=10, repr=False)
    telegram_max_retries: int = field(default=3)
    telegram_backoff_seconds: int = field(default=2)
    alert_cooldown_seconds: int = field(default=300)
    alert_debounce_seconds: int = field(default=60)
    audit_log_path: str = "audit.jsonl"
    app_timezone: str = "America/El_Salvador"
    log_level: str = "INFO"

    def __post_init__(self):
        """Valida los valores después de la inicialización."""
        # Validar timeout
        if not 1 <= self.telegram_timeout_seconds <= 120:
            raise ValueError(
                f"telegram_timeout_seconds debe estar entre 1 y 120, se recibió: {self.telegram_timeout_seconds}"
            )

        # Validar retries
        if not 0 <= self.telegram_max_retries <= 10:
            raise ValueError(
                f"telegram_max_retries debe estar entre 0 y 10, se recibió: {self.telegram_max_retries}"
            )

        # Validar backoff
        if not 0 <= self.telegram_backoff_seconds <= 60:
            raise ValueError(
                f"telegram_backoff_seconds debe estar entre 0 y 60, se recibió: {self.telegram_backoff_seconds}"
            )

        # Validar cooldown
        if not 1 <= self.alert_cooldown_seconds <= 3600:
            raise ValueError(
                f"alert_cooldown_seconds debe estar entre 1 y 3600, se recibió: {self.alert_cooldown_seconds}"
            )

        # Validar debounce
        if not 1 <= self.alert_debounce_seconds <= 3600:
            raise ValueError(
                f"alert_debounce_seconds debe estar entre 1 y 3600, se recibió: {self.alert_debounce_seconds}"
            )

        # Validar chat_id (debe ser un número negativo para grupos o positivo para usuarios)
        if not re.match(r"^-?\d+$", self.telegram_chat_id.strip()):
            raise ValueError(
                f"telegram_chat_id debe ser un número válido, se recibió: {self.telegram_chat_id}"
            )

        # Limpiar y validar token
        self.telegram_bot_token = self.telegram_bot_token.strip()
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN no puede estar vacío")


def load_config() -> AppConfig:
    """
    Carga y valida la configuración centralizada desde variables de entorno.
    Usa valores seguros por defecto para timeouts y retries.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID son obligatorios.")

    # Parsear valores con validación
    def safe_int_env(key: str, default: int, min_val: int = 0, max_val: int = 120) -> int:
        """Parsea un entero con validación de rango."""
        try:
            value = int(os.getenv(key, str(default)))
            if not min_val <= value <= max_val:
                return default
            return value
        except (ValueError, TypeError):
            return default

    # Validar zona horaria
    tz = os.getenv("APP_TIMEZONE", "America/El_Salvador").strip()
    try:
        import pytz

        pytz.timezone(tz)  # Validar que la zona horaria exista
    except (ImportError, pytz.exceptions.UnknownTimeZoneError):
        tz = "America/El_Salvador"

    return AppConfig(
        telegram_bot_token=token,
        telegram_chat_id=chat_id,
        telegram_timeout_seconds=safe_int_env("TELEGRAM_TIMEOUT_SECONDS", 10, 1, 120),
        telegram_max_retries=safe_int_env("TELEGRAM_MAX_RETRIES", 3, 0, 10),
        telegram_backoff_seconds=safe_int_env("TELEGRAM_BACKOFF_SECONDS", 2, 0, 60),
        alert_cooldown_seconds=safe_int_env("ALERT_COOLDOWN_SECONDS", 300, 1, 3600),
        alert_debounce_seconds=safe_int_env("ALERT_DEBOUNCE_SECONDS", 60, 1, 3600),
        audit_log_path=os.getenv("AUDIT_LOG_PATH", "audit.jsonl").strip() or "audit.jsonl",
        app_timezone=tz,
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )
