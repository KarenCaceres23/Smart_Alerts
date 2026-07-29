import json
from datetime import datetime, timezone
import logging
from typing import Optional, Any
from pathlib import Path
from .models import AuditState, Severity

logger = logging.getLogger(__name__)


class AuditLogger:
    """Escribe logs de auditoría en formato JSONL."""

    def __init__(self, log_path: str = "audit.jsonl", tz_str: str = "UTC"):
        self.log_path = Path(log_path)
        self.tz_str = tz_str

        # Ensure directory exists
        if self.log_path.parent:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        state: AuditState,
        alert_id: str,
        rule_id: str,
        sensor_id: str,
        severity: Optional[Severity] = None,
        reason: Optional[str] = None,
        attempts: Optional[int] = None,
        latency_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """Registra un evento de auditoría en el archivo JSONL."""
        now = datetime.now(timezone.utc).isoformat()

        # Build payload avoiding any credential or secrets
        payload = {
            "timestamp": now,
            "state": state.value,
            "alert_id": alert_id,
            "rule_id": rule_id,
            "sensor_id": sensor_id,
        }

        if severity:
            payload["severity"] = severity.value
        if reason:
            payload["reason"] = reason
        if attempts is not None:
            payload["attempts"] = attempts
        if latency_ms is not None:
            payload["latency_ms"] = latency_ms
        if error:
            payload["error"] = error

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            logger.error(f"Error escribiendo log de auditoría: {e}")
