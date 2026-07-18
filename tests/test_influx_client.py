import pytest
from unittest.mock import patch, MagicMock
from src.influx_client import InfluxSensorRepository

@patch("src.influx_client.InfluxDBClient")
def test_influx_client_empty_result(mock_client):
    # Simular API de consulta sin resultados
    mock_query_api = MagicMock()
    mock_query_api.query.return_value = []
    
    mock_client.return_value.query_api.return_value = mock_query_api
    
    repo = InfluxSensorRepository(token="fake_token")
    reading = repo.get_latest_reading("S1", "Z1")
    
    assert reading is None

@patch("src.influx_client.InfluxDBClient")
def test_influx_client_valid_result(mock_client):
    # Simular resultado válido
    mock_record = MagicMock()
    mock_record.values = {"flow_rate": 15.0, "daily_volume": 100.0}
    mock_record.get_time.return_value = "2023-01-01T12:00:00Z"
    
    mock_table = MagicMock()
    mock_table.records = [mock_record]
    
    mock_query_api = MagicMock()
    mock_query_api.query.return_value = [mock_table]
    
    mock_client.return_value.query_api.return_value = mock_query_api
    
    repo = InfluxSensorRepository(token="fake_token")
    reading = repo.get_latest_reading("S1", "Z1")
    
    assert reading is not None
    assert reading.flow_rate == 15.0
    assert reading.daily_volume == 100.0
