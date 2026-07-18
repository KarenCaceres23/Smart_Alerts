# Análisis del Escenario Hídrico - SmartH2O

## 1. Alcance y limitaciones de la Fase 2

Este documento corresponde a la Fase 2 de Integración.
**Limitaciones actuales:** Solo incluye la definición estática de reglas, parámetros, plantillas y lógica anti-spam (debounce). La consulta real de datos históricos, la conexión con InfluxDB y la automatización (Fase 3) no están contempladas aquí.

## 2. Objetivo del análisis

Definir los puntos de monitoreo, las variables principales y la lógica conceptual para detectar comportamientos anómalos en el consumo de agua, preparando el camino para el motor de reglas de alertas (Smart_Alerts).

## 3. Puntos de monitoreo

| ID del sensor | Zona   | Punto de medición                  | Horario operativo típico        |
| ------------- | ------ | ---------------------------------- | ------------------------------- |
| SH2O-ZA-001   | Zona A | Sanitarios piso 1                  | 07:00 - 19:00 (L-V)             |
| SH2O-ZB-001   | Zona B | Cocina / comedor institucional     | 11:00 - 16:00 (L-V)             |
| SH2O-ZC-001   | Zona C | Áreas verdes / riego exterior      | 20:00 - 22:00 (L-D)             |
| SH2O-ZD-001   | Zona D | Cuarto de mantenimiento / cisterna | 24 horas                        |
| SH2O-ZE-001   | Zona E | Sanitarios piso 2                  | 08:00 - 18:00 (L-V)             |

## 4. Variables observadas

| Nombre técnico      | Unidad | Tipo de dato    | Uso dentro del sistema                                        |
| ------------------- | ------ | --------------- | ------------------------------------------------------------- |
| `sensor_id`         | N/A    | String          | Identifica el punto de medición que envía la lectura.         |
| `timestamp`         | ISO    | DateTime        | Registra cuándo ocurrió la medición.                          |
| `flow_rate`         | L/min  | Float           | Permite detectar consumo alto, flujo continuo o posible fuga. |
| `cumulative_volume` | L      | Float           | Permite conocer el consumo total diario por zona.             |
| `status`            | N/A    | Enum/String     | Indica la condición del sensor (normal/offline).              |
| `zone` / `location` | N/A    | String/Object   | Relaciona la lectura con una zona física.                     |

## 5. Necesidades de alertamiento (Reglas R01-R04)

Las anomalías se agrupan en las siguientes reglas conceptuales. Debido a la variedad de zonas, existe una **necesidad estricta de usar umbrales configurables** para cada regla, en lugar de valores duros (hardcoded).

*   **R01:** Flujo por encima del límite crítico de la zona (ej. > 20 L/min).
*   **R02:** Flujo detectado fuera del horario operativo de la zona (ej. caudal de noche).
*   **R03:** Sensor fuera de línea (sin datos recientes).
*   **R04:** Consumo acumulado diario superando el límite planificado.

## 6. Severidades

El sistema utiliza niveles normalizados (`INFO`, `WARNING`, `CRITICAL`) de acuerdo con la política general documentada en `mecanismo_deteccion_alertas.md`. Las notificaciones se enviarán mediante el Bot de Telegram de SmartH2O.
