from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import pytz

class Severity(str, Enum):
    """Enumeración para los niveles de severidad admitidos."""
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"
    
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper()
            if val_upper == "CRÍTICA" or val_upper == "CRITICAL":
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
    DETECTED = "DETECTED"
    PENDING_DEBOUNCE = "PENDING_DEBOUNCE"
    SENT = "SENT"
    SUPPRESSED = "SUPPRESSED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    RESOLVED = "RESOLVED"

@dataclass
class Alert:
    """Estructura de datos para estandarizar la información de las alertas."""
    rule_id: str
    sensor_id: str
    title: str
    description: str
    severity: Severity
    occurred_at: datetime = field(default_factory=lambda: datetime.now(pytz.utc))
    alert_id: str = field(init=False)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Generar un ID estable para el cooldown basado en rule_id y sensor_id
        if not isinstance(self.severity, Severity):
            self.severity = Severity(self.severity)
        self.alert_id = f"{self.rule_id}_{self.sensor_id}"

@dataclass(frozen=True)
class SensorReading:
    sensor_id: str
    zone: str
    timestamp: datetime
    flow_rate: Optional[float]
    daily_volume: Optional[float]

@dataclass(frozen=True)
class SensorConfig:
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

@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    triggered: bool
    severity: Severity
    title: str
    description: str
    value: Optional[float] = None
    threshold: Optional[float] = None
