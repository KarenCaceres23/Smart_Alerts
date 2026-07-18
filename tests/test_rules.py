import pytest
from datetime import datetime
from src.models import SensorReading, SensorConfig
from src.rules import evaluate_r01, evaluate_r02, evaluate_r04, is_off_hours
from src.telegram_bot import Severity

@pytest.fixture
def base_config():
    return SensorConfig(
        sensor_id="S1",
        zone="Z1",
        critical_flow_threshold=20.0,
        off_hours_flow_threshold=5.0,
        daily_volume_limit=1000.0,
        operating_start_hour=8,
        operating_end_hour=18,
        critical_persistence_seconds=60,
        off_hours_persistence_seconds=60,
        offline_timeout_seconds=60
    )

def test_is_off_hours():
    # Horario normal 08:00 - 18:00
    assert not is_off_hours(datetime(2023, 1, 1, 10, 0), 8, 18)
    assert is_off_hours(datetime(2023, 1, 1, 4, 0), 8, 18)
    assert is_off_hours(datetime(2023, 1, 1, 19, 0), 8, 18)
    
    # Horario cruzando medianoche 22:00 - 06:00
    assert not is_off_hours(datetime(2023, 1, 1, 23, 0), 22, 6)
    assert not is_off_hours(datetime(2023, 1, 1, 2, 0), 22, 6)
    assert is_off_hours(datetime(2023, 1, 1, 12, 0), 22, 6)

def test_r01(base_config):
    reading = SensorReading("S1", "Z1", datetime.now(), 10.0, 0.0)
    assert evaluate_r01(reading, base_config) is None
    
    reading = SensorReading("S1", "Z1", datetime.now(), 20.0, 0.0)
    assert evaluate_r01(reading, base_config) is None
    
    reading = SensorReading("S1", "Z1", datetime.now(), 21.0, 0.0)
    result = evaluate_r01(reading, base_config)
    assert result is not None
    assert result.rule_id == "R01"
    assert result.triggered is True
    assert result.severity == Severity.CRITICAL

def test_r02(base_config):
    reading = SensorReading("S1", "Z1", datetime(2023, 1, 1, 12, 0), 10.0, 0.0)
    assert evaluate_r02(reading, base_config) is None
    
    reading = SensorReading("S1", "Z1", datetime(2023, 1, 1, 20, 0), 4.0, 0.0)
    assert evaluate_r02(reading, base_config) is None
    
    reading = SensorReading("S1", "Z1", datetime(2023, 1, 1, 20, 0), 6.0, 0.0)
    result = evaluate_r02(reading, base_config)
    assert result is not None
    assert result.rule_id == "R02"

def test_r04(base_config):
    reading = SensorReading("S1", "Z1", datetime.now(), 0.0, 500.0)
    assert evaluate_r04(reading, base_config) is None
    
    reading = SensorReading("S1", "Z1", datetime.now(), 0.0, 1001.0)
    result = evaluate_r04(reading, base_config)
    assert result is not None
    assert result.rule_id == "R04"
    assert result.severity == Severity.CRITICAL
