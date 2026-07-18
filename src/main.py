import logging
from datetime import datetime
from dotenv import load_dotenv

from src.config import get_sensor_configs
from src.detector import Detector
from src.influx_client import InfluxSensorRepository
from src.telegram_bot import TelegramBot, SendStatus

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class MonitoringService:
    """Orquestador que coordina la recolección, detección y notificación."""
    def __init__(self):
        self.repository = InfluxSensorRepository()
        self.detector = Detector()
        self.bot = TelegramBot()
        self.configs = get_sensor_configs()

    def run_detection_cycle(self):
        logger.info("Iniciando ciclo de detección...")
        
        stats = {
            "processed": 0,
            "detected": 0,
            "sent": 0,
            "suppressed": 0,
            "failed": 0,
            "errors": 0
        }
        
        current_time = datetime.now()
        
        for config in self.configs:
            stats["processed"] += 1
            try:
                # 1. Obtener lectura
                reading = self.repository.get_latest_reading(config.sensor_id, config.zone)
                
                # 2. Evaluar reglas
                alerts = []
                if reading:
                    alerts.extend(self.detector.evaluate_reading(reading, config, current_time))
                else:
                    # Si no hay lectura, evaluamos R03
                    # Suponemos que last_valid_reading es None para forzar timeout, 
                    # en un caso real guardaríamos el último timestamp conocido.
                    alerts.extend(self.detector.evaluate_offline_sensor(config, None, current_time))
                
                # 3. Enviar alertas detectadas
                for alert in alerts:
                    stats["detected"] += 1
                    status = self.bot.send_alert(alert)
                    
                    if status == SendStatus.SENT:
                        stats["sent"] += 1
                        logger.info(f"Alerta enviada: {alert.rule_id} en {alert.sensor_id}")
                    elif status == SendStatus.SUPPRESSED:
                        stats["suppressed"] += 1
                        logger.info(f"Alerta suprimida (cooldown): {alert.rule_id} en {alert.sensor_id}")
                    else:
                        stats["failed"] += 1
                        logger.error(f"Fallo al enviar alerta: {alert.rule_id} en {alert.sensor_id}")
                        
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error procesando sensor {config.sensor_id}: {str(e)}")
                
        # Cerrar repositorio
        self.repository.close()
        
        # Imprimir resumen final
        print("\n--- Resumen de Ejecución ---")
        print(f"Sensores procesados: {stats['processed']}")
        print(f"Alertas detectadas: {stats['detected']}")
        print(f"Alertas enviadas: {stats['sent']}")
        print(f"Alertas suprimidas: {stats['suppressed']}")
        print(f"Errores: {stats['errors']}")

if __name__ == "__main__":
    load_dotenv()
    service = MonitoringService()
    service.run_detection_cycle()
