from unittest.mock import MagicMock, patch

from src.main import MonitoringService
from src.smart_alerts.models import SensorReading


@patch("src.main.InfluxSensorRepository")
@patch("src.main.AuditLogger")
@patch("src.main.TelegramNotifier")
@patch("src.main.load_config")
@patch("src.main.setup_logging")
def test_monitoring_service_uses_influx_repository(
    mock_setup_logging, mock_load_config, mock_notifier, mock_audit_logger, mock_influx_repo_class
):
    mock_config = MagicMock()
    mock_config.alert_debounce_seconds = 60
    mock_config.alert_cooldown_seconds = 300
    mock_config.app_timezone = "UTC"
    mock_config.telegram_bot_token = "test"
    mock_config.audit_log_path = "audit.jsonl"
    mock_load_config.return_value = mock_config

    mock_repo_instance = MagicMock()
    mock_influx_repo_class.return_value = mock_repo_instance

    mock_reading = SensorReading(
        sensor_id="SH2O-ZA-001",
        zone="Sanitarios piso 1",
        timestamp="2023-10-27T10:00:00Z",
        flow_rate=25.0,
        daily_volume=500.0,
    )
    mock_repo_instance.get_latest_reading.return_value = mock_reading

    # Initialize service
    service = MonitoringService()

    # Run cycle
    service.run_detection_cycle()

    # Verify repository was called
    mock_repo_instance.get_latest_reading.assert_called_once()
    args, kwargs = mock_repo_instance.get_latest_reading.call_args
    assert kwargs["sensor_id"] == "SH2O-ZA-001"
    assert kwargs["zone"] == "Sanitarios piso 1"

    # Verify repository was closed at the end
    mock_repo_instance.close.assert_called_once()
