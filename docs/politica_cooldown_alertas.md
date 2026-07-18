# Política de Cooldown (Debounce) de Alertas

El módulo de notificaciones de Telegram implementa una política estricta de *debounce* (anti-spam) conocida como **Cooldown**. 

## Objetivo
Evitar que una misma anomalía persistente (por ejemplo, una llave abierta que sigue reportando alto consumo cada segundo) inunde de mensajes el grupo de Telegram del equipo de mantenimiento, volviendo el sistema molesto e inútil.

## Configuración y Reglas del Cooldown

La configuración está centralizada en la variable de entorno `ALERT_COOLDOWN_SECONDS`, la cual por defecto está establecida en **300 segundos (5 minutos)**.

### ¿Cómo funciona la supresión?
La lógica de supresión actúa de forma independiente por cada combinación de Sensor y Regla:

1. **Clave Única:** El sistema rastrea los envíos utilizando una clave combinada: `(sensor_id, rule_id)`.
2. **Registro de Tiempo:** Cuando el Bot de Telegram envía exitosamente una alerta (código 200 de la API), registra el *timestamp* exacto (hora de envío) asociado a esa clave única en su diccionario de memoria (`self._cooldown_registry`).
3. **Bloqueo (Suppressed):** Si el Detector vuelve a solicitar el envío de una alerta para ese mismo `sensor_id` y esa misma `rule_id`, el Bot calcula el tiempo transcurrido. Si el tiempo es **menor** a `ALERT_COOLDOWN_SECONDS` (5 minutos), la alerta es silenciosamente ignorada (Estado `SUPPRESSED`).
4. **Liberación:** Una vez que superan los 5 minutos, la siguiente evaluación fallida del detector logrará pasar el filtro y se enviará una nueva notificación (Estado `SENT`).

### Ejemplo de Enrutamiento Independiente
Dado que la clave de cooldown utiliza ambos parámetros (`sensor_id` + `rule_id`):
* Si el **Sensor A** dispara la **Regla R01**, entra en cooldown para esa regla.
* Si un minuto después, el **Sensor B** dispara la **Regla R01**, el mensaje **SÍ se envía**, porque es un sensor distinto.
* Si el **Sensor A** dispara la **Regla R03**, el mensaje **SÍ se envía**, porque es una regla distinta en el mismo sensor.

Esta granularidad asegura que nunca se oculten incidentes aislados mientras se suprime el spam efectivo.
