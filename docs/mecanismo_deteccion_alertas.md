# Mecanismo de Detección de Anomalías y Alertas

## 1. Objetivo del documento

Este documento describe cómo el sistema SmartH2O detectará anomalías en el consumo de agua utilizando datos almacenados en InfluxDB y cómo se generarán alertas mediante un bot de Telegram o correo electrónico.

El propósito es dejar claro el flujo de integración entre los datos de sensores, la base de datos, las reglas de detección y los canales de notificación.

## 2. Flujo general del sistema

Sensor / Simulador IoT → MQTT/REST → Servicio de Ingestión → InfluxDB → Detector de reglas → Bot de Telegram / Email

Descripción del flujo:

1. El sensor o simulador IoT genera lecturas de consumo de agua.
2. Cada lectura contiene datos como `sensor_id`, `timestamp`, `flow_rate`, `cumulative_volume`, `status`, `anomaly_flag` y `location`.
3. Los datos son enviados mediante MQTT o REST hacia el servicio de ingestión.
4. El servicio de ingestión valida y almacena los datos en InfluxDB.
5. El detector consulta InfluxDB en ventanas de tiempo recientes.
6. Las lecturas se comparan con las reglas de detección.
7. Si se cumple una condición anómala, se genera una alerta.
8. La alerta se envía por Telegram o email.

## 3. Datos utilizados para la detección

| Campo | Descripción | Ejemplo |
|---|---|---|
| `sensor_id` | Identificador único del sensor | SH2O-ZA-001 |
| `timestamp` | Fecha y hora de la lectura | 2026-06-18T10:30:00Z |
| `flow_rate` | Caudal instantáneo en litros por minuto | 22.5 |
| `cumulative_volume` | Volumen acumulado del día en litros | 850.0 |
| `status` | Estado del sensor o lectura | normal, warning, critical, offline |
| `anomaly_flag` | Indica si la lectura es anómala | true o false |
| `location` | Ubicación del punto de medición | Edificio, piso, zona |

## 4. Reglas de detección propuestas

| Regla | Condición | Severidad | Canal de notificación | Descripción |
|---|---|---|---|---|
| R01 | `flow_rate` > 20 L/min durante más de 10 minutos | critical | Telegram | Posible fuga o consumo excesivo sostenido. |
| R02 | `flow_rate` > 5 L/min en horario nocturno | warning | Telegram | Consumo fuera del horario esperado. |
| R03 | Sensor sin datos por más de 10 minutos | warning | Telegram/email | Posible desconexión o falla del sensor. |
| R04 | `cumulative_volume` supera el consumo esperado diario | critical | Telegram/email | Consumo acumulado anormal para la zona. |

## 5. Consulta de datos desde InfluxDB

El detector consultará InfluxDB para obtener las lecturas recientes de cada sensor.

La consulta se realizará usando:
- `sensor_id`
- ventana de tiempo reciente, por ejemplo últimos 5 o 10 minutos
- variable monitoreada, como `flow_rate` o `cumulative_volume`
- ubicación del sensor

El objetivo es determinar si el comportamiento del consumo de agua se mantiene dentro de los rangos esperados o si cumple una regla de anomalía.

## 6. Funcionamiento del bot de alertas

El bot será el canal encargado de notificar al equipo cuando se detecte una anomalía.

Cada mensaje de alerta debería incluir:
- ID del sensor.
- Zona afectada.
- Regla activada.
- Valor detectado.
- Severidad.
- Hora del evento.
- Acción sugerida.

Ejemplo de mensaje:

```text
🚨 Alerta crítica SmartH2O

Sensor: SH2O-ZA-001  
Zona: Sanitarios piso 1  
Regla activada: R01 - Posible fuga  
Caudal detectado: 22.5 L/min  
Severidad: critical  
Hora: 2026-06-18 10:30  

Acción sugerida: revisar el punto de medición y validar posible fuga.
```

## 7. Política de cooldown

Para evitar el envío repetido de alertas del mismo sensor, se propone aplicar un tiempo de espera entre notificaciones.

Variable sugerida:

`ALERT_COOLDOWN_SECONDS = 300`

Esto equivale a 5 minutos.

La alerta no se volverá a enviar para el mismo sensor y la misma regla hasta que pase ese tiempo.

## 8. Pendientes de validación

- Confirmar si la conexión será mediante MQTT o REST.
- Confirmar si InfluxDB será la base de datos definitiva.
- Validar los umbrales con el equipo.
- Confirmar si el canal principal de alertas será Telegram, email o ambos.
- Coordinar con la persona encargada de InfluxDB para definir cómo se harán las consultas.
- Confirmar si las reglas estarán en código, Grafana Alerting o en otro módulo detector.
