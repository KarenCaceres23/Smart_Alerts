from telegram_bot import Alert, SendStatus, Severity, TelegramBot


def main() -> None:
    print("Iniciando prueba del bot de Telegram de SmartH2O...\n")

    bot = TelegramBot()
    pruebas_exitosas = 0
    total_pruebas = 4

    print("1. Enviando primera alerta...")

    alerta_1 = Alert(
        rule_id="R01",
        sensor_id="sensor_03",
        zone="Cocina",
        value=42.5,
        threshold=20.0,
        severity=Severity.CRITICAL,
        description="Caudal superior al límite permitido.",
        recommended_action="Revisar tuberías, válvulas y posibles fugas.",
    )

    estado_1 = bot.send_alert(alerta_1)

    if estado_1 == SendStatus.SENT:
        pruebas_exitosas += 1
        print("✅ Prueba 1 exitosa. Estado: SENT\n")
    else:
        print(f"❌ Prueba 1 falló. Estado devuelto: {estado_1}\n")

    print(
        "2. Enviando segunda alerta inmediata "
        "(mismo sensor y regla, diferente valor)..."
    )

    alerta_2 = Alert(
        rule_id="R01",
        sensor_id="sensor_03",
        zone="Cocina",
        value=43.0,
        threshold=20.0,
        severity=Severity.CRITICAL,
        description="Caudal superior al límite permitido.",
        recommended_action="Revisar tuberías, válvulas y posibles fugas.",
    )

    estado_2 = bot.send_alert(alerta_2)

    if estado_2 == SendStatus.SUPPRESSED:
        pruebas_exitosas += 1
        print(
            "✅ Prueba 2 exitosa. "
            "La alerta fue suprimida por debounce. "
            "Estado: SUPPRESSED\n"
        )
    else:
        print(f"❌ Prueba 2 falló. Estado devuelto: {estado_2}\n")

    print("3. Enviando alerta de otro sensor con la misma regla...")

    alerta_3 = Alert(
        rule_id="R01",
        sensor_id="sensor_04",
        zone="Sanitarios",
        value=25.0,
        threshold=20.0,
        severity=Severity.WARNING,
        description="Caudal superior al límite permitido.",
        recommended_action="Verificar el uso de agua en los sanitarios.",
    )

    estado_3 = bot.send_alert(alerta_3)

    if estado_3 == SendStatus.SENT:
        pruebas_exitosas += 1
        print(
            "✅ Prueba 3 exitosa. "
            "Se envió la alerta de otro sensor. "
            "Estado: SENT\n"
        )
    else:
        print(f"❌ Prueba 3 falló. Estado devuelto: {estado_3}\n")

    print("4. Enviando otra regla para el primer sensor...")

    alerta_4 = Alert(
        rule_id="R03",
        sensor_id="sensor_03",
        zone="Cocina",
        value=None,
        threshold=None,
        severity=Severity.INFO,
        description="Sensor sin comunicación durante 10 minutos.",
        recommended_action=(
            "Revisar la alimentación eléctrica, la red, "
            "el broker MQTT y el servicio de ingestión."
        ),
    )

    estado_4 = bot.send_alert(alerta_4)

    if estado_4 == SendStatus.SENT:
        pruebas_exitosas += 1
        print(
            "✅ Prueba 4 exitosa. "
            "Se envió la alerta de otra regla. "
            "Estado: SENT\n"
        )
    else:
        print(f"❌ Prueba 4 falló. Estado devuelto: {estado_4}\n")

    print("=" * 55)
    print(f"Resultado final: {pruebas_exitosas}/{total_pruebas} pruebas exitosas.")

    if pruebas_exitosas == total_pruebas:
        print("✅ Todas las pruebas manuales finalizaron correctamente.")
    else:
        print("❌ Una o más pruebas no produjeron el resultado esperado.")


if __name__ == "__main__":
    main()
