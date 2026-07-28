import pytest
from unittest import mock
from requests.exceptions import Timeout, ConnectionError, RequestException
from datetime import datetime, timezone
from src.smart_alerts.notifier.telegram import TelegramNotifier
from src.smart_alerts.models import Alert, Severity, SendStatus
from src.smart_alerts.config import AppConfig

class DummyCooldownManager:
    def __init__(self, in_cooldown=False):
        self._in_cooldown = in_cooldown
        self.marked = False
        
    def is_in_cooldown(self, alert_id):
        return self._in_cooldown
        
    def mark_as_sent(self, alert_id):
        self.marked = True
        
    def cleanup(self):
        pass

@pytest.fixture
def config():
    return AppConfig(
        telegram_bot_token="test_token",
        telegram_chat_id="123",
        telegram_timeout_seconds=1,
        telegram_max_retries=2,
        telegram_backoff_seconds=0, # 0 for fast tests
        alert_cooldown_seconds=300,
        app_timezone="UTC",
        log_level="INFO"
    )

@pytest.fixture
def alert():
    return Alert("R01", "S01", "Title", "Desc", "BAJA", occurred_at=datetime.now(timezone.utc))

@mock.patch("requests.post")
def test_successful_send(mock_post, config, alert):
    """Test 1: Envío exitoso."""
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True}
    mock_post.return_value = mock_response
    
    cooldown = DummyCooldownManager()
    audit_mock = mock.MagicMock()
    notifier = TelegramNotifier(config, cooldown, audit_mock)
    
    result = notifier.send(alert)
    assert result.status == SendStatus.SENT
    assert result.attempts == 1
    assert cooldown.marked is True
    assert audit_mock.log_event.call_count == 1
    args, kwargs = audit_mock.log_event.call_args
    assert kwargs["state"].value == "SENT"

@mock.patch("requests.post")
def test_timeout(mock_post, config, alert):
    """Test 3: Timeout."""
    mock_post.side_effect = Timeout("Timeout")
    
    cooldown = DummyCooldownManager()
    notifier = TelegramNotifier(config, cooldown)
    
    result = notifier.send(alert)
    assert result.status == SendStatus.FAILED
    assert result.attempts == 2 # max retries = 2
    assert cooldown.marked is False

@mock.patch("requests.post")
def test_connection_error(mock_post, config, alert):
    """Test 4: Error de conexión."""
    mock_post.side_effect = ConnectionError("Conn Error")
    
    cooldown = DummyCooldownManager()
    notifier = TelegramNotifier(config, cooldown)
    
    result = notifier.send(alert)
    assert result.status == SendStatus.FAILED
    assert result.attempts == 2

@mock.patch("requests.post")
def test_http_401(mock_post, config, alert):
    """Test 5: HTTP 401."""
    mock_response = mock.Mock()
    mock_response.status_code = 401
    mock_error = RequestException("401")
    mock_error.response = mock_response
    mock_post.side_effect = mock_error
    
    cooldown = DummyCooldownManager()
    notifier = TelegramNotifier(config, cooldown)
    
    result = notifier.send(alert)
    assert result.status == SendStatus.FAILED
    assert result.attempts == 1 # 401 no se reintenta

@mock.patch("time.sleep")
@mock.patch("requests.post")
def test_http_429_retry_after(mock_post, mock_sleep, config, alert):
    """Test 6: HTTP 429 con retry_after."""
    # Primer intento da 429, segundo da 200
    mock_resp_429 = mock.Mock()
    mock_resp_429.status_code = 429
    mock_resp_429.json.return_value = {"parameters": {"retry_after": 5}}
    
    mock_resp_200 = mock.Mock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {"ok": True}
    
    mock_post.side_effect = [mock_resp_429, mock_resp_200]
    
    cooldown = DummyCooldownManager()
    notifier = TelegramNotifier(config, cooldown)
    
    result = notifier.send(alert)
    
    assert result.status == SendStatus.SENT
    # attempts stays 1 because 429 doesn't consume network retries
    assert result.attempts == 1
    mock_sleep.assert_called_with(5)
    assert cooldown.marked is True

