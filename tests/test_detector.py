import pytest
from datetime import datetime, timedelta
from src.models import SensorReading, SensorConfig
from src.detector import Detector

@pytest.fixture
def config():
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
        offline_timeout_seconds=300
    )

def test_detector_no_alerts(config):
    detector = Detector()
    reading = SensorReading("S1", "Z1", datetime.now(), 10.0, 100.0)
    alerts = detector.evaluate_reading(reading, config)
    assert len(alerts) == 0

def test_detector_persistence_r01(config):
    detector = Detector()
    base_time = datetime(2023, 1, 1, 12, 0, 0)
    
    # 1. Primera lectura por encima del umbral, no debe alertar aún (persistencia)
    reading = SensorReading("S1", "Z1", base_time, 25.0, 100.0)
    alerts = detector.evaluate_reading(reading, config, current_time=base_time)
    assert len(alerts) == 0
    
    # 2. Segunda lectura 30 seg después, sin alerta
    current_time = base_time + timedelta(seconds=30)
    alerts = detector.evaluate_reading(reading, config, current_time=current_time)
    assert len(alerts) == 0
    
    # 3. Tercera lectura 60 seg después, genera alerta
    current_time = base_time + timedelta(seconds=60)
    alerts = detector.evaluate_reading(reading, config, current_time=current_time)
    assert len(alerts) == 1
    assert alerts[0].rule_id == "R01"
    
    # 4. Condición vuelve a la normalidad, se resuelve
    current_time = base_time + timedelta(seconds=90)
    normal_reading = SensorReading("S1", "Z1", current_time, 10.0, 100.0)
    alerts = detector.evaluate_reading(normal_reading, config, current_time=current_time)
    assert len(alerts) == 0
    assert ("S1", "R01") not in detector._active_conditions

def test_detector_offline_sensor(config):
    detector = Detector()
    current_time = datetime(2023, 1, 1, 12, 5, 0)
    last_reading = datetime(2023, 1, 1, 12, 0, 0)
    
    alerts = detector.evaluate_offline_sensor(config, last_reading, current_time=current_time)
    assert len(alerts) == 1
    assert alerts[0].rule_id == "R03"
