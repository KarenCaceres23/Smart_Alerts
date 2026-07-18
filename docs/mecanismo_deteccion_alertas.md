# Mecanismo de Detección de Anomalías y Alertas

## 1. Alcance de la Fase 2

Este documento define el mecanismo de detección conceptual y la estructura de alertas de la Fase 2. Aún **no** incluye la integración con InfluxDB, las consultas Flux, Grafana Alerting ni la ejecución programada automática (estas pertenecen a la Fase 3).

## 2. Flujo conceptual de detección

1. El sensor o simulador IoT genera lecturas de consumo de agua.
2. Los datos son enviados mediante MQTT o REST hacia el servicio de ingestión.
3. El servicio valida y almacena los datos en InfluxDB.
4. El detector (futura Fase 3) consulta InfluxDB evaluando ventanas de tiempo.
5. Se comparan las lecturas con los umbrales de las reglas.
6. Si se cumple una condición, se instancia una `Alert`.
7. El sistema verifica el *debounce* (cooldown). Si no está suprimida, envía la alerta a Telegram.

## 3. Estructura de una Alerta

Toda anomalía detectada se encapsula en una estructura inmutable (`dataclass Alert`) que contiene:
- `rule_id`: (R01, R02, etc.)
- `sensor_id`: Identificador único del sensor.
- `zone`: Ubicación (ej. Cocina, Sanitarios).
- `value`: Lectura actual.
- `threshold`: Valor de referencia superado.
- `severity`: Severidad del evento.
- `description`: Contexto del evento.
- `recommended_action`: Acción sugerida.

### Severidades
Solo existen tres niveles de severidad (`Enum Severity`):
- `INFO` (ℹ️): Informativo o eventos de conectividad.
- `WARNING` (⚠️): Advertencias, consumo irregular o fuera de horario.
- `CRITICAL` (🚨): Fallas críticas, flujos excesivos o posibles fugas mayores.

## 4. Reglas de detección detalladas

### R01: Caudal crítico por sensor/zona
- **Objetivo:** Detectar fugas mayores o consumo excesivo continuo.
- **Condición:** `flow_rate` > umbral crítico configurado (ej. 20 L/min).
- **Persistencia:** Durante más de 10 minutos seguidos.
- **Severidad:** `CRITICAL`
- **Acción recomendada:** Revisar tuberías, válvulas y buscar posibles fugas.
- **Criterio de resolución:** Caudal vuelve por debajo del umbral durante al menos 5 minutos.

### R02: Flujo fuera del horario operativo
- **Objetivo:** Identificar usos de agua nocturnos o en fines de semana.
- **Condición:** `flow_rate` > umbral mínimo (ej. 5 L/min) fuera de horario.
- **Persistencia:** Al menos 5 minutos.
- **Severidad:** `WARNING`
- **Acción recomendada:** Verificar llaves abiertas o personal fuera de horario.
- **Criterio de resolución:** Caudal vuelve a cero.

### R03: Sensor sin comunicación
- **Objetivo:** Monitorear el estado de salud (healthcheck) de la red IoT.
- **Condición:** Ausencia total de datos del sensor.
- **Persistencia:** Más de 10 minutos sin registros.
- **Severidad:** `INFO` (o `WARNING`).
- **Acción recomendada:** Revisar alimentación eléctrica, red, broker MQTT.
- **Criterio de resolución:** Recepción de un nuevo dato válido.

### R04: Consumo diario excesivo
- **Objetivo:** Evitar sobrepasar la capacidad o presupuesto hídrico.
- **Condición:** `cumulative_volume` > consumo esperado diario.
- **Persistencia:** N/A (Se dispara en cuanto se supera).
- **Severidad:** `CRITICAL`
- **Acción recomendada:** Realizar auditoría de consumo en la zona afectada.
- **Criterio de resolución:** Inicio de un nuevo día (reinicio del acumulado).

## 5. Política de Debounce (Cooldown)

Para evitar saturar de notificaciones (spam) a los usuarios cuando un sensor oscila sobre el umbral:
- Se implementa un registro en memoria de las alertas enviadas exitosamente.
- La clave del cooldown es la combinación exacta de `(sensor_id, rule_id)`. **No** depende del valor ni la descripción.
- Si una alerta para ese sensor y regla se envió en los últimos `ALERT_COOLDOWN_SECONDS` (ej. 300s = 5 min), el estado de envío será `SUPPRESSED`.
- Si el envío HTTP falla, **no** se registra el cooldown, para reintentarlo en el próximo ciclo.

## 6. Parámetros configurables y seguridad de credenciales

El sistema utiliza variables de entorno (archivo `.env`) para evitar el registro accidental (hardcoding) de información sensible en GitHub:
- `TELEGRAM_BOT_TOKEN`: Token otorgado por BotFather.
- `TELEGRAM_CHAT_ID`: ID del chat de destino.
- `ALERT_COOLDOWN_SECONDS`: (Opcional, por defecto 300) Tiempo en segundos para el debounce.

El archivo `.env` está en `.gitignore` para máxima seguridad.

## 7. Plantillas de Telegram

El bot procesa la estructura `Alert` y genera un mensaje HTML. Ejemplo:

```text
🚨 ALERTA CRÍTICA – SmartH2O

Regla: R01
Sensor: SH2O-ZA-001
Zona: Sanitarios piso 1
Valor detectado: 22.50 L/min
Umbral: 20.00 L/min

Descripción:
Caudal superior al límite permitido.

Acción recomendada:
Revisar el punto de medición y validar posible fuga.

Fecha: 2026-06-18 10:30:00
```
