import os
import sys
import time
import pytest
from unittest.mock import patch

# Agregar el directorio src al path para importar correctamente los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from telegram_bot import TelegramBot, _cooldown_registry

@pytest.fixture(autouse=True)
def clean_registry():
    """Limpia el registro de cooldown antes y después de cada test para aislamiento."""
    _cooldown_registry.clear()
    yield
    _cooldown_registry.clear()

def test_initial_alert_not_blocked():
    """Test 1: Una alerta nueva no debe ser bloqueada por el sistema de debounce/cooldown."""
    bot = TelegramBot()
    # La primera vez que se evalúa una alerta nueva no debe estar en cooldown
    assert bot._is_in_cooldown("Alerta Sismo", "Magnitud 4.5", "ALTA") is False

def test_duplicate_alert_within_cooldown_is_blocked():
    """Test 2: Enviar la misma alerta inmediatamente después debe activar el bloqueo anti-spam."""
    bot = TelegramBot()
    # Primera ejecución (registra la hora de envío)
    bot._is_in_cooldown("Alerta Sismo", "Magnitud 4.5", "ALTA")
    # Segunda ejecución inmediata (debe ser bloqueada por debounce)
    assert bot._is_in_cooldown("Alerta Sismo", "Magnitud 4.5", "ALTA") is True

def test_different_alert_not_blocked_by_debounce():
    """Test 3: Una alerta con diferente título o descripción no debe ser bloqueada."""
    bot = TelegramBot()
    bot._is_in_cooldown("Alerta Sismo", "Magnitud 4.5", "ALTA")
    # Alerta diferente debe permitirse sin problemas
    assert bot._is_in_cooldown("Alerta Sismo", "Magnitud 5.2", "CRITICA") is False

def test_cooldown_expiration_allows_alert():
    """Test 4: Una vez transcurrido el tiempo de cooldown, la misma alerta debe volver a permitirse."""
    bot = TelegramBot()
    bot.cooldown_seconds = 10  # Configurar cooldown a 10 segundos para la prueba
    
    with patch('time.time') as mock_time:
        mock_time.return_value = 1000.0
        # Primera alerta en el tiempo t=1000
        assert bot._is_in_cooldown("Alerta Presion", "Presión alta en válvula", "MEDIA") is False
        
        # Simular que pasaron 15 segundos (t=1015, mayor a los 10s de cooldown)
        mock_time.return_value = 1015.0
        assert bot._is_in_cooldown("Alerta Presion", "Presión alta en válvula", "MEDIA") is False

def test_custom_cooldown_seconds_configuration():
    """Test 5: Validar el comportamiento con duración de cooldown personalizada en el bot."""
    bot = TelegramBot()
    bot.cooldown_seconds = 5  # Solo 5 segundos
    
    with patch('time.time') as mock_time:
        mock_time.return_value = 2000.0
        bot._is_in_cooldown("Alerta Sensor", "Sensor desconectado", "BAJA")
        
        # A los 3 segundos sigue bloqueado por el debounce
        mock_time.return_value = 2003.0
        assert bot._is_in_cooldown("Alerta Sensor", "Sensor desconectado", "BAJA") is True
        
        # A los 6 segundos el tiempo expiró y ya está liberado
        mock_time.return_value = 2006.0
        assert bot._is_in_cooldown("Alerta Sensor", "Sensor desconectado", "BAJA") is False
