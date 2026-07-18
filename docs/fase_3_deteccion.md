# Fase 3: Detección Automática de Anomalías

## Arquitectura Limpia y Desacoplada
Para esta fase, el repositorio se ha estructurado separando las responsabilidades de captura de datos, evaluación y notificación:
1. **Modelos (`models.py`)**: Define `SensorReading` y `SensorConfig` como estructuras inmutables.
2. **Reglas (`rules.py`)**: Lógica pura para evaluar R01-R04. Sin estado.
3. **Detector (`detector.py`)**: Maneja la persistencia en memoria (usando diccionarios con timestamps). Convierte los resultados de las reglas en instancias de `Alert`.
4. **Infraestructura (`influx_client.py` y `telegram_bot.py`)**:
    - `InfluxSensorRepository` obtiene datos.
    - `TelegramBot` envía datos y hace debounce.
5. **Orquestador (`main.py`)**: Ejecuta el ciclo coordinando las capas.

## Base de Datos y Motor de Reglas (Decisión Arquitectónica)
> [!IMPORTANT]
> Se ha confirmado que en el sistema final productivo, **la base de datos definitiva será InfluxDB y las reglas de negocio residirán en Grafana Alerting**. Este módulo detector en Python sirve para probar, simular y validar las condiciones como parte del rol de Integración Jr, demostrando que la lógica y notificaciones de Telegram operan correctamente bajo esas reglas.

## Persistencia vs Cooldown
- **Persistencia**: La regla no se activa hasta que ha estado sostenida durante X segundos. El `Detector` lleva este registro de cuándo se detectó por primera vez.
- **Cooldown (Debounce)**: Una vez que el `Detector` emite el `Alert`, el `TelegramBot` lo recibe, lo envía y entra en *cooldown* de Y segundos para no hacer spam, incluso si el Detector sigue emitiendo el `Alert`.

## Pruebas
Todas las pruebas están implementadas en la suite `tests/` utilizando `pytest` y validando persistencia, horarios cruzados de medianoche y umbrales sin conectarse a la API de InfluxDB o Telegram.
