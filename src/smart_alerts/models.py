import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pytz


class Severity(str, Enum):
    """Enumeración para los niveles de severidad admitidos."""

    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"

    @classmethod
    def _missing_(cls, value):
        """Soporta variaciones de escritura para valores faltantes."""
        if isinstance(value, str):
            val_upper = value.upper()
            if val_upper in ("CRÍTICA", "CRITICAL"):
                return cls.CRITICA
            if val_upper == "INFO":
                return cls.BAJA
            if val_upper == "WARNING":
                return cls.MEDIA
        raise ValueError(f"Invalid severity value: {value}")


class SendStatus(str, Enum):
    """Enumeración para los posibles estados de envío de una alerta."""

    SENT = "sent"
    SUPPRESSED = "suppressed"
    FAILED = "failed"


class AuditState(str, Enum):
    """Estados posibles en el ciclo de vida de una alerta."""

    DETECTED = "DETECTED"
    PENDING_DEBOUNCE = "PENDING_DEBOUNCE"
    SENT = "SENT"
    SUPPRESSED = "SUPPRESSED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    RESOLVED = "RESOLVED"


@dataclass
class Alert:
    """
    Estructura de datos para estandarizar la información de las alertas.

    Genera un alert_id único usando hash + timestamp para garantizar unicidad
    incluso cuando múltiples reglas se disparan para el mismo sensor.
    """

    rule_id: str
    sensor_id: str
    title: str
    description: str
    severity: Severity
    occurred_at: datetime = field(default_factory=lambda: datetime.now(pytz.utc))
    alert_id: str | None = field(default=None)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Genera un ID único y valida el nivel de severidad."""
        # Validar y convertir severity si es necesario
        if not isinstance(self.severity, Severity):
            self.severity = Severity(self.severity)

        # Generar ID único basado en timestamp y hash de contenido,
        # a menos que el llamador haya provisto uno explícitamente.
        if not self.alert_id:
            unique_content = f"{self.rule_id}:{self.sensor_id}:{self.occurred_at.isoformat()}"
            content_hash = hashlib.md5(unique_content.encode()).hexdigest()[:8]
            self.alert_id = f"{self.rule_id}_{self.sensor_id}_{content_hash}"


@dataclass(frozen=True)
class SensorReading:
    """Lectura de sensor inmutable con valores validados."""

    sensor_id: str
    zone: str
    timestamp: datetime
    flow_rate: float | None = None
    daily_volume: float | None = None

    def __post_init__(self):
        """Valida campos numéricos no negativos."""
        if self.flow_rate is not None and self.flow_rate < 0:
            raise ValueError(f"flow_rate no puede ser negativo: {self.flow_rate}")
        if self.daily_volume is not None and self.daily_volume < 0:
            raise ValueError(f"daily_volume no puede ser negativo: {self.daily_volume}")


@dataclass(frozen=True)
class SensorConfig:
    """Configuración para un sensor con validaciones de rango."""

    sensor_id: str
    zone: str
    critical_flow_threshold: float
    off_hours_flow_threshold: float
    daily_volume_limit: float
    operating_start_hour: int
    operating_end_hour: int
    critical_persistence_seconds: int
    off_hours_persistence_seconds: int
    offline_timeout_seconds: int

    def __post_init__(self):
        """Valida rangos y valores de configuración."""
        # Validar umbrales positivos
        if self.critical_flow_threshold <= 0:
            raise ValueError(
                f"critical_flow_threshold debe ser positivo: {self.critical_flow_threshold}"
            )
        if self.daily_volume_limit <= 0:
            raise ValueError(f"daily_volume_limit debe ser positivo: {self.daily_volume_limit}")

        # Validar horas operativas (0-23)
        if not 0 <= self.operating_start_hour <= 23:
            raise ValueError(
                f"operating_start_hour debe estar entre 0 y 23: {self.operating_start_hour}"
            )
        if not 0 <= self.operating_end_hour <= 23:
            raise ValueError(
                f"operating_end_hour debe estar entre 0 y 23: {self.operating_end_hour}"
            )

        # Validar tiempos positivos
        if self.critical_persistence_seconds <= 0:
            raise ValueError(
                f"critical_persistence_seconds debe ser positivo: {self.critical_persistence_seconds}"
            )
        if self.off_hours_persistence_seconds <= 0:
            raise ValueError(
                f"off_hours_persistence_seconds debe ser positivo: {self.off_hours_persistence_seconds}"
            )
        if self.offline_timeout_seconds <= 0:
            raise ValueError(
                f"offline_timeout_seconds debe ser positivo: {self.offline_timeout_seconds}"
            )


@dataclass(frozen=True)
class RuleResult:
    """
    Resultado de una regla evaluada.

    El campo `triggered` indica si la regla se disparó, útil para
    diferenciar entre "regla no disparada" vs "regla disparada pero sin persistencia aún".
    """

    rule_id: str
    triggered: bool
    severity: Severity
    title: str
    description: str
    value: float | None = None
    threshold: float | None = None
