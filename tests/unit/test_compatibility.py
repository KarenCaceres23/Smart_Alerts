from unittest import mock
from src.telegram_bot import send_telegram_alert

@mock.patch("src.telegram_bot._notifier")
def test_compatibility_send_telegram_alert(mock_notifier):
    """Test 15: Compatibilidad con send_telegram_alert()."""
    import src.telegram_bot
    # Forzar _configured a True para saltar la validación
    src.telegram_bot._configured = True
    
    mock_result = mock.Mock()
    # Usar el enum real de SendStatus.SENT si aplica, o 'sent' como estaba
    mock_result.status = "sent" 
    mock_notifier.send.return_value = mock_result
    
    result = src.telegram_bot.send_telegram_alert("Título Viejo", "Descripción Vieja", "CRITICA")
    assert result is True
    
    # Verificamos qué alerta se generó
    alert_called = mock_notifier.send.call_args[0][0]
    assert alert_called.title == "Título Viejo"
    assert alert_called.description == "Descripción Vieja"
    assert alert_called.severity.value == "CRITICA"
    assert alert_called.rule_id == "MANUAL"