@mock.patch("time.sleep")
@mock.patch("requests.post")
def test_http_429_limit_reached(mock_post, mock_sleep, config, alert):
    """Test 6.1: HTTP 429 sobrepasa el límite (MAX_429_RETRIES = 3)."""
    mock_resp_429 = mock.Mock()
    mock_resp_429.status_code = 429
    mock_resp_429.json.return_value = {"parameters": {"retry_after": 1}}
    
    # Proveer 4 veces 429 para forzar el quiebre
    mock_post.side_effect = [mock_resp_429] * 4
    
    cooldown = DummyCooldownManager()
    notifier = TelegramNotifier(config, cooldown)
    
    result = notifier.send(alert)
    
    assert result.status == SendStatus.FAILED
    assert result.error == "HTTP 429 Rate Limit Exceeded permanently"

@mock.patch("requests.post")
def test_http_400_and_403(mock_post, config, alert):
    """Test 8: HTTP 400 y 403."""
    cooldown = DummyCooldownManager()
    notifier = TelegramNotifier(config, cooldown)
    
    # Test 400
    mock_response = mock.Mock()
    mock_response.status_code = 400
    mock_error = RequestException("400")
    mock_error.response = mock_response
    mock_post.side_effect = mock_error
    
    result = notifier.send(alert)
    assert result.status == SendStatus.FAILED
    assert result.attempts == 1 # 400 no se reintenta
    
    # Test 403
    mock_response.status_code = 403
    mock_error.response = mock_response
    mock_post.side_effect = mock_error
    
    result = notifier.send(alert)
    assert result.status == SendStatus.FAILED
    assert result.attempts == 1 # 403 no se reintenta

@mock.patch("requests.post")
def test_invalid_telegram_response(mock_post, config, alert):
    """Test 9: Respuesta Telegram 200 OK pero con error lógico (ok: False)."""
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": False, "description": "Bad Request: chat not found"}
    mock_post.return_value = mock_response
    
    cooldown = DummyCooldownManager()
    notifier = TelegramNotifier(config, cooldown)
    
    result = notifier.send(alert)
    assert result.status == SendStatus.FAILED
    assert result.error == "Bad Request: chat not found"
    assert result.attempts == 1 # No se reintenta errores lógicos de Telegram

@mock.patch("requests.post")
def test_generic_http_error(mock_post, config, alert):
    """Test 7: Error HTTP genérico."""
    mock_response = mock.Mock()
    mock_response.status_code = 500
    mock_error = RequestException("500")
    mock_error.response = mock_response
    mock_post.side_effect = mock_error
    
    cooldown = DummyCooldownManager()
    notifier = TelegramNotifier(config, cooldown)
    
    result = notifier.send(alert)
    assert result.status == SendStatus.FAILED
    assert result.attempts == 2 # 500 sí se reintenta

def test_html_characters(config, alert):
    """Test 10: Caracteres HTML en título y descripción."""
    alert_html = Alert("R01", "S01", "<Script>Title", "Desc & <b>Bold</b>", "BAJA", occurred_at=datetime.now(timezone.utc))
    cooldown = DummyCooldownManager()
    notifier = TelegramNotifier(config, cooldown)
    
    msg = notifier._build_message(alert_html)
    assert "&lt;Script&gt;Title" in msg
    assert "Desc &amp; &lt;b&gt;Bold&lt;/b&gt;" in msg

def test_hide_token_in_logs(caplog):
    """Test 17: Ocultamiento de token en logs."""
    from src.smart_alerts.utils.logging_config import setup_logging
    
    # Configuramos el log con un token falso para ocultar
    setup_logging("INFO", "UTC", "secreto123")
    
    logger = logging.getLogger(__name__)
    logger.error("Error al conectar con https://api.telegram.org/botsecreto123/sendMessage")
    
    # El caplog captura todo, verificamos que no está el secreto
    for record in caplog.records:
        if record.levelno == logging.ERROR:
            # Notar que record.message tiene el original, 
            # pero al formatearlo para la salida final es donde se enmascara.
            # En pytest caplog el message puede no estar parseado por nuestro formatter.
            # Nuestro formatter actúa a nivel de Handler.
            # Para testear el formatter de verdad instanciamos y formateamos:
            from src.smart_alerts.utils.logging_config import TimezoneFormatter
            fmt = TimezoneFormatter(mask_token="secreto123")
            formatted = fmt.format(record)
            assert "secreto123" not in formatted
            assert "***TOKEN_OCULTO***" in formatted
