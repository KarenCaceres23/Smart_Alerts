# Análisis del Escenario Hídrico - SmartH2O

## 1. Objetivo del análisis

Este documento define los puntos de monitoreo, las variables principales y los umbrales iniciales del sistema SmartH2O.

El propósito es dejar clara la base técnica para detectar comportamientos anómalos en el consumo de agua y facilitar la integración con InfluxDB, el detector de reglas y el bot de alertas.

SmartH2O se enfoca en el monitoreo inteligente del consumo hídrico, por lo tanto este análisis se centra en caudal, volumen acumulado, estado del sensor, ubicación y posibles fugas.

---

## 2. Puntos de monitoreo e integración

| ID del sensor | Zona   | Punto de medición                  | Datos enviados                                             | Sistema que recibe el dato | Observación de integración                                    |
| ------------- | ------ | ---------------------------------- | ---------------------------------------------------------- | -------------------------- | ------------------------------------------------------------- |
| SH2O-ZA-001   | Zona A | Sanitarios piso 1                  | `flow_rate`, `cumulative_volume`, `status`                 | InfluxDB                   | Alto consumo durante horario laboral.                         |
| SH2O-ZB-001   | Zona B | Cocina / comedor institucional     | `flow_rate`, `cumulative_volume`, `status`                 | InfluxDB                   | Consumo alto en horarios de comida o limpieza.                |
| SH2O-ZC-001   | Zona C | Áreas verdes / riego exterior      | `flow_rate`, `cumulative_volume`, `status`                 | InfluxDB                   | Se debe detectar consumo fuera del horario de riego.          |
| SH2O-ZD-001   | Zona D | Cuarto de mantenimiento / cisterna | `flow_rate`, `cumulative_volume`, `status`, `anomaly_flag` | InfluxDB                   | Punto crítico para detectar fugas, rebalses o flujo continuo. |
| SH2O-ZE-001   | Zona E | Sanitarios piso 2                  | `flow_rate`, `cumulative_volume`, `status`                 | InfluxDB                   | Bajo consumo esperado, especialmente en horario nocturno.     |

---

## 3. Variables a monitorear

| Nombre visible           | Nombre técnico      | Unidad                          | Tipo de dato    | Uso dentro del sistema                                        |
| ------------------------ | ------------------- | ------------------------------- | --------------- | ------------------------------------------------------------- |
| Identificador del sensor | `sensor_id`         | N/A                             | String          | Identifica el punto de medición que envía la lectura.         |
| Fecha y hora             | `timestamp`         | ISO 8601                        | DateTime/String | Registra cuándo ocurrió la medición.                          |
| Caudal instantáneo       | `flow_rate`         | L/min                           | Float           | Permite detectar consumo alto, flujo continuo o posible fuga. |
| Volumen acumulado        | `cumulative_volume` | L                               | Float           | Permite conocer el consumo total diario por zona.             |
| Estado del sensor        | `status`            | normal/warning/critical/offline | Enum/String     | Indica la condición general del sensor o de la lectura.       |
| Bandera de anomalía      | `anomaly_flag`      | true/false                      | Boolean         | Marca si la lectura presenta comportamiento anómalo.          |
| Ubicación                | `location`          | building/floor/zone             | Object          | Relaciona la lectura con edificio, piso y zona.               |

---

## 4. Flujo de integración de datos

El sistema SmartH2O recibe lecturas generadas por sensores o por un simulador IoT. Cada lectura representa el consumo de agua en un punto de monitoreo.

Flujo general:

```txt
Sensor / Simulador IoT → MQTT/REST → Servicio de Ingestión → InfluxDB → Detector de reglas → Bot de Telegram / Email
```

Descripción del flujo:

