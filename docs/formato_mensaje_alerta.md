# Formato del Mensaje de Alerta

Para el envío de notificaciones a Telegram, el sistema utiliza plantillas en formato **HTML** parseado (soportado nativamente por la API de Telegram). 

## Estructura Base

Cada mensaje de alerta contiene campos dinámicos que se llenan dependiendo de la anomalía detectada. El formato exacto es el siguiente:

```html
🚨 <b>ALERTA SMART H2O</b> 🚨

<b>Sensor:</b> {sensor_id}
<b>Zona:</b> {zone}
<b>Regla Activada:</b> {rule_id}
<b>Severidad:</b> {severity_emoji} {severity}

<b>Descripción:</b>
{description}

<b>Valor Detectado:</b>
{value_str} {threshold_str}

<b>Acción Recomendada:</b>
{recommended_action}
```

## Campos Dinámicos
* **`{sensor_id}` y `{zone}`**: Identifican la ubicación exacta de la medición.
* **`{rule_id}`**: Identificador de la regla vulnerada (R01, R02, R03, R04).
* **`{severity_emoji}` y `{severity}`**: Mapeo visual y textual del nivel de criticidad (INFO ℹ️, WARNING ⚠️, CRITICAL 🔴).
* **`{value_str}`**: El valor numérico registrado en la medición, formateado a 2 decimales y acompañado de su unidad (L/min o Litros).
* **`{threshold_str}`**: El límite permitido configurado para la zona, mostrado como contexto.
* **`{description}` y `{recommended_action}`**: Mensajes de negocio en español para guiar la respuesta del personal de mantenimiento.

## Consideraciones Técnicas
Para evitar inyecciones HTML que rompan el formato de Telegram, el código en Python utiliza `html.escape()` sobre todos los campos de texto libre antes de renderizar la plantilla.
