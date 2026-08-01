# Runbook de Operaciones de Alertas — Smart_Alerts

## Propósito

Este runbook describe los procedimientos operativos estándar (SOP) para responder a las alertas generadas por el sistema Smart_Alerts. Cubre las cuatro reglas activas (R01–R04), incluyendo severidad, rol responsable, acciones recomendadas, comportamiento del cooldown, escalación y cierre de incidentes.

---

## Reglas activas

| ID  | Nombre                        | Condición de disparo                                           | Severidad  |
|-----|-------------------------------|----------------------------------------------------------------|------------|
| R01 | Flujo alto crítico            | `flow_rate` supera el umbral máximo configurado para la zona  | `CRITICAL` |
| R02 | Flujo fuera de horario        | `flow_rate > 0` detectado fuera del horario operativo         | `WARNING`  |
| R03 | Sensor fuera de línea         | Sin datos nuevos del sensor durante más de N segundos         | `WARNING`  |
| R04 | Consumo diario acumulado alto | `cumulative_volume` supera el límite diario planificado       | `WARNING`  |

---

## R01 — Flujo alto crítico

**Severidad:** 🔴 CRITICAL

**Rol responsable:** Técnico de mantenimiento de turno

**Condición:** El caudal registrado por un sensor supera el umbral máximo configurado en la variable de entorno `FLOW_RATE_THRESHOLD` (valor típico: 20 L/min).

### Acciones recomendadas

1. Verificar físicamente la zona reportada para detectar llaves abiertas, fugas o roturas.
2. Cerrar manualmente el suministro de la zona si el caudal no disminuye.
3. Registrar el incidente en el sistema de tickets con el `sensor_id`, la zona y el valor detectado.
4. Si el problema persiste más de 10 minutos, escalar al supervisor de planta (ver sección *Escalación*).

### Cooldown

- **Período:** 300 segundos (5 minutos) por clave `(sensor_id, rule_id)`.
- Durante el cooldown, alertas adicionales de la misma combinación sensor/regla quedan en estado `SUPPRESSED`.
- El cooldown se activa únicamente cuando la alerta es enviada exitosamente (`SENT`).

### Cierre del incidente

- El incidente se cierra cuando el valor de `flow_rate` desciende por debajo del umbral durante al menos un ciclo de evaluación.
- Confirmar el cierre en el ticket indicando la causa raíz y la acción correctiva aplicada.

---

## R02 — Flujo fuera de horario

**Severidad:** 🟡 WARNING

**Rol responsable:** Supervisor de planta / Guardia de seguridad

**Condición:** Se detecta caudal activo (`flow_rate > 0`) fuera del horario operativo configurado para la zona (campo `operating_hours` en la configuración).

### Acciones recomendadas

1. Verificar si hay personal autorizado trabajando fuera de horario.
2. Si no hay personal autorizado, inspeccionar la zona para detectar fugas o acceso no autorizado.
3. Revisar el historial de accesos en los últimos 60 minutos.
4. Si el consumo es continuo y no justificado, cortar el suministro y notificar al responsable de zona.

### Cooldown

- **Período:** 300 segundos (5 minutos) por clave `(sensor_id, rule_id)`.
- Alertas repetidas del mismo sensor/regla quedan suprimidas hasta que expire el cooldown.

### Cierre del incidente

- El incidente se cierra cuando el sensor deja de registrar caudal fuera de horario o cuando el horario operativo comienza.
- Documentar si el consumo fue autorizado o no.

---

## R03 — Sensor fuera de línea

**Severidad:** 🟡 WARNING

**Rol responsable:** Técnico de infraestructura / DevOps

**Condición:** El sistema no recibe datos nuevos de un sensor durante más del período de inactividad configurado. Indica un posible fallo de conectividad, corte de energía o fallo del sensor físico.

### Acciones recomendadas

