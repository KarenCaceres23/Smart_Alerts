import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.smart_alerts.models import AuditState, Severity

logger = logging.getLogger(__name__)

# Límite máximo de archivo de auditoría (5MB)
MAX_AUDIT_FILE_SIZE = 5 * 1024 * 1024


class AuditLogger:
    """
    Escribe logs de auditoría en formato JSONL con límites de tamaño
    y manejo de errores robusto.

    El archivo de auditoría se rota automáticamente cuando excede el tamaño máximo.
    """

    def __init__(self, log_path: str = "audit.jsonl", tz_str: str = "UTC"):
        # Validar y sanitizar el path
        self.log_path = self._sanitize_path(log_path)
        self.tz_str = tz_str

        # Ensure directory exists con manejo de errores
        if self.log_path.parent and not self.log_path.parent.exists():
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"Error creando directorio de auditoría: {e}")
                raise

    def _sanitize_path(self, path: str) -> Path:
        """Sanitiza el path para prevenir directory traversal."""
        # Eliminar caracteres potencialmente peligrosos
        safe_name = os.path.basename(path)
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")

        if not safe_name:
            safe_name = "audit.jsonl"

        # Usar el directorio actual por defecto
        return Path(safe_name)

    def log_event(
        self,
        state: AuditState,
        alert_id: str,
        rule_id: str,
        sensor_id: str,
        severity: Severity | None = None,
        reason: str | None = None,
        attempts: int | None = None,
        latency_ms: int | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Registra un evento de auditoría en el archivo JSONL.

        El archivo se rota automáticamente cuando excede MAX_AUDIT_FILE_SIZE.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Build payload avoiding any credential or secrets
        payload: dict[str, Any] = {
            "timestamp": now,
            "state": state.value,
            "alert_id": alert_id,
            "rule_id": rule_id,
            "sensor_id": sensor_id,
        }

        if severity:
            payload["severity"] = severity.value
        if reason:
            # Sanitizar reason para evitar inyección
            payload["reason"] = str(reason)[:500]
        if attempts is not None:
            payload["attempts"] = attempts
        if latency_ms is not None:
            payload["latency_ms"] = latency_ms
        if error:
            # Sanitizar error
            payload["error"] = str(error)[:500]
        if metadata:
            payload["metadata"] = metadata

        try:
            # Verificar si necesitamos rotar el archivo
            if self._should_rotate():
                self._rotate_file()

            # Asegurar que el archivo existe
            if not self.log_path.exists():
                self.log_path.touch()

            self._write_line(payload)
        except Exception as e:
            logger.error(f"Error escribiendo log de auditoría: {e}")

    def _should_rotate(self) -> bool:
        """Verifica si el archivo necesita rotación."""
        try:
            if self.log_path.exists():
                return self.log_path.stat().st_size >= MAX_AUDIT_FILE_SIZE
        except OSError:
            pass
        return False

    def _rotate_file(self) -> None:
        """Rota el archivo de auditoría."""
        try:
            backup_path = self.log_path.with_suffix(".jsonl.bak")
            if backup_path.exists():
                backup_path.unlink()
            self.log_path.rename(backup_path)
            logger.info(f"Archivo de auditoría rotado a {backup_path}")
        except OSError as e:
            logger.error(f"Error rotando archivo de auditoría: {e}")

    def _write_line(self, payload: dict[str, Any]) -> None:
        """Escribe una línea JSON al archivo."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def read_entries(
        self,
        limit: int = 100,
        state: AuditState | None = None,
        sensor_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Lee entradas del archivo de auditoría con filtros opcionales.

        Args:
            limit: Máximo número de entradas a devolver
            state: Filtrar por estado (opcional)
            sensor_id: Filtrar por sensor_id (opcional)

        Returns:
            Lista de entradas de auditoría
        """
        entries = []

        if not self.log_path.exists():
            return entries

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Aplicar filtros
                        if state and entry.get("state") != state.value:
                            continue
                        if sensor_id and entry.get("sensor_id") != sensor_id:
                            continue

                        entries.append(entry)

                        if len(entries) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            logger.error(f"Error leyendo auditoría: {e}")

        return entries

    def get_stats(self) -> dict[str, int]:
        """Devuelve estadísticas básicas del archivo de auditoría."""
        stats = {
            "total_entries": 0,
            "by_state": {},
        }

        if not self.log_path.exists():
            return stats

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        stats["total_entries"] += 1

                        state = entry.get("state", "UNKNOWN")
                        stats["by_state"][state] = stats["by_state"].get(state, 0) + 1
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass

        return stats
