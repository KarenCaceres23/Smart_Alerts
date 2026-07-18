from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.telegram_bot import Severity

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
    description: str
    recommended_action: str
    value: Optional[float]
    threshold: Optional[float]
