# Bot de Telegram - Alertas SmartH2O

Este repositorio contiene el módulo de notificaciones de Telegram para el proyecto **SmartH2O**. Su función principal es recibir eventos del sistema y enviar alertas de texto formateadas a un grupo o usuario de Telegram.

## Descripción general

El código se conecta a la API de Telegram para automatizar los avisos. Entre sus características están:
- Envío de mensajes en formato HTML con el nivel de severidad y la hora exacta.
- Uso de variables de entorno para no exponer los tokens de seguridad en el código fuente.
- Un sistema de protección "anti-spam" (cooldown) que evita que se mande la misma alerta muchas veces seguidas si un sensor falla o el sistema se queda pegado.

## Instalación

1. Primero clona este repositorio en tu equipo.
2. Instala las dependencias necesarias de Python:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración del Entorno

Es necesario configurar tus propias credenciales para que el bot funcione.

1. Crea un archivo llamado `.env` basándote en el archivo de ejemplo (`.env.example`).
2. Llena los datos con tu información:
   - `TELEGRAM_BOT_TOKEN`: El token que te da BotFather al crear tu bot en Telegram.
   - `TELEGRAM_CHAT_ID`: El ID numérico del chat o grupo donde el bot mandará los mensajes.
   - `ALERT_COOLDOWN_SECONDS`: El tiempo de espera en segundos antes de dejar pasar una alerta repetida (por ejemplo, 60).

**Nota de seguridad:** Nunca subas tu archivo `.env` a GitHub ni compartas tu Token. Si lo haces por error, debes generar uno nuevo en BotFather para evitar que otros controlen tu bot.

## ¿Cómo probarlo?

Si no sabes tu `TELEGRAM_CHAT_ID`, primero mándale un mensaje a tu bot en Telegram y luego corre este script para averiguar tu ID numérico:
```bash
python src/get_chat_id.py
```

Una vez que tengas configurado todo tu `.env`, puedes lanzar una alerta de prueba ejecutando:
```bash
python src/test_bot.py
```

Este script de prueba mandará una alerta a tu Telegram y luego intentará mandar otra igual de inmediato para comprobar que el sistema anti-spam funciona correctamente (la segunda será bloqueada en la consola).

## Problemas comunes

Si la prueba no te funciona, revisa lo siguiente:
- **Error 401 Unauthorized:** Tu token está mal escrito o caducado. Revisa tu `.env`.
- **Chat not found:** El bot no encuentra el chat. Recuerda que siempre tienes que escribirle tú primero al bot en Telegram antes de poder enviar mensajes por código.
- **getUpdates devuelve vacío:** Si al correr `get_chat_id.py` no te sale nada, es porque la API limpió los mensajes viejos. Mándale un "hola" a tu bot en Telegram y vuelve a correr el script.
