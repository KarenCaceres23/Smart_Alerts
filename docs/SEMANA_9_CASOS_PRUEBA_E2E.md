# Casos de Prueba E2E - Semana 9

Los siguientes casos detallan los escenarios para la prueba E2E de validación funcional con la infraestructura real de SmartH2O.

---

### Caso: E2E-01 - Detección de Flujo Crítico
- **ID:** E2E-01
- **Nombre:** Detección de Flujo Crítico
- **Precondición:** El sistema tiene conectividad a InfluxDB y Telegram.
- **Sensor:** `AARD-EDIF-A-SAN1` (Sanitarios Piso 1)
- **Entrada:** Dato en InfluxDB con `flow_rate = 25.0` (L/min)
- **Acción:** Ejecutar `python -m src.main`
- **Resultado Esperado:** El sistema detecta que 25.0 supera el *Umbral provisional pendiente de validación funcional* (20.0), aprueba el debounce, y envía la alerta.
- **Evidencia:** Captura de pantalla de Telegram y log `SENT` en `audit.jsonl`.
- **Criterio de Aceptación:** La alerta incluye el valor exacto (25.0 L/min) y la zona correcta ("Sanitarios Piso 1").

---

### Caso: E2E-02 - Prevención Anti-Spam (Cooldown)
- **ID:** E2E-02
- **Nombre:** Prevención Anti-Spam (Cooldown)
- **Precondición:** Se acaba de ejecutar el Caso E2E-01 exitosamente y el estado de memoria sigue vivo.
- **Sensor:** `AARD-EDIF-A-SAN1`
- **Entrada:** Dato subsecuente en InfluxDB con `flow_rate = 26.0` (L/min) dentro del periodo de cooldown (ej. 5 minutos).
- **Acción:** Ejecutar evaluación nuevamente.
- **Resultado Esperado:** El detector identifica la anomalía, pero el Notificador la suprime (Cooldown activo).
- **Evidencia:** Mensaje `SUPPRESSED` en el log de salida/auditoría.
- **Criterio de Aceptación:** No se genera un mensaje duplicado en Telegram.

---

### Caso: E2E-03 - Comportamiento Normal
- **ID:** E2E-03
- **Nombre:** Flujo Normal
- **Precondición:** Sin alertas activas.
- **Sensor:** `AARD-EDIF-A-COCINA`
- **Entrada:** `flow_rate = 1.5` y `cumulative_volume = 150.0`.
- **Acción:** Ejecutar `python -m src.main`.
- **Resultado Esperado:** Los valores están por debajo de los *umbrales provisionales pendientes de validación funcional*. No se detectan anomalías.
- **Evidencia:** Log de ejecución indica `Detectados=0, Enviados=0`.
- **Criterio de Aceptación:** Ninguna notificación a Telegram y el sistema termina limpiamente.

---

### Caso: E2E-04 - Sensor Offline
- **ID:** E2E-04
- **Nombre:** Alerta de Inactividad (Offline)
- **Precondición:** Sensor sin enviar datos en InfluxDB por más de 10 minutos (timeout).
- **Sensor:** `AARD-EDIF-A-CIST`
- **Entrada:** La consulta a InfluxDB retorna `None` o vacío para la ventana de tiempo.
- **Acción:** Ejecutar `python -m src.main`.
- **Resultado Esperado:** El sistema evalúa el sensor offline y dispara una alerta de pérdida de conectividad.
- **Evidencia:** Mensaje de alerta de inactividad en Telegram.
- **Criterio de Aceptación:** El mensaje especifica claramente que el sensor no reporta datos, diferenciándose de una alerta de flujo.
