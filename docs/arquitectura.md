# Arquitectura Smart Alerts

## Flujo de Alertas

El ciclo completo del módulo se describe a continuación:
1. **Recolección:** Un ciclo (en `main.py`) adquiere la lectura (actualmente estática/simulada).
2. **Detector (`detector.py`):** Ejecuta cada lectura por las diferentes reglas y valida su tiempo de persistencia.
3. **Reglas (`rules.py`):** Modelos puros que retornan si la condición dada aplica o no, junto con su Severidad.
4. **Notificador (`notifier/telegram.py`):** 
   - **Cooldown:** Antes de enviar, verifica si `(sensor_id, rule_id)` ya fue alertado en los últimos `N` segundos (gestionado por `cooldown/memory.py`).
   - **Envío HTTP:** Si no está en cooldown, realiza la llamada a Telegram.
   - **Manejo de Errores:** En caso de 429 se extrae `retry_after`, esperando el tiempo necesario. Para errores 500 o timeouts, se usa backoff configurado.
   - **Recuperación:** Retorna un estado (`SENT`, `SUPPRESSED`, `FAILED`).

## Estados

- **SENT:** La alerta alcanzó la red HTTP exitosamente y fue procesada por Telegram con `ok=True`. Sólo entonces se activa el cooldown.
- **SUPPRESSED:** La alerta no se envió porque fue enviada recientemente.
- **FAILED:** Errores irrecuperables (HTTP 401) o se alcanzó el límite de intentos (Timeout, Error de Conexión) sin éxito.

## Resoluciones de Incidentes

- Las reglas detectan cuándo la condición vuelve a ser normal y eliminan el registro de persistencia del `Detector`.

## Decisiones Arquitectónicas y Riesgos Conocidos

- **Cooldown en memoria:** En un sistema de contenedores múltiples o serverless con reinicios, el diccionario se perderá, permitiendo alertas duplicadas en un reinicio en frío. Por eso, el `CooldownManager` está diseñado como interfaz para migrar fácilmente a Redis.
- **Timezone:** Para evitar confusiones, todos los logs y fechas en mensajes de Telegram son parseados obligatoriamente con la timezone de la instalación física del sistema (ej. `America/El_Salvador`).