1. Verificar conectividad de red en la zona del sensor afectado.
2. Revisar el estado del contenedor o servicio que publica datos hacia InfluxDB.
3. Comprobar si el sensor tiene alimentación eléctrica.
4. Si el problema es de red, reiniciar el agente de telemetría correspondiente.
5. Si el sensor físico está dañado, iniciar proceso de reemplazo y dejar constancia en el ticket.

### Cooldown

- **Período:** 300 segundos (5 minutos) por clave `(sensor_id, rule_id)`.
- Si el sensor permanece sin datos, la alerta puede reaparecer al expirar el cooldown.

### Cierre del incidente

- El incidente se cierra cuando el sensor vuelve a enviar datos dentro del período esperado.
- Registrar la causa del downtime y la duración total del período sin datos.

---

## R04 — Consumo diario acumulado alto

**Severidad:** 🟡 WARNING

**Rol responsable:** Responsable de zona / Gerencia de operaciones

**Condición:** El volumen acumulado diario (`cumulative_volume`) del sensor supera el límite planificado configurado en `DAILY_VOLUME_THRESHOLD`.

### Acciones recomendadas

1. Revisar el historial de consumo del día para identificar picos inusuales.
2. Comparar con el consumo típico de días anteriores (mismo día de la semana).
3. Determinar si el exceso corresponde a una actividad extraordinaria justificada.
4. Si el consumo es anómalo, correlacionar con las alertas R01 (flujo alto) y R02 (fuera de horario) del mismo sensor.
5. Si corresponde a una fuga no detectada, activar el protocolo de cierre de suministro.

### Cooldown

- **Período:** 300 segundos (5 minutos) por clave `(sensor_id, rule_id)`.
- El medidor acumulado se reinicia al inicio de cada día; por tanto, esta alerta puede dispararse una sola vez por día en condiciones normales.

### Cierre del incidente

- El incidente se cierra al final del día cuando se reinicia el contador acumulado o cuando el consumo se normaliza.
- Documentar si el exceso fue justificado o requirió acción correctiva.

---

## Escalación

Si una alerta de severidad `CRITICAL` (R01) no se resuelve dentro de **10 minutos** desde su primera notificación:

1. Notificar al **supervisor de planta** directamente por Telegram o llamada telefónica.
2. Si el supervisor no responde en 5 minutos, notificar al **gerente de operaciones**.
3. Si el incidente implica riesgo de daño estructural o pérdida masiva de agua, activar el **protocolo de emergencia de infraestructura**.

Para alertas `WARNING` no resueltas en **30 minutos**:

1. Escalar al supervisor de turno.
2. Documentar en el ticket el intento de resolución y el estado actual.

---

## Comportamiento del sistema durante el cooldown

El sistema implementa un mecanismo de *debounce* (cooldown) para evitar spam de notificaciones:

- La clave de cooldown es `(sensor_id, rule_id)`, lo que significa que:
  - El mismo sensor disparando la misma regla queda en cooldown.
  - Diferentes sensores con la misma regla, o el mismo sensor con diferentes reglas, **no** se afectan entre sí.
- El registro de cooldown es **en memoria**. Un reinicio del servicio limpia el estado y puede producir alertas duplicadas temporalmente.
- El período por defecto es **300 segundos**, configurable mediante la variable `ALERT_COOLDOWN_SECONDS`.

---

## Estados de alerta

| Estado      | Descripción                                                                 |
|-------------|-----------------------------------------------------------------------------|
| `SENT`      | La alerta fue enviada exitosamente a Telegram y el cooldown fue activado.   |
| `SUPPRESSED`| La alerta fue ignorada porque la misma combinación está dentro del cooldown.|
| `FAILED`    | La alerta no pudo enviarse (error HTTP irrecuperable o límite de reintentos alcanzado). |

---

## Referencias

- [Política de Cooldown](./politica_cooldown_alertas.md)
- [Formato del Mensaje de Alerta](./formato_mensaje_alerta.md)
- [Arquitectura Smart Alerts](./arquitectura.md)
- [Análisis del Escenario Hídrico](./analisis.md)
