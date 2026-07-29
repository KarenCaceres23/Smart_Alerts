from src.smart_alerts.audit import AuditLogger
from src.smart_alerts.config import load_config
from src.smart_alerts.cooldown.memory import MemoryCooldownManager
from src.smart_alerts.models import Alert, SendStatus, Severity
from src.smart_alerts.notifier.telegram import TelegramNotifier
from src.smart_alerts.utils.logging_config import setup_logging


def main() -> None:
    print("Iniciando prueba manual del Notificador de Telegram...")

    # 1. Cargar configuración
    try:
        config = load_config()
        setup_logging(config.log_level, config.app_timezone, config.telegram_bot_token)
    except ValueError as e:
        print(f"Error de configuración: {e}")
        print("Asegúrate de haber copiado .env.example a .env y configurado las variables.")
        return

    # 2. Instanciar manejadores
    try:
        audit_logger = AuditLogger(config.audit_log_path, config.app_timezone)
        cooldown_manager = MemoryCooldownManager(config.alert_cooldown_seconds)
        bot = TelegramNotifier(config, cooldown_manager, audit_logger)
    except Exception as e:
        print(f"❌ Error al configurar el notificador: {e}")
        return

    pruebas_exitosas = 0
    total_pruebas = 4

    print("1. Enviando primera alerta...")

    alerta_1 = Alert(
        rule_id="R01",
        sensor_id="sensor_03",
        title="Flujo Crítico Detectado",
        description="Caudal superior al límite permitido.\nZona: Cocina\nValor detectado: 42.50\nUmbral: 20.00",
        severity=Severity.CRITICA,
    )

    estado_1 = bot.send(alerta_1)

    if estado_1.status == SendStatus.SENT:
        pruebas_exitosas += 1
        print("[OK] Prueba 1 exitosa. Estado: SENT\n")
    else:
        print(f"[ERROR] Prueba 1 falló. Estado devuelto: {estado_1.status}\n")

    print("2. Enviando segunda alerta inmediata " "(mismo sensor y regla, diferente valor)...")

    alerta_2 = Alert(
        rule_id="R01",
        sensor_id="sensor_03",
        title="Flujo Crítico Detectado",
        description="Caudal superior al límite permitido.\nZona: Cocina\nValor detectado: 43.00\nUmbral: 20.00",
        severity=Severity.CRITICA,
    )

    estado_2 = bot.send(alerta_2)

    if estado_2.status == SendStatus.SUPPRESSED:
        pruebas_exitosas += 1
        print(
            "[OK] Prueba 2 exitosa. "
            "La alerta fue suprimida por debounce. "
            "Estado: SUPPRESSED\n"
        )
    else:
        print(f"[ERROR] Prueba 2 falló. Estado devuelto: {estado_2.status}\n")

    print("3. Enviando alerta de otro sensor con la misma regla...")

    alerta_3 = Alert(
        rule_id="R01",
        sensor_id="sensor_04",
        title="Flujo Detectado",
        description="Caudal superior al límite permitido.\nZona: Sanitarios\nValor detectado: 25.00\nUmbral: 20.00",
        severity=Severity.MEDIA,
    )

    estado_3 = bot.send(alerta_3)

    if estado_3.status == SendStatus.SENT:
        pruebas_exitosas += 1
        print("[OK] Prueba 3 exitosa. " "Se envió la alerta de otro sensor. " "Estado: SENT\n")
    else:
        print(f"[ERROR] Prueba 3 falló. Estado devuelto: {estado_3.status}\n")

    print("4. Enviando otra regla para el primer sensor...")

    alerta_4 = Alert(
        rule_id="R03",
        sensor_id="sensor_03",
        title="Sensor Desconectado",
        description="Sensor sin comunicación durante 10 minutos.\nZona: Cocina",
        severity=Severity.BAJA,
    )

    estado_4 = bot.send(alerta_4)

    if estado_4.status == SendStatus.SENT:
        pruebas_exitosas += 1
        print("[OK] Prueba 4 exitosa. " "Se envió la alerta de otra regla. " "Estado: SENT\n")
    else:
        print(f"[ERROR] Prueba 4 falló. Estado devuelto: {estado_4.status}\n")

    print("=" * 55)
    print(f"Resultado final: {pruebas_exitosas}/{total_pruebas} pruebas exitosas.")

    if pruebas_exitosas == total_pruebas:
        print("[OK] Todas las pruebas manuales finalizaron correctamente.")
    else:
        print("[ERROR] Una o más pruebas no produjeron el resultado esperado.")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    main()
