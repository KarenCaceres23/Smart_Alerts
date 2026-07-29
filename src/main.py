import logging
from datetime import datetime

import pytz

from src.smart_alerts.audit import AuditLogger
from src.smart_alerts.config import load_config
from src.smart_alerts.cooldown.memory import MemoryCooldownManager
from src.smart_alerts.detector import Detector
from src.smart_alerts.models import SendStatus, SensorConfig
from src.smart_alerts.notifier.telegram import TelegramNotifier
from src.smart_alerts.utils.logging_config import setup_logging


# Simulamos la carga de configuraciones por sensor por simplicidad académica
def get_sensor_configs() -> list[SensorConfig]:
    return [
        SensorConfig(
            sensor_id="SH2O-ZA-001",
            zone="Sanitarios piso 1",
            critical_flow_threshold=20.0,
            off_hours_flow_threshold=5.0,
            daily_volume_limit=1000.0,
            operating_start_hour=7,
            operating_end_hour=19,
            critical_persistence_seconds=600,
            off_hours_persistence_seconds=300,
            offline_timeout_seconds=600,
        )
    ]


logger = logging.getLogger(__name__)


class MonitoringService:
    """Orquestador principal."""

    def __init__(self):
        self.config = load_config()
        setup_logging(
            self.config.log_level, self.config.app_timezone, self.config.telegram_bot_token
        )

        self.audit_logger = AuditLogger(self.config.audit_log_path, self.config.app_timezone)
        self.cooldown_manager = MemoryCooldownManager(self.config.alert_cooldown_seconds)
        self.notifier = TelegramNotifier(self.config, self.cooldown_manager, self.audit_logger)

        self.detector = Detector(
            self.config.alert_debounce_seconds, self.audit_logger, self.config.app_timezone
        )
        self.configs = get_sensor_configs()

        # En una app real, aquí se inicializaría el repositorio de InfluxDB
        self.repository = None

    def run_detection_cycle(self):
        logger.info("Iniciando ciclo de detección...")

        stats = {
            "processed": 0,
            "detected": 0,
            "sent": 0,
            "suppressed": 0,
            "failed": 0,
            "errors": 0,
        }

        tz = pytz.timezone(self.config.app_timezone)
        current_time = datetime.now(tz)

        for config in self.configs:
            stats["processed"] += 1
            try:
                # Aquí normalmente buscaríamos la lectura de InfluxDB
                reading = None

                alerts = []
                if reading:
                    alerts.extend(self.detector.evaluate_reading(reading, config, current_time))
                else:
                    alerts.extend(self.detector.evaluate_offline_sensor(config, None, current_time))

                for alert in alerts:
                    stats["detected"] += 1
                    result = self.notifier.send(alert)

                    if result.status == SendStatus.SENT:
                        stats["sent"] += 1
                    elif result.status == SendStatus.SUPPRESSED:
                        stats["suppressed"] += 1
                    else:
                        stats["failed"] += 1

            except Exception:
                stats["errors"] += 1
                logger.error(f"Error procesando sensor {config.sensor_id}", exc_info=True)

        # Limpieza de memoria
        self.cooldown_manager.cleanup()

        logger.info(
            f"Resumen de Ejecución: Procesados={stats['processed']}, Detectados={stats['detected']}, Enviados={stats['sent']}, Suprimidos={stats['suppressed']}, Fallidos={stats['failed']}, Errores={stats['errors']}"
        )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    service = MonitoringService()
    service.run_detection_cycle()
