from unittest import mock
from src.telegram_bot import send_telegram_alert

@mock.patch("src.telegram_bot._notifier.send")
def test_compatibility_send_telegram_alert(mock_send):
    """Test 15: Compatibilidad con send_telegram_alert()."""
    mock_result = mock.Mock()
    mock_result.status = "sent" # o SendStatus.SENT
    mock_send.return_value = mock_result
    
    result = send_telegram_alert("Título Viejo", "Descripción Vieja", "CRITICA")
    assert result is True
    
    # Verificamos qué alerta se generó
    alert_called = mock_send.call_args[0][0]
    assert alert_called.title == "Título Viejo"
    assert alert_called.description == "Descripción Vieja"
    assert alert_called.severity.value == "CRITICA"
    assert alert_called.rule_id == "MANUAL"
