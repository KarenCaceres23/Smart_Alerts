import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Asegurar que el path sea correcto para importar src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.smart_alerts.models import Alert, Severity
from src.smart_alerts.config import load_config
from src.smart_alerts.cooldown.memory import MemoryCooldownManager
from src.smart_alerts.audit import AuditLogger
from src.smart_alerts.notifier.telegram import TelegramNotifier

load_dotenv()
config = load_config()

audit_logger = AuditLogger(config.audit_log_path, config.app_timezone)
cooldown_manager = MemoryCooldownManager(config.alert_cooldown_seconds)
notifier = TelegramNotifier(config, cooldown_manager, audit_logger)

alert1 = Alert(
    rule_id="R01",
    sensor_id="SH2O-ZA-001",
    title="🔴 ALERTA: Flujo Crítico Detectado",
    description="El sensor en Sanitarios piso 1 detectó un flujo de 35 L/min superando el límite de 20 L/min.",
    severity=Severity.CRITICA,
    metadata={"flow_rate": 35.0, "threshold": 20.0}
)

alert2 = Alert(
    rule_id="R03",
    sensor_id="SH2O-ZA-001",
    title="🟡 ADVERTENCIA: Volumen Diario Excedido",
    description="Se ha superado el límite diario de volumen de agua en Sanitarios piso 1.",
    severity=Severity.MEDIA,
    metadata={"daily_volume": 1050.0, "limit": 1000.0}
)

print("Enviando Alerta 1...")
res1 = notifier.send(alert1)
print(f"Resultado 1: {res1.status}")

print("Enviando Alerta 2...")
res2 = notifier.send(alert2)
print(f"Resultado 2: {res2.status}")