1. El sensor o simulador genera una lectura de consumo de agua.
2. La lectura incluye `sensor_id`, `timestamp`, `flow_rate`, `cumulative_volume`, `status`, `anomaly_flag` y `location`.
3. El dato se envía mediante MQTT o REST hacia el servicio de ingestión.
4. El servicio valida la estructura del mensaje.
5. La lectura se almacena en InfluxDB como serie temporal.
6. El detector consulta los datos recientes.
7. Las lecturas se comparan con umbrales normales y anómalos.
8. Si se detecta una condición anómala, se genera una alerta por Telegram o email.

---

## 5. Umbrales de comportamiento normal y anómalo

| Zona                     | Comportamiento normal              | Advertencia                          | Crítico / Anomalía                         | Posible causa                         |
| ------------------------ | ---------------------------------- | ------------------------------------ | ------------------------------------------ | ------------------------------------- |
| Sanitarios piso 1        | 0–15 L/min en horario laboral      | Más de 15 L/min por más de 5 minutos | Más de 20 L/min por más de 10 minutos      | Posible fuga o uso excesivo.          |
| Cocina / comedor         | 0–18 L/min en horarios de comida   | Más de 18 L/min por más de 5 minutos | Más de 25 L/min por más de 10 minutos      | Consumo anormal o llave abierta.      |
| Riego exterior           | Consumo solo en horario programado | Consumo fuera del horario esperado   | Caudal nocturno mayor a 5 L/min            | Riego activo fuera de horario o fuga. |
| Cisterna / mantenimiento | Flujo variable según demanda       | Flujo continuo por más de 10 minutos | Flujo alto sostenido por más de 15 minutos | Posible fuga, rebalse o falla.        |
| Sanitarios piso 2        | 0–10 L/min en horario laboral      | Más de 10 L/min por más de 5 minutos | Caudal nocturno mayor a 5 L/min            | Consumo fuera de patrón o fuga.       |

---

## 6. Reglas iniciales de anomalía

| Regla | Condición                                             | Severidad | Canal de notificación | Descripción                                |
| ----- | ----------------------------------------------------- | --------- | --------------------- | ------------------------------------------ |
| R01   | `flow_rate` > 20 L/min durante más de 10 minutos      | critical  | Telegram              | Posible fuga o consumo excesivo sostenido. |
| R02   | `flow_rate` > 5 L/min en horario nocturno             | warning   | Telegram              | Consumo fuera del horario esperado.        |
| R03   | Sensor sin datos por más de 10 minutos                | warning   | Telegram/email        | Posible desconexión o falla del sensor.    |
| R04   | `cumulative_volume` supera el consumo esperado diario | critical  | Telegram/email        | Consumo acumulado anormal para la zona.    |

---

## 7. Decisión técnica D01

**Decisión:** Uso de InfluxDB para almacenar métricas de consumo de agua.

**Justificación:**
Las lecturas de SmartH2O son datos asociados al tiempo, como caudal instantáneo, volumen acumulado y estado del sensor. InfluxDB es adecuada para almacenar series temporales, consultar datos recientes y facilitar la detección de anomalías por ventanas de tiempo.

**Impacto en la integración:**

* Cada lectura debe enviarse con una estructura consistente.
* Los datos deben incluir `sensor_id`, `timestamp`, `flow_rate`, `cumulative_volume`, `status`, `anomaly_flag` y `location`.
* El detector podrá consultar datos recientes por sensor y zona.
* La información podrá integrarse posteriormente con Grafana y alertas automáticas.

**Estado de la decisión:** Propuesta para validación del equipo.

---

## 8. Pendientes de validación con el equipo

* Confirmar si el envío de datos será mediante MQTT o REST.
* Confirmar si InfluxDB será la base de datos definitiva.
* Validar los umbrales con el equipo.
* Confirmar los horarios laborales, nocturnos y de riego.
* Definir si las alertas se enviarán por Telegram, email o ambos canales.
* Confirmar si las reglas estarán en código, Grafana Alerting o en otro módulo detector.
* Validar si la cisterna tendrá reglas más estrictas por ser un punto crítico.
