import gc
import hashlib
import logging
from datetime import datetime, timedelta

import pytz

from src.smart_alerts.audit import AuditLogger
from src.smart_alerts.models import (
    Alert,
    AuditState,
    RuleResult,
    SensorConfig,
    SensorReading,
    Severity,
)
from src.smart_alerts.rules import evaluate_r01, evaluate_r02, evaluate_r04

logger = logging.getLogger(__name__)


class Detector:
    """
    Clase para evaluar reglas de negocio y generar alertas con persistencia temporal.

    Maneja el debounce de alertas y el rastreo de condiciones activas.
    """

    # Límite máximo de condiciones activas para prevenir memory leaks
    MAX_ACTIVE_CONDITIONS = 10000

    def __init__(
        self,
        debounce_seconds: int,
        audit_logger: AuditLogger | None = None,
        tz_str: str = "UTC",
    ):
        self.debounce_seconds = max(1, debounce_seconds)  # Validar valor mínimo
        self.audit_logger = audit_logger
        try:
            self.tz = pytz.timezone(tz_str)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Zona horaria desconocida: {tz_str}, usando UTC")
            self.tz = pytz.UTC

        # Maps (sensor_id, rule_id) to the datetime it first triggered
        self._active_conditions: dict[tuple[str, str], datetime] = {}
        self._total_evaluations = 0

    def _now(self) -> datetime:
        """Obtiene la hora actual en la zona horaria configurada."""
        return datetime.now(self.tz)

    def _generate_alert_id(self, rule_id: str, sensor_id: str, timestamp: datetime) -> str:
        """
        Genera un ID único para la alerta usando hash de contenido.
        Esto asegura unicidad incluso con múltiples reglas por sensor.
        """
        content = f"{rule_id}:{sensor_id}:{timestamp.isoformat()}"
        return f"{rule_id}_{sensor_id}_{hashlib.md5(content.encode()).hexdigest()[:8]}"

    def evaluate_reading(
        self, reading: SensorReading, config: SensorConfig, current_time: datetime | None = None
    ) -> list[Alert]:
        """Evalúa una lectura contra las reglas R01, R02 y R04."""
        alerts = []

        # Usar la zona horaria del sensor si está disponible, sino la configurada
        reading_time = reading.timestamp
        if reading_time.tzinfo is None:
            reading_time = pytz.UTC.localize(reading_time)

        # Si no se provee current_time, usar el timestamp de la lectura.
        # Esto garantiza que el cálculo del debounce (time_active) sea determinista
        # y consistente con los datos evaluados, en lugar de depender de la hora
        # real del sistema (que rompe el procesamiento por lotes y las pruebas).
        if current_time is None:
            current_time = reading_time

        # Evaluar R01
        r01_result = evaluate_r01(reading, config)
        if r01_result:
            alert = self._process_rule_result(
                r01_result, reading, config.critical_persistence_seconds, current_time
            )
            if alert:
                alerts.append(alert)
        else:
            self._resolve_condition(reading.sensor_id, "R01")

        # Evaluar R02
        r02_result = evaluate_r02(reading, config, self.tz)
        if r02_result:
            alert = self._process_rule_result(
                r02_result, reading, config.off_hours_persistence_seconds, current_time
            )
            if alert:
                alerts.append(alert)
        else:
            self._resolve_condition(reading.sensor_id, "R02")

        # Evaluar R04
        r04_result = evaluate_r04(reading, config)
        if r04_result:
            alert = self._process_rule_result(
                r04_result, reading, config.critical_persistence_seconds, current_time
            )
            if alert:
                alerts.append(alert)
        else:
            self._resolve_condition(reading.sensor_id, "R04")

        # Cleanup periódico para prevenir memory leaks
        self._total_evaluations += 1
        if self._total_evaluations % 1000 == 0:
            self._cleanup_old_conditions()

        return alerts

    def evaluate_offline_sensor(
        self,
        config: SensorConfig,
        last_valid_reading: datetime | None,
        current_time: datetime | None = None,
    ) -> list[Alert]:
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
                occurred_at=current_time,
            )
            alerts.append(alert)

        return alerts

    def _process_rule_result(
        self,
        result: RuleResult,
        reading: SensorReading,
        persistence_seconds: int,
        current_time: datetime,
    ) -> Alert | None:
        """
        Maneja la persistencia y convierte un RuleResult en Alert si se cumple el tiempo.

        El debounce se calcula desde la primera detección hasta que se cumple
        el tiempo de persistencia mínimo.
        """
        key = (reading.sensor_id, result.rule_id)

        if key not in self._active_conditions:
            self._active_conditions[key] = current_time
            if self.audit_logger:
                self.audit_logger.log_event(
                    state=AuditState.DETECTED,
                    alert_id="N/A",  # Will be assigned on alert generation
                    rule_id=result.rule_id,
                    sensor_id=reading.sensor_id,
                    severity=result.severity,
                    reason=f"Anomalía detectada. Iniciando debounce de {persistence_seconds}s",
                )

        time_active = (current_time - self._active_conditions[key]).total_seconds()

        if time_active >= persistence_seconds:
            # Añadir info de valores al description
            val_str = f"{result.value:.2f}" if result.value is not None else "N/A"
            thresh_str = f"{result.threshold:.2f}" if result.threshold is not None else "N/A"
            full_desc = f"{result.description}\n\nValor detectado: {val_str}\nUmbral: {thresh_str}"

            # Generar ID único para la alerta
            alert_id = self._generate_alert_id(result.rule_id, reading.sensor_id, current_time)

            return Alert(
                rule_id=result.rule_id,
                sensor_id=reading.sensor_id,
                title=result.title,
                description=full_desc,
                severity=result.severity,
                occurred_at=current_time,
                alert_id=alert_id,
            )
        elif time_active > 0:
            if self.audit_logger:
                self.audit_logger.log_event(
                    state=AuditState.PENDING_DEBOUNCE,
                    alert_id="N/A",
                    rule_id=result.rule_id,
                    sensor_id=reading.sensor_id,
                    severity=result.severity,
                    reason=f"Esperando debounce. Activo por {time_active:.1f}s de {persistence_seconds}s",
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
                    reason="La anomalía desapareció antes o después de emitir alerta, debounce reiniciado.",
                )

    def _cleanup_old_conditions(self) -> None:
        """
        Elimina condiciones antiguas que han expirado.
        Esto previene memory leaks en ejecuciones prolongadas.
        """
        if len(self._active_conditions) > self.MAX_ACTIVE_CONDITIONS:
            logger.warning(
                f"Demasiadas condiciones activas ({len(self._active_conditions)}), limpiando antiguas..."
            )

        cutoff = self._now() - timedelta(
            seconds=self.debounce_seconds * 6
        )  # 6x el debounce como margen

        expired_keys = [k for k, v in self._active_conditions.items() if v < cutoff]

        for k in expired_keys:
            del self._active_conditions[k]

        # Forzar garbage collection si se eliminaron muchas entradas
        if expired_keys:
            gc.collect()

    def get_active_conditions_count(self) -> int:
        """Devuelve el número actual de condiciones activas (para monitoreo)."""
        return len(self._active_conditions)
