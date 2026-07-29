# SmartH2O Telegram Bot & Alertas

Módulo de alertas para el proyecto académico **SmartH2O**, diseñado con arquitectura escalable, pruebas unitarias y manejo robusto de notificaciones hacia Telegram.

## Estado de la Arquitectura

| Componente | Diseñado | Implementado | Probado |
|------------|----------|-------------|---------|
| Notificador Telegram | Sí | Sí | Sí (Mocks) |
| Cooldown en Memoria | Sí | Sí | Sí |
| Reglas de Detección (R01-R04) | Sí | Sí (Básico) | Sí |
| Cliente InfluxDB | Sí | No (Simulado) | No |
| Almacenamiento Cooldown Distribuido (Redis) | Sí | No | No |

*Estado actual: El proyecto cuenta con lógica de detección, notificación, debounce, cooldown, reintentos, auditoría y pruebas automatizadas. Las integraciones reales con InfluxDB, Telegram y almacenamiento persistente requieren validación adicional en infraestructura real.*

## Requisitos y Configuración

1. Instalar Python 3.10+ y dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Configurar variables de entorno copiando `.env.example` a `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_id
   TELEGRAM_TIMEOUT_SECONDS=10
   TELEGRAM_MAX_RETRIES=3
   TELEGRAM_BACKOFF_SECONDS=2
   ALERT_COOLDOWN_SECONDS=300
   APP_TIMEZONE=America/El_Salvador
   ```

## Ejecución y Pruebas

### Uso manual
Para obtener tu Chat ID de forma segura:
```bash
python src/get_chat_id.py
```

Para correr una ronda de detección simulada:
```bash
python -m src.main
```

### Automatización (Pruebas)
Para ejecutar la batería completa de pruebas unitarias garantizando que el sistema cumple los requisitos (incluyendo timeout, backoff 429, validaciones de severidad y cooldown en memoria):
```bash
pytest tests/unit -v
```
También puedes correr los linters:
```bash
black --check src tests
ruff check src tests
```

## Arquitectura

El núcleo está contenido en `src/smart_alerts/`:
- **config.py:** Validación estricta y segura de entorno.
- **models.py:** Estructuras inmutables (`Alert`, `Severity`).
- **cooldown/:** Abstracción de estado anti-spam. Actualmente usa memoria con `time.monotonic()` y recolección de basura.
- **notifier/:** Cliente HTTP robusto con backoff y reintentos.
- **detector.py y rules.py:** Evaluación modular de umbrales.

Para retrocompatibilidad, existe el wrapper en `src/telegram_bot.py` que permite usar `send_telegram_alert(...)` desde scripts legacy.

## Mecanismos de Prevención de Spam y Reintentos

### Debounce vs Cooldown
- **Debounce (Supresión Temprana):** Se evalúa *antes* de crear la alerta. El `Detector` mide por cuánto tiempo consecutivo (`time_active`) una anomalía está presente usando una variable global `ALERT_DEBOUNCE_SECONDS`. Si la anomalía parpadea (varía repetidamente por arriba y por debajo del umbral en poco tiempo), el debounce evita que se envíen múltiples alertas. Una vez superado el umbral temporal, la alerta se pasa al Notificador.
- **Cooldown (Período de Silencio):** Se evalúa *antes* de enviar una alerta a Telegram. Una vez que se envía con éxito una alerta específica (identificada de forma estable por la regla y el sensor), el `CooldownManager` la bloquea durante `ALERT_COOLDOWN_SECONDS` minutos. El cooldown solo se consume cuando la alerta es despachada exitosamente (ok=True).

### Política de Reintentos (Retries) y Tratamiento de Errores
El sistema está diseñado para manejar incidencias de red respetando las políticas de la API:
- **Errores Recuperables:** Fallos de conexión (`ConnectionError`), agotamiento de tiempo de espera (`Timeout`) y errores genéricos (`HTTP 500`). Estos se reintentan hasta un máximo de `TELEGRAM_MAX_RETRIES` veces, esperando `TELEGRAM_BACKOFF_SECONDS` entre cada intento.
- **Límite de Tasa (HTTP 429 - Too Many Requests):** Cuando Telegram solicita frenar, el notificador suspende el hilo inmediatamente leyendo el cabezal `retry_after`. Los reintentos por 429 *no* consumen el presupuesto de `TELEGRAM_MAX_RETRIES`.
- **Errores Definitivos:** Errores de cliente (HTTP 400, 401, 403, 404) y respuestas ilógicas (`ok: False` sin razón recuperable) detienen inmediatamente el envío sin reintentar ni consumir el cooldown.

### Registro de Auditoría (Audit Log)
El sistema guarda un log estructurado (JSONL) en `AUDIT_LOG_PATH` documentando todos los cambios de estado en la máquina de auditoría:
- `DETECTED`: Anomalía vista por primera vez, inicio del Debounce.
- `PENDING_DEBOUNCE`: La anomalía sigue presente pero aún no supera `ALERT_DEBOUNCE_SECONDS`.
- `RESOLVED`: La anomalía regresó a la normalidad.
- `SENT`: Alerta enviada con éxito.
- `RETRYING`: Intento fallido pero recuperable.
- `FAILED`: Intento fallido permanente o límite de intentos superado.
- `SUPPRESSED`: Suprimido por la política de Cooldown.
El log no contiene tokens ni datos sensibles.

## Limitaciones actuales

El proyecto se encuentra en una etapa de validación técnica y todavía presenta las siguientes limitaciones:

- La integración con InfluxDB se encuentra preparada y probada mediante simulaciones, pero requiere validación con una instancia real y datos reales.
- El almacenamiento de cooldown y debounce utiliza memoria local, por lo que su estado se pierde al reiniciar la aplicación.
- El registro de auditoría se almacena localmente en formato JSONL y todavía no cuenta con persistencia centralizada.
- Las pruebas unitarias utilizan mocks para evitar llamadas reales a Telegram y a servicios externos.
- La validación en GitHub Actions confirma el funcionamiento automatizado del código, pero no sustituye una prueba de integración completa con credenciales e infraestructura reales.
- El sistema todavía no ha sido sometido a pruebas de carga, alta concurrencia ni despliegue distribuido.
- La configuración y los umbrales de las reglas deben validarse con datos reales de los sensores antes de utilizarse en producción.

## Seguridad

- El `.env` está en `.gitignore`.
- Los logs enmascaran el `TELEGRAM_BOT_TOKEN` (si es capturado).
- `get_chat_id.py` oculta parcialmente los IDs devueltos por la API para evitar filtraciones.
