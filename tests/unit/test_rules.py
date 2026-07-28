import pytest
from datetime import datetime
import pytz
from src.smart_alerts.models import SensorReading, SensorConfig
from src.smart_alerts.rules import evaluate_r01, evaluate_r02, evaluate_r04, is_off_hours

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
        critical_persistence_seconds=600,
        off_hours_persistence_seconds=300,
        offline_timeout_seconds=600
    )

def test_r01_trigger(config):
    reading = SensorReading("S01", "Zone", datetime.now(), 25.0, 500.0)
    result = evaluate_r01(reading, config)
    assert result is not None
    assert result.triggered is True
    assert result.rule_id == "R01"

def test_r01_no_trigger(config):
    reading = SensorReading("S01", "Zone", datetime.now(), 15.0, 500.0)
    result = evaluate_r01(reading, config)
    assert result is None

def test_r02_trigger_off_hours(config):
    tz = pytz.timezone("America/El_Salvador")
    # Off hours: 22:00 local time
    timestamp = tz.localize(datetime(2023, 1, 1, 22, 0, 0))
    reading = SensorReading("S01", "Zone", timestamp, 10.0, 500.0)
    result = evaluate_r02(reading, config, tz)
    assert result is not None
    assert result.rule_id == "R02"

def test_r02_no_trigger_in_hours(config):
    tz = pytz.timezone("America/El_Salvador")
    # In hours: 14:00 local time
    timestamp = tz.localize(datetime(2023, 1, 1, 14, 0, 0))
    reading = SensorReading("S01", "Zone", timestamp, 10.0, 500.0)
    result = evaluate_r02(reading, config, tz)
    assert result is None
    
def test_is_off_hours_24_7():
    # 24/7 condition: start == end
    dt = datetime(2023, 1, 1, 15, 0, 0)
    assert not is_off_hours(dt, 0, 0)
    assert not is_off_hours(dt, 7, 7)

def test_r02_timezone_conversion(config):
    tz = pytz.timezone("America/El_Salvador")
    # 10:00 AM El Salvador is in hours (7-19)
    # 10:00 AM El Salvador is 16:00 UTC
    timestamp_utc = pytz.utc.localize(datetime(2023, 1, 1, 16, 0, 0))
    reading = SensorReading("S01", "Zone", timestamp_utc, 10.0, 500.0)
    # It should convert properly and evaluate 10:00 local -> In hours -> no trigger
    result = evaluate_r02(reading, config, tz)
    assert result is None

def test_r04_trigger(config):
    reading = SensorReading("S01", "Zone", datetime.now(), 0.0, 1500.0)
    result = evaluate_r04(reading, config)
    assert result is not None
    assert result.rule_id == "R04"
