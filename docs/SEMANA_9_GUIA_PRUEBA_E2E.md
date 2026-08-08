# Guía de Prueba End-to-End (E2E) - Semana 9

Esta guía detalla los pasos para validar el flujo completo de alertas desde InfluxDB hasta Telegram, pasando por el Detector de Smart_Alerts.

## 1. Requisitos Previos
- Acceso de lectura al bucket `telemetria_agua` en InfluxDB.
- Un bot de Telegram creado y un chat (grupo o usuario) donde el bot tenga permisos de escritura.
- Python 3.10+ y dependencias instaladas (`pip install -r requirements.txt`).

## 2. Variables de Entorno Necesarias
Asegúrate de configurar el archivo `.env` en la raíz del proyecto. **Nunca utilices tokens reales en repositorios públicos o commits.**

```env
INFLUXDB_URL=http://tu-servidor-influx:8086
INFLUXDB_TOKEN=tu_token_solo_en_local
INFLUXDB_ORG=tu_org
INFLUXDB_BUCKET=telemetria_agua
INFLUXDB_MEASUREMENT=consumo_agua
INFLUXDB_FLOW_FIELD=flow_rate
INFLUXDB_VOLUME_FIELD=cumulative_volume

TELEGRAM_BOT_TOKEN=tu_token_de_telegram_solo_en_local
TELEGRAM_CHAT_ID=tu_chat_id_solo_en_local
```

## 3. Verificación de Conexión a InfluxDB
Antes de correr el sistema, verifica que el host de InfluxDB responda haciendo un `curl` o usando la interfaz web de InfluxDB con las credenciales provistas.

## 4. Verificación de Lectura de los Sensores
Revisa manualmente (mediante InfluxDB Data Explorer) que existan datos recientes para los sensores soportados:
- `AARD-EDIF-A-CIST`
- `AARD-EDIF-A-COCINA`
- `AARD-EDIF-A-RIEGO`
- `AARD-EDIF-A-SAN1`
- `AARD-EDIF-A-SAN2`

## 5. Ejecución de Smart_Alerts
Para ejecutar un ciclo de detección, lanza el módulo principal:
```bash
python -m src.main
```
Observa la salida de consola para verificar cuántos sensores fueron procesados.

## 6. Cómo Provocar o Seleccionar una Lectura Anómala
**De forma controlada (en pruebas):**
- Inyectar manualmente un dato en InfluxDB para uno de los sensores (por ejemplo, `AARD-EDIF-A-SAN1`) con un `flow_rate` de `25.0` (superando el umbral crítico provisional de `20.0`).

## 7. Cómo Comprobar que Detector Identifica la Anomalía
- Revisa los logs de consola al ejecutar `python -m src.main`. El sistema debe indicar que se detectó una anomalía y que el estado cambió a `DETECTED` o `PENDING_DEBOUNCE`.
- Si el umbral se supera por más tiempo que el `ALERT_DEBOUNCE_SECONDS`, se generará la alerta.

## 8. Cómo Confirmar la Alerta en Telegram
- Abre la aplicación de Telegram y verifica el chat correspondiente al `TELEGRAM_CHAT_ID`.
- Deberá aparecer un mensaje formateado en HTML con iconos de alerta y detalles del sensor, zona y valor que disparó la regla.

## 9. Qué Hacer si No Llega la Alerta
- Verifica la conectividad de red hacia `api.telegram.org`.
- Revisa si la alerta fue suprimida por la política Anti-Spam (Cooldown). El log indicará `SUPPRESSED`.
- Revisa si la alerta fue suprimida por Debounce (el tiempo de anomalía no superó los segundos requeridos).
- Confirma que el Token y Chat ID en el archivo `.env` son correctos.

## 10. Qué Logs Revisar
- **Consola:** Logs de ejecución en tiempo real (`INFO`, `DEBUG`, `ERROR`).
- **Audit Log:** Revisa el archivo `audit.jsonl` generado por el sistema. Debe contener eventos estructurados detallando el ciclo de vida de la detección (`SENT`, `SUPPRESSED`, etc.).

## 11. Criterios de Éxito
- El sistema se conecta a InfluxDB exitosamente.
- Lee los datos reales.
- El Detector evalúa basándose en umbrales correctos.
- La alerta llega a Telegram con formato válido y sin retrasos injustificados.
- El evento queda registrado en `audit.jsonl`.

## 12. Criterios de Fallo
- Errores de conexión no manejados (Crash de la aplicación).
- Falsos positivos por lecturas que no superan umbrales.
- Filtración de tokens o credenciales en los logs o errores expuestos.
- Telegram bloquea el bot (Ej. HTTP 429 persistente sin backoff).
