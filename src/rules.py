from datetime import datetime
from typing import Optional
from src.telegram_bot import Severity
from src.models import SensorReading, SensorConfig, RuleResult

def is_off_hours(current_time: datetime, start_hour: int, end_hour: int) -> bool:
    """Check if the current time is outside operating hours."""
    current_hour = current_time.hour
    if start_hour > end_hour:
        is_operating = current_hour >= start_hour or current_hour < end_hour
    else:
        is_operating = start_hour <= current_hour < end_hour
    return not is_operating

def evaluate_r01(reading: SensorReading, config: SensorConfig) -> Optional[RuleResult]:
    """R01 - Caudal crítico."""
    if reading.flow_rate is not None and reading.flow_rate > config.critical_flow_threshold:
        return RuleResult(
            rule_id="R01",
            triggered=True,
            severity=Severity.CRITICAL,
            description="Caudal superior al límite permitido sostenido en el tiempo.",
            recommended_action="Revisar tuberías, válvulas y posibles fugas.",
            value=reading.flow_rate,
            threshold=config.critical_flow_threshold
        )
    return None

def evaluate_r02(reading: SensorReading, config: SensorConfig) -> Optional[RuleResult]:
    """R02 - Flujo fuera del horario operativo."""
    if reading.flow_rate is not None and reading.flow_rate > config.off_hours_flow_threshold:
        if is_off_hours(reading.timestamp, config.operating_start_hour, config.operating_end_hour):
            return RuleResult(
                rule_id="R02",
                triggered=True,
                severity=Severity.WARNING,
                description="Consumo detectado fuera del horario operativo esperado.",
                recommended_action="Verificar si hay personal fuera de horario o llaves abiertas.",
                value=reading.flow_rate,
                threshold=config.off_hours_flow_threshold
            )
    return None

def evaluate_r04(reading: SensorReading, config: SensorConfig) -> Optional[RuleResult]:
    """R04 - Consumo diario excesivo."""
    if reading.daily_volume is not None and reading.daily_volume > config.daily_volume_limit:
        return RuleResult(
            rule_id="R04",
            triggered=True,
            severity=Severity.CRITICAL,
            description="Consumo acumulado diario anormal para la zona.",
            recommended_action="Realizar auditoría de consumo en la zona afectada.",
            value=reading.daily_volume,
            threshold=config.daily_volume_limit
        )
    return None
