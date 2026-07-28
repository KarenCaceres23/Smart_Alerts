import pytest
import pytz
from datetime import datetime, timedelta
from src.smart_alerts.detector import Detector
from src.smart_alerts.models import SensorConfig, SensorReading

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
        offline_timeout_seconds=600
    )

from src.smart_alerts.audit import AuditLogger
from unittest.mock import MagicMock

def test_detector_offline_pending(config):
    detector = Detector(debounce_seconds=60)
    # last_valid_reading is None -> should return no alerts
    alerts = detector.evaluate_offline_sensor(config, None)
    assert len(alerts) == 0

def test_detector_persistence_history(config):
    audit_mock = MagicMock(spec=AuditLogger)
    detector = Detector(debounce_seconds=60, audit_logger=audit_mock)
    
    # Send a reading that breaches threshold at T=0
    t0 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.utc)
    reading1 = SensorReading("S01", "Zone", t0, 25.0, 50.0)
    alerts = detector.evaluate_reading(reading1, config)
    assert len(alerts) == 0 # First time, just registered, no alert yet
    
    assert audit_mock.log_event.call_count == 1
    # Check that DETECTED was logged
    args, kwargs = audit_mock.log_event.call_args
    assert kwargs["state"].value == "DETECTED"
    
    # Send another reading 30 seconds later (threshold not reached 60s)
    t1 = t0 + timedelta(seconds=30)
    reading2 = SensorReading("S01", "Zone", t1, 25.0, 50.0)
    alerts = detector.evaluate_reading(reading2, config)
    assert len(alerts) == 0
    assert audit_mock.log_event.call_count == 2
    args, kwargs = audit_mock.log_event.call_args
    assert kwargs["state"].value == "PENDING_DEBOUNCE"
    
    # Send another reading 65 seconds later
    t2 = t0 + timedelta(seconds=65)
    reading3 = SensorReading("S01", "Zone", t2, 25.0, 50.0)
    alerts = detector.evaluate_reading(reading3, config)
    assert len(alerts) == 1
    assert alerts[0].rule_id == "R01"

def test_detector_resolves_condition(config):
    audit_mock = MagicMock(spec=AuditLogger)
    detector = Detector(debounce_seconds=60, audit_logger=audit_mock)
    
    t0 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.utc)
    reading1 = SensorReading("S01", "Zone", t0, 25.0, 50.0)
    detector.evaluate_reading(reading1, config) # Breaches, starts debounce
    
    t1 = t0 + timedelta(seconds=10)
    reading2 = SensorReading("S01", "Zone", t1, 5.0, 50.0) # Normal reading
    detector.evaluate_reading(reading2, config) # Should resolve condition
    
    # audit_logger should have recorded RESOLVED
    args, kwargs = audit_mock.log_event.call_args
    assert kwargs["state"].value == "RESOLVED"
