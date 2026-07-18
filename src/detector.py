from datetime import datetime
from typing import Dict, List

from src.models import SensorReading, SensorConfig
from src.telegram_bot import Alert, Severity
from src.rules import evaluate_r01, evaluate_r02, evaluate_r04

class Detector:
    """Clase para evaluar reglas de negocio y generar alertas con persistencia temporal."""
    
    def __init__(self):
        # Maps (sensor_id, rule_id) to the datetime it first triggered
        self._active_conditions: Dict[tuple[str, str], datetime] = {}
        
    def evaluate_reading(
        self,
        reading: SensorReading,
        config: SensorConfig,
        current_time: datetime | None = None
    ) -> List[Alert]:
        """Evalúa una lectura contra las reglas R01, R02 y R04."""
        if current_time is None:
            current_time = datetime.now()
            
        alerts = []
        
        # Evaluar R01
        r01_result = evaluate_r01(reading, config)
        if r01_result:
            alert = self._process_rule_result(r01_result, reading, config.critical_persistence_seconds, current_time)
            if alert: alerts.append(alert)
        else:
            self._resolve_condition(reading.sensor_id, "R01")
            
        # Evaluar R02
        r02_result = evaluate_r02(reading, config)
        if r02_result:
            alert = self._process_rule_result(r02_result, reading, config.off_hours_persistence_seconds, current_time)
            if alert: alerts.append(alert)
        else:
            self._resolve_condition(reading.sensor_id, "R02")
            
        # Evaluar R04
        r04_result = evaluate_r04(reading, config)
        if r04_result:
            # R04 no requiere persistencia según los requisitos (se dispara en cuanto supera)
            alert = self._process_rule_result(r04_result, reading, 0, current_time)
            if alert: alerts.append(alert)
        else:
            self._resolve_condition(reading.sensor_id, "R04")
            
        return alerts
        
    def evaluate_offline_sensor(
        self,
        config: SensorConfig,
        last_valid_reading: datetime | None,
        current_time: datetime | None = None
    ) -> List[Alert]:
        """Evalúa si un sensor está fuera de línea (R03)."""
        if current_time is None:
            current_time = datetime.now()
            
        alerts = []
        
        if last_valid_reading is None:
            time_offline = float('inf')
        else:
            time_offline = (current_time - last_valid_reading).total_seconds()
            
        if time_offline >= config.offline_timeout_seconds:
            alert = Alert(
                rule_id="R03",
                sensor_id=config.sensor_id,
                zone=config.zone,
                value=None,
                threshold=None,
                severity=Severity.INFO,
                description="Sensor sin datos recientes. Posible desconexión o falla.",
                recommended_action="Revisar alimentación eléctrica, red o broker MQTT."
            )
            alerts.append(alert)
            
        return alerts

    def _process_rule_result(
        self, 
        result, 
        reading: SensorReading, 
        persistence_seconds: int, 
        current_time: datetime
    ) -> Alert | None:
        """Maneja la persistencia y convierte un RuleResult en Alert si se cumple el tiempo."""
        key = (reading.sensor_id, result.rule_id)
        
        if key not in self._active_conditions:
            # Condición detectada por primera vez
            self._active_conditions[key] = current_time
            
        time_active = (current_time - self._active_conditions[key]).total_seconds()
        
        if time_active >= persistence_seconds:
            # Condición con persistencia cumplida
            return Alert(
                rule_id=result.rule_id,
                sensor_id=reading.sensor_id,
                zone=reading.zone,
                value=result.value,
                threshold=result.threshold,
                severity=result.severity,
                description=result.description,
                recommended_action=result.recommended_action
            )
        # Condición todavía activa pero sin persistencia suficiente
        return None

    def _resolve_condition(self, sensor_id: str, rule_id: str) -> None:
        """Marca una condición como resuelta eliminándola del registro de persistencia."""
        key = (sensor_id, rule_id)
        if key in self._active_conditions:
            del self._active_conditions[key]
