"""
Este archivo funciona como un wrapper de compatibilidad para código antiguo
que dependa de `from telegram_bot import send_telegram_alert`.
"""
import logging
from src.smart_alerts.config import load_config
from src.smart_alerts.models import Alert, Severity, SendStatus
from src.smart_alerts.cooldown.memory import MemoryCooldownManager
from src.smart_alerts.notifier.telegram import TelegramNotifier
from src.smart_alerts.utils.logging_config import setup_logging

# Inicializar un singleton del notificador para mantener el cooldown en memoria
_notifier = None
_configured = False
try:
    _config = load_config()
    setup_logging(_config.log_level, _config.app_timezone, _config.telegram_bot_token)
    _cooldown_manager = MemoryCooldownManager(_config.alert_cooldown_seconds)
    _notifier = TelegramNotifier(_config, _cooldown_manager)
    _configured = True
except Exception as e:
    _configured = False
    print(f"Error cargando configuración para telegram_bot wrapper: {e}")

def send_telegram_alert(title: str, description: str, severity: str = "MEDIA") -> bool:
    """
    Función puente para asegurar que integraciones pasadas funcionen sin cambios.
    """
    if not _configured:
        print("El notificador no está configurado correctamente.")
        return False
        
    try:
        sev_enum = Severity(severity)
    except ValueError:
        sev_enum = Severity.MEDIA
        
    # Creamos una alerta genérica para el script puente
    alert = Alert(
        rule_id="MANUAL",
        sensor_id="MANUAL_SCRIPT",
        title=title,
        description=description,
        severity=sev_enum
    )
    
    result = _notifier.send(alert)
    return result.status == SendStatus.SENT
