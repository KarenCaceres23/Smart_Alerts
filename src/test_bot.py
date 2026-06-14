from telegram_bot import send_telegram_alert

def main():
    print("Iniciando prueba del bot de Telegram de SmartH2O...\n")
    print("Enviando primer mensaje de prueba...")
    
    # Enviar mensaje de prueba con severidad BAJA
    resultado1 = send_telegram_alert(
        title="Prueba de integración del bot <OK>",
        description="El bot de SmartH2O está funcionando correctamente y las etiquetas HTML están seguras.",
        severity="BAJA"
    )
    
    if resultado1 == True:
        print("\n✅ Prueba 1 exitosa. ¡Revisa tu aplicación de Telegram!")
    else:
        print("\n❌ La prueba 1 falló. Revisa los errores en la consola.")
        print("💡 Sugerencia: Revisa que tu archivo .env esté bien configurado.")

    print("\nEnviando segundo mensaje idéntico para probar el cooldown...")
    
    # Enviar mensaje idéntico para probar cooldown sin hacer spam real
    resultado2 = send_telegram_alert(
        title="Prueba de integración del bot <OK>",
        description="El bot de SmartH2O está funcionando correctamente y las etiquetas HTML están seguras.",
        severity="BAJA"
    )
    
    if resultado2 == False:
        print("\n✅ Prueba 2 exitosa: alerta repetida omitida por el sistema anti-spam (cooldown).")
    else:
        print("\n❌ La prueba 2 falló en el cooldown: el mensaje se envió de nuevo en lugar de ser bloqueado.")

if __name__ == "__main__":
    main()
