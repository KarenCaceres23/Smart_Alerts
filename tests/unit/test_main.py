from unittest.mock import MagicMock, patch

from src.main import MonitoringService


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

    # Mock config para que `get_latest_reading` retorne un valor ficticio si quisiéramos,
    # pero como tenemos 5 sensores, podemos devolver None u otro valor.
    # Aquí probamos que llame a la db 5 veces
    mock_repo_instance.get_latest_reading.return_value = None

    # Initialize service
    service = MonitoringService()

    # Run cycle
    service.run_detection_cycle()

    # Verify repository was called 5 veces
    assert mock_repo_instance.get_latest_reading.call_count == 5

    # Comprobamos las llamadas exactas
    expected_calls = [
        ("AARD-EDIF-A-CIST", "Cisterna"),
        ("AARD-EDIF-A-COCINA", "Cocina"),
        ("AARD-EDIF-A-RIEGO", "Riego"),
        ("AARD-EDIF-A-SAN1", "Sanitarios Piso 1"),
        ("AARD-EDIF-A-SAN2", "Sanitarios Piso 2"),
    ]

    actual_calls = [
        (call.kwargs["sensor_id"], call.kwargs["zone"])
        for call in mock_repo_instance.get_latest_reading.call_args_list
    ]

    assert actual_calls == expected_calls

    # Verify repository was closed at the end
    mock_repo_instance.close.assert_called_once()
