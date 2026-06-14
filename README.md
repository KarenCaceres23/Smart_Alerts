# SmartH2O Telegram Bot

Este proyecto es una integración de notificaciones por Telegram para el proyecto académico **SmartH2O**. Permite enviar alertas de forma automatizada, segura y profesional ante eventos del sistema, con niveles de severidad y protección anti-spam.

## 📋 ¿Qué hace este proyecto?
Contiene los scripts para conectarse a la API de Telegram y enviar notificaciones. Incluye buenas prácticas de seguridad (variables de entorno), protección contra inyección de HTML, soporte para diferentes niveles de severidad con emojis, un sistema de cooldown (anti-spam) y una clase `TelegramBot` escalable, lista para integrarse con futuros módulos.

## 🚀 Instalación y Preparación

1. Asegúrate de tener Python instalado en tu sistema.
2. Instala las dependencias necesarias. En tu terminal ejecuta:

**Windows PowerShell / Linux / Mac:**
```bash
pip install -r requirements.txt
```

## 🔐 Configuración (Archivo `.env`)

> ⚠️ **ADVERTENCIA IMPORTANTE DE SEGURIDAD:** 
> - **NUNCA** debes subir tu archivo `.env` a GitHub ni compartirlo públicamente.
> - El token funciona como la contraseña de tu bot.
> - Si crees que tu token ha sido expuesto, ve a BotFather y usa el comando `/revoke` para invalidarlo inmediatamente.

Para configurar tu proyecto localmente:

1. Duplica el archivo `.env.example` y nómbralo `.env`:
   - **En Windows PowerShell:** `Copy-Item .env.example .env`
   - **En Linux / Git Bash:** `cp .env.example .env`

2. Abre el archivo `.env` y rellena las variables:
   - `TELEGRAM_BOT_TOKEN`: La credencial que autoriza a tu código a usar el bot.
   - `TELEGRAM_CHAT_ID`: El identificador de la conversación (usuario o grupo) donde llegarán los mensajes.
   - `ALERT_COOLDOWN_SECONDS`: Tiempo en segundos (por defecto 60) que debe pasar antes de volver a enviar una alerta idéntica (para evitar spam).

### 🤖 ¿Cómo obtener el TELEGRAM_BOT_TOKEN?
1. Abre Telegram y busca a **@BotFather**.
2. Escríbele `/newbot` y sigue las instrucciones para darle un nombre y un nombre de usuario.
3. Al finalizar, BotFather te dará un Token (se ve parecido a esto: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`).
4. Cópialo y pégalo en tu archivo `.env`.

### 🔍 ¿Cómo obtener el TELEGRAM_CHAT_ID?
El Chat ID le dice al bot a quién enviarle el mensaje (puede ser a ti directamente o a un grupo de alertas como "SmartH2OAlerts").

1. Abre Telegram y búscate a ti mismo, o crea un grupo y añade a tu bot.
2. **Escríbele un mensaje al bot** en ese chat (ej. "hola"). Esto es obligatorio para que Telegram registre el chat.
3. En tu terminal, ejecuta este comando:

**Windows PowerShell / Linux / Git Bash:**
```bash
python src/get_chat_id.py
```
> **Nota sobre Grupos:** Si agregaste el bot a un grupo, el `chat_id` normalmente empezará con un signo negativo (ej: `-100123456789`). Esto es una convención normal de Telegram para identificar a los supergrupos. Cópialo completo con el guion incluido.

## 🧪 Probar el funcionamiento

Una vez configurado tu archivo `.env`, puedes ejecutar la prueba:

**Windows PowerShell / Linux / Git Bash:**
```bash
python src/test_bot.py
```

El script enviará una alerta de prueba y luego intentará enviar otra idéntica para verificar que el sistema de anti-spam (cooldown) funcione correctamente y omita el segundo mensaje.

## 🛠️ Errores comunes y soluciones

- **`TELEGRAM_BOT_TOKEN no está configurado`**: Significa que no creaste el archivo `.env` o el nombre de la variable no coincide con el del `.env.example`.
- **`Error devuelto por Telegram: Bad Request: chat not found`**: El bot no encuentra el CHAT_ID. Asegúrate de haberle mandado un mensaje al bot en el chat correspondiente primero.
- **`Error devuelto por Telegram: Unauthorized` (Error 401)**: Tu Token es incorrecto, está incompleto en el `.env`, o ha sido revocado.
- **`Error devuelto por Telegram: Bad Request` (Error 400)**: Generalmente ocurre si intentas enviar un mensaje con HTML mal formado. El código ya previene esto usando `html.escape`.
- **`Result vacío en getUpdates`**: Al ejecutar `get_chat_id.py` el resultado está vacío. Esto ocurre porque el bot no ha recibido ningún mensaje reciente. Simplemente envíale "hola" al bot y vuelve a ejecutar el script.

## 📸 Evidencia de funcionamiento

*(Aquí puedes anexar una captura de pantalla del mensaje enviado al grupo de Telegram mostrando el formato con el emoji, título, descripción y hora. Asegúrate siempre de ocultar cualquier fragmento de tu token si aparece en la pantalla).*
