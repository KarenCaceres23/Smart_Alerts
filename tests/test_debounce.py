from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
import pytz

from src.smart_alerts.detector import Detector
from src.smart_alerts.models import SensorConfig, SensorReading
from src.smart_alerts.audit import AuditLogger


@pytest.fixture
def config():
    return SensorConfig(
        sensor_id="S01",
        zone="Zone",
        critical_flow_threshold=20.0,
        off_hours_flow_threshold=5.0,
        daily_volume_limit=1000.0,
        operating_start_hour=7,
        operating_end_hour=19,
        critical_persistence_seconds=60,
        off_hours_persistence_seconds=300,
        offline_timeout_seconds=600,
    )


def test_debounce_starts_pending(config):
    """Prueba 1: Una lectura anómala inicia el debounce pero no envía alerta inmediata."""
    audit_mock = MagicMock(spec=AuditLogger)
    detector = Detector(debounce_seconds=60, audit_logger=audit_mock)

    t0 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.utc)
    reading = SensorReading("S01", "Zone", t0, 25.0, 50.0)
    alerts = detector.evaluate_reading(reading, config)
    
    assert len(alerts) == 0
    args, kwargs = audit_mock.log_event.call_args
    assert kwargs["state"].value == "DETECTED"


def test_debounce_keeps_pending(config):
    """Prueba 2: Lecturas adicionales dentro del tiempo de persistencia mantienen el estado pendiente."""
    audit_mock = MagicMock(spec=AuditLogger)
    detector = Detector(debounce_seconds=60, audit_logger=audit_mock)

    t0 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.utc)
    detector.evaluate_reading(SensorReading("S01", "Zone", t0, 25.0, 50.0), config)
    
    t1 = t0 + timedelta(seconds=30)
    alerts = detector.evaluate_reading(SensorReading("S01", "Zone", t1, 26.0, 50.0), config)
    
    assert len(alerts) == 0
    args, kwargs = audit_mock.log_event.call_args
    assert kwargs["state"].value == "PENDING_DEBOUNCE"


def test_debounce_triggers_alert(config):
    """Prueba 3: Una lectura que supera el tiempo de persistencia dispara la alerta."""
    detector = Detector(debounce_seconds=60)

    t0 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.utc)
    detector.evaluate_reading(SensorReading("S01", "Zone", t0, 25.0, 50.0), config)
    
    t1 = t0 + timedelta(seconds=65)  # Pasó el umbral de 60s
    alerts = detector.evaluate_reading(SensorReading("S01", "Zone", t1, 27.0, 50.0), config)
    
    assert len(alerts) == 1
    assert alerts[0].rule_id == "R01"
    assert alerts[0].severity.value == "CRITICA"


def test_debounce_resolves_if_normal(config):
    """Prueba 4: Una lectura normal antes de terminar el tiempo cancela (resuelve) el debounce."""
    audit_mock = MagicMock(spec=AuditLogger)
    detector = Detector(debounce_seconds=60, audit_logger=audit_mock)

    t0 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.utc)
    detector.evaluate_reading(SensorReading("S01", "Zone", t0, 25.0, 50.0), config)
    
    t1 = t0 + timedelta(seconds=30)
    # Lectura normal (debajo del umbral de 20)
    alerts = detector.evaluate_reading(SensorReading("S01", "Zone", t1, 15.0, 50.0), config)
    
    assert len(alerts) == 0
    args, kwargs = audit_mock.log_event.call_args
    assert kwargs["state"].value == "RESOLVED"


def test_debounce_resets_after_resolve(config):
    """Prueba 5: Después de resolverse una anomalía, un nuevo pico reinicia el contador."""
    audit_mock = MagicMock(spec=AuditLogger)
    detector = Detector(debounce_seconds=60, audit_logger=audit_mock)

    # 1. Anomalía
    t0 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.utc)
    detector.evaluate_reading(SensorReading("S01", "Zone", t0, 25.0, 50.0), config)
    
    # 2. Resuelve
    t1 = t0 + timedelta(seconds=10)
    detector.evaluate_reading(SensorReading("S01", "Zone", t1, 15.0, 50.0), config)
    
    # 3. Nueva Anomalía
    t2 = t1 + timedelta(seconds=10)
    alerts = detector.evaluate_reading(SensorReading("S01", "Zone", t2, 30.0, 50.0), config)
    
    # Debe ser tratada como nueva y no sumar a los 10+10 segundos anteriores
    assert len(alerts) == 0
    args, kwargs = audit_mock.log_event.call_args
    assert kwargs["state"].value == "DETECTED"
