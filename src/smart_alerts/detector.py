from datetime import datetime
from typing import Dict, List, Optional
import pytz

from src.smart_alerts.models import SensorReading, SensorConfig, Alert, Severity, AuditState
from src.smart_alerts.rules import evaluate_r01, evaluate_r02, evaluate_r04
from src.smart_alerts.audit import AuditLogger

class Detector:
    """Clase para evaluar reglas de negocio y generar alertas con persistencia temporal."""
    
    def __init__(self, debounce_seconds: int, audit_logger: Optional[AuditLogger] = None, tz_str: str = "UTC"):
        # Maps (sensor_id, rule_id) to the datetime it first triggered
        self._active_conditions: Dict[tuple[str, str], datetime] = {}
        self.debounce_seconds = debounce_seconds
        self.audit_logger = audit_logger
        self.tz = pytz.timezone(tz_str)
        
    def _now(self) -> datetime:
        return datetime.now(self.tz)
        
    def evaluate_reading(
        self,
        reading: SensorReading,
        config: SensorConfig,
        current_time: datetime | None = None
    ) -> List[Alert]:
        """Evalúa una lectura contra las reglas R01, R02 y R04."""
        alerts = []
        
        # Evaluar R01
        r01_result = evaluate_r01(reading, config)
        if r01_result:
            alert = self._process_rule_result(r01_result, reading, self.debounce_seconds)
            if alert: alerts.append(alert)
        else:
            self._resolve_condition(reading.sensor_id, "R01")
            
        # Evaluar R02
        r02_result = evaluate_r02(reading, config, self.tz)
        if r02_result:
            alert = self._process_rule_result(r02_result, reading, self.debounce_seconds)
            if alert: alerts.append(alert)
        else:
            self._resolve_condition(reading.sensor_id, "R02")
            
        # Evaluar R04
        r04_result = evaluate_r04(reading, config)
        if r04_result:
            alert = self._process_rule_result(r04_result, reading, self.debounce_seconds)
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
            current_time = self._now()
            
        alerts = []
        
        if last_valid_reading is None:
            # Estado PENDING o NOT_SEEN, no disparamos timeout sin registro
            return alerts
            
        time_offline = (current_time - last_valid_reading).total_seconds()
            
        if time_offline >= config.offline_timeout_seconds:
            alert = Alert(
                rule_id="R03",
                sensor_id=config.sensor_id,
                title="ALERTA INFORMATIVA",
                description="Sensor sin datos recientes. Posible desconexión o falla. Revisar red o broker.",
                severity=Severity.BAJA,
                occurred_at=current_time
            )
            alerts.append(alert)
            
        return alerts

    def _process_rule_result(
        self, 
        result, 
        reading: SensorReading, 
        persistence_seconds: int
    ) -> Alert | None:
        """Maneja la persistencia y convierte un RuleResult en Alert si se cumple el tiempo."""
        key = (reading.sensor_id, result.rule_id)
        
        if key not in self._active_conditions:
            self._active_conditions[key] = reading.timestamp
            if self.audit_logger:
                self.audit_logger.log_event(
                    state=AuditState.DETECTED,
                    alert_id="N/A", # Will be assigned on alert generation
                    rule_id=result.rule_id,
                    sensor_id=reading.sensor_id,
                    severity=result.severity,
                    reason=f"Anomalía detectada. Iniciando debounce de {persistence_seconds}s"
                )
            
        time_active = (reading.timestamp - self._active_conditions[key]).total_seconds()
        
        if time_active >= persistence_seconds:
            # Añadir info de valores al description
            val_str = f"{result.value:.2f}" if result.value is not None else "N/A"
            thresh_str = f"{result.threshold:.2f}" if result.threshold is not None else "N/A"
            full_desc = f"{result.description}\n\nValor detectado: {val_str}\nUmbral: {thresh_str}"
            
            return Alert(
                rule_id=result.rule_id,
                sensor_id=reading.sensor_id,
                title=result.title,
                description=full_desc,
                severity=result.severity,
                occurred_at=reading.timestamp
            )
        elif time_active > 0:
            if self.audit_logger:
                self.audit_logger.log_event(
                    state=AuditState.PENDING_DEBOUNCE,
                    alert_id="N/A",
                    rule_id=result.rule_id,
                    sensor_id=reading.sensor_id,
                    severity=result.severity,
                    reason=f"Esperando debounce. Activo por {time_active}s de {persistence_seconds}s"
                )
        return None

    def _resolve_condition(self, sensor_id: str, rule_id: str) -> None:
        """Marca una condición como resuelta eliminándola del registro de persistencia."""
        key = (sensor_id, rule_id)
        if key in self._active_conditions:
            del self._active_conditions[key]
            if self.audit_logger:
                self.audit_logger.log_event(
                    state=AuditState.RESOLVED,
                    alert_id="N/A",
                    rule_id=rule_id,
                    sensor_id=sensor_id,
                    reason="La anomalía desapareció antes o después de emitir alerta, debounce reiniciado."
                )
