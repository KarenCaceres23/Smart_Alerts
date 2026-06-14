# SmartH2O Telegram Bot

Este repositorio contiene el módulo de notificaciones por Telegram para el proyecto académico **SmartH2O**. Su función principal es enviar alertas de texto formateadas a un grupo o usuario de Telegram cuando el sistema detecta un evento relevante.

## Descripción general

El módulo se conecta con la API de Telegram para automatizar el envío de avisos del sistema. Entre sus principales características se incluyen:

* Envío de mensajes en formato HTML.
* Alertas con nivel de severidad y hora de envío.
* Uso de variables de entorno para proteger credenciales sensibles.
* Archivo `.env.example` como plantilla de configuración.
* Protección anti-spam mediante cooldown para evitar alertas repetidas.
* Script auxiliar para obtener el `TELEGRAM_CHAT_ID`.
* Script de prueba para validar el funcionamiento del bot.

## Instalación

Para preparar el entorno de ejecución, asegúrate de estar dentro de la carpeta del proyecto e instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

En Linux, si estás usando entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración del entorno

Para que el bot funcione, es necesario crear un archivo `.env` basado en el archivo `.env.example`.

```bash
cp .env.example .env
```

Dentro del archivo `.env` se deben configurar las siguientes variables:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
ALERT_COOLDOWN_SECONDS=60
```

### Variables utilizadas

* `TELEGRAM_BOT_TOKEN`: token generado por BotFather al crear el bot de Telegram.
* `TELEGRAM_CHAT_ID`: identificador numérico del chat o grupo donde se enviarán las alertas.
* `ALERT_COOLDOWN_SECONDS`: tiempo de espera, en segundos, antes de permitir nuevamente una alerta repetida.

## Seguridad

El archivo `.env` contiene credenciales sensibles y no debe subirse a GitHub.

Reglas importantes:

* No compartir el token del bot públicamente.
* No colocar credenciales directamente en el código fuente.
* No subir el archivo `.env` al repositorio.
* Si el token se expone por error, se debe revocar desde BotFather usando el comando `/revoke`.

## Obtener el TELEGRAM_CHAT_ID

Si no conoces el `TELEGRAM_CHAT_ID`, primero debes enviar un mensaje al bot o al grupo donde está agregado.

Luego ejecuta:

```bash
python src/get_chat_id.py
```

El script mostrará el ID del chat en la terminal. En grupos o supergrupos, el ID puede iniciar con `-100`.

## Prueba del bot

Cuando el archivo `.env` ya esté configurado, ejecuta:

```bash
python src/test_bot.py
```

El script enviará una alerta de prueba a Telegram y luego intentará enviar una segunda alerta idéntica para validar el sistema anti-spam.

La primera alerta debe enviarse correctamente.
La segunda alerta debe ser omitida por cooldown.

## Problemas comunes

### Error 401 Unauthorized

El token del bot está mal escrito, fue revocado o no corresponde al bot configurado. Revisa el archivo `.env`.

### Chat not found

El bot no encuentra el chat configurado. Verifica que el `TELEGRAM_CHAT_ID` sea correcto y que el bot esté agregado al grupo.

### getUpdates devuelve vacío

Telegram no tiene mensajes recientes registrados para el bot. Envía un mensaje al bot o al grupo y vuelve a ejecutar:

```bash
python src/get_chat_id.py
```

## Evidencia de funcionamiento

Durante las pruebas se verificó que:

* El bot envía mensajes correctamente al grupo configurado.
* Las credenciales se leen desde el archivo `.env`.
* El archivo `.env` permanece ignorado por Git.
* El sistema anti-spam evita el envío repetido de una misma alerta dentro del tiempo de cooldown configurado.

## Estado del módulo

El módulo de notificaciones por Telegram queda preparado como base para futuras integraciones con reglas de detección, sensores, dashboards o servicios de alertamiento del proyecto SmartH2O.
