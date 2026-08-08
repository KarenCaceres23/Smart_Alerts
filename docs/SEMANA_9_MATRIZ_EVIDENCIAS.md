# Matriz de Evidencias - Semana 9

Esta matriz detalla los casos mínimos a probar de extremo a extremo y el estado de sus evidencias.

| ID | Prueba | Objetivo | Evidencia Requerida | Resultado Esperado | Resultado Observado | Estado | Observaciones |
|----|--------|----------|---------------------|--------------------|---------------------|--------|---------------|
| **E2E-01** | Conexión a InfluxDB | Validar autenticación y conexión al bucket real. | Log de inicio mostrando conexión exitosa. | Sistema reporta `Conectado a InfluxDB` sin excepciones de red. | PENDIENTE | PENDIENTE | Requiere credenciales de entorno real. |
| **E2E-02** | Lectura de sensor real | Verificar que se lee el `flow_rate` de un sensor de la lista. | Salida de logs indicando procesamiento del sensor `AARD-EDIF-A-...` | Se recupera el registro más reciente sin errores de casteo. | PENDIENTE | PENDIENTE | |
| **E2E-03** | Lectura normal | Validar que lecturas dentro de rango no disparen alertas. | Log de ejecución o `audit.jsonl` vacío para esa lectura. | No se envían mensajes a Telegram; contador de detectados = 0. | PENDIENTE | PENDIENTE | |
| **E2E-04** | Flujo crítico | Validar regla de flujo sobre umbral crítico. | Captura de pantalla del mensaje en Telegram. | Alerta de Severidad ALTA despachada en Telegram. | PENDIENTE | PENDIENTE | Umbrales provisionales. |
| **E2E-05** | Consumo elevado | Validar regla de volumen acumulado diario superado. | Captura de pantalla de Telegram. | Alerta por volumen diario superado enviada. | PENDIENTE | PENDIENTE | |
| **E2E-06** | Sensor sin datos / offline | Validar la regla de sensor desconectado (timeout). | Mensaje en Telegram notificando sensor offline. | Alerta de Severidad MEDIA o ALTA por falta de reporte. | PENDIENTE | PENDIENTE | |
| **E2E-07** | Envío a Telegram | Verificar integración de red y API de Telegram. | Mensaje renderizado correctamente con formato HTML en la app. | Mensaje visualmente correcto, con iconos y datos legibles. | PENDIENTE | PENDIENTE | |
| **E2E-08** | Cooldown / anti-spam | Confirmar que alertas repetitivas son silenciadas. | Log de consola mostrando `SUPPRESSED` tras primera alerta. | Primera alerta llega a Telegram, la segunda no se envía. | PENDIENTE | PENDIENTE | Requiere mantener el estado de memoria vivo entre pruebas. |
| **E2E-09** | Registro en audit log | Validar que toda acción genera trazabilidad. | Archivo `audit.jsonl` conteniendo el JSON del evento. | El evento tiene status `SENT` o `SUPPRESSED`, timestamp y sensor_id. | PENDIENTE | PENDIENTE | |
