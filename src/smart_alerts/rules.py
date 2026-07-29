from datetime import datetime
from typing import Optional
import pytz

from src.smart_alerts.models import SensorReading, SensorConfig, RuleResult, Severity


def is_off_hours(current_time: datetime, start_hour: int, end_hour: int) -> bool:
    """Check if the current time is outside operating hours."""
    if start_hour == end_hour:
        return False

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
            severity=Severity.CRITICA,
            title="ALERTA CRÍTICA",
            description="Caudal superior al límite permitido sostenido en el tiempo. Revisar tuberías, válvulas y posibles fugas.",
            value=reading.flow_rate,
            threshold=config.critical_flow_threshold,
        )
    return None


def evaluate_r02(
    reading: SensorReading, config: SensorConfig, tz: pytz.tzinfo.BaseTzInfo
) -> Optional[RuleResult]:
    """R02 - Flujo fuera del horario operativo."""
    if reading.flow_rate is not None and reading.flow_rate > config.off_hours_flow_threshold:
        local_time = reading.timestamp.astimezone(tz)
        if is_off_hours(local_time, config.operating_start_hour, config.operating_end_hour):
            return RuleResult(
                rule_id="R02",
                triggered=True,
                severity=Severity.MEDIA,
                title="ALERTA DE ADVERTENCIA",
                description="Consumo detectado fuera del horario operativo esperado. Verificar si hay personal fuera de horario o llaves abiertas.",
                value=reading.flow_rate,
                threshold=config.off_hours_flow_threshold,
            )
    return None


def evaluate_r04(reading: SensorReading, config: SensorConfig) -> Optional[RuleResult]:
    """R04 - Consumo diario excesivo."""
    if reading.daily_volume is not None and reading.daily_volume > config.daily_volume_limit:
        return RuleResult(
            rule_id="R04",
            triggered=True,
            severity=Severity.CRITICA,
            title="ALERTA CRÍTICA",
            description="Consumo acumulado diario anormal para la zona. Realizar auditoría de consumo.",
            value=reading.daily_volume,
            threshold=config.daily_volume_limit,
        )
    return None
