# SmartH2O Telegram Bot

En este repositorio presento el módulo de notificaciones por Telegram que desarrollé para el proyecto académico **SmartH2O**. Su función principal es enviar alertas automatizadas a un grupo o usuario cuando el sistema detecta un evento importante.

## Descripción del Desarrollo

Para este módulo, realicé la integración directa con la API de Telegram. Entre las principales características y mecanismos que implementé, destacan:

* **Estructura de Datos Robusta:** Implementé un modelo basado en la clase `Alert` (una `dataclass` inmutable), asegurando que todas las alertas contengan información estandarizada (sensor, regla, zona, valor, etc.).
* **Severidades Estandarizadas:** A través de la enumeración `Severity`, el sistema soporta exclusivamente niveles `INFO`, `WARNING` y `CRITICAL`, garantizando consistencia.
* **Estados de Envío Claros:** Utilizando la enumeración `SendStatus`, el bot devuelve estados precisos y verificables (`SENT`, `SUPPRESSED` por debounce, o `FAILED`).
* **Formato HTML:** Las alertas se envían con una estructura clara que incluye formato a 2 decimales para las lecturas (ej. `42.50 L/min`), nivel de severidad con emojis y hora exacta.
* **Seguridad de credenciales:** Configuré el uso de variables de entorno (`.env`) para no exponer los tokens en el código fuente.
* **Protección Anti-Spam (Cooldown):** Desarrollé una lógica en memoria estricta y delegada a la clase `TelegramBot` que evita enviar alertas repetidas si se detecta la misma anomalía (misma regla en el mismo sensor) dentro del tiempo de espera.
* **Scripts de soporte:** Creé un script auxiliar (`get_chat_id.py`) para facilitar la obtención del ID del grupo, y un script exhaustivo de validación (`test_bot.py`) para comprobar los diferentes casos de uso.

## Preparación del Entorno

Para poner en marcha el proyecto, es necesario instalar las dependencias que configuré. Asegúrate de estar dentro de la carpeta y ejecuta:

```bash
pip install -r requirements.txt
```

*(En Linux, si usas un entorno virtual, actívalo antes con `source .venv/bin/activate`).*

## Configuración de Credenciales

Para que el bot tenga acceso, dejé un archivo de plantilla llamado `.env.example`. Solo tienes que copiarlo y crear tu propio archivo `.env`:

```bash
cp .env.example .env
```

Dentro de tu nuevo archivo `.env`, debes llenar estos tres datos:

```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
ALERT_COOLDOWN_SECONDS=60
```

* `TELEGRAM_BOT_TOKEN`: El token que te entrega BotFather al registrar el bot.
* `TELEGRAM_CHAT_ID`: El número identificador del chat donde llegarán las alertas.
* `ALERT_COOLDOWN_SECONDS`: El tiempo en segundos que el sistema debe esperar antes de dejar pasar una alerta repetida.

### Notas de Seguridad Implementadas

Como medida de seguridad para el repositorio, apliqué las siguientes reglas:
* El archivo `.env` está configurado para ser ignorado por Git, por lo que nunca se subirá a GitHub.
* Ningún token o contraseña se coloca directamente dentro de los scripts `.py`.
* Si alguna vez el token llega a filtrarse accidentalmente, recuerda revocarlo de inmediato usando `/revoke` en BotFather.

## ¿Cómo obtener tu Chat ID?

Si no conoces tu `TELEGRAM_CHAT_ID`, asegúrate de enviarle un mensaje de prueba al bot desde tu Telegram y luego ejecuta el script que preparé:

```bash
python src/get_chat_id.py
```
*(Si lo agregaste a un grupo, es normal que el ID empiece con un signo negativo `-100...`).*

## Ejecución de Pruebas

Una vez configurado tu `.env`, puedes validar toda la integración ejecutando:

```bash
python src/test_bot.py
```

Al correrlo, notarás que la primera alerta llega correctamente a tu Telegram, pero el segundo intento es bloqueado intencionalmente por la consola para demostrar que el sistema anti-spam (cooldown) que diseñé está funcionando correctamente.

## Solución de Problemas Comunes

Si al probarlo te encuentras con algún error, revisa estos puntos:

* **Error 401 Unauthorized:** Probablemente hay un error de tipeo en el token o fue revocado. Revisa tu `.env`.
* **Chat not found:** El bot no encuentra tu chat. Asegúrate de haberle mandado un mensaje primero en Telegram para registrar la conversación.
* **getUpdates devuelve vacío:** La API de Telegram a veces limpia el historial rápido. Solo mándale otro mensaje al bot y vuelve a correr `get_chat_id.py`.
