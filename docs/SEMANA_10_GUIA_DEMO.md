# Guion de Demostración - Semana 10

Este documento contiene el guion paso a paso para la demostración en vivo del sistema Smart_Alerts, junto con un plan de contingencia detallado.

## Flujo Esperado de la Demo

### 1. Mostrar sensor/dato en InfluxDB
- **Pantalla a mostrar:** Interfaz gráfica de InfluxDB (Data Explorer).
- **Discurso Sugerido:** "Aquí podemos observar nuestro bucket `telemetria_agua` recibiendo datos reales del sistema SmartH2O. Enfocaremos nuestra prueba en el sensor de los Sanitarios del Piso 1 (`AARD-EDIF-A-SAN1`)."
- **Evidencia:** Gráfica de InfluxDB con los datos actuales.
- **Resultado Esperado:** Visualización clara de que hay datos entrando a la base de datos.

### 2. Mostrar una condición anómala
- **Pantalla a mostrar:** Interfaz gráfica de InfluxDB o un script de simulación de inyección de datos.
- **Discurso Sugerido:** "Para probar nuestro detector, vamos a inyectar (o visualizar) una lectura que supera nuestro umbral crítico, con un flujo de 25 L/min."
- **Evidencia:** Dato anómalo visible en el dashboard o log de inyección.
- **Resultado Esperado:** Un pico claro por encima de los 20 L/min.

### 3. Ejecutar Smart_Alerts
- **Pantalla a mostrar:** Consola / Terminal del servidor.
- **Discurso Sugerido:** "Ahora ejecutaremos manualmente nuestro ciclo de detección usando `python -m src.main`. En producción, esto será automatizado, pero hoy lo lanzamos a demanda para observar el comportamiento paso a paso."
- **Evidencia:** Comando tipeado y ejecutándose en pantalla.
- **Resultado Esperado:** Script corriendo sin errores.

### 4. Mostrar detección
- **Pantalla a mostrar:** Consola / Terminal del servidor (Salida del log).
- **Discurso Sugerido:** "Como pueden ver en los logs, el sistema ha evaluado las métricas de los 5 sensores. Detectó la anomalía en el Sanitario Piso 1 al superar la regla de Umbral Crítico y el tiempo de persistencia (debounce)."
- **Evidencia:** Log mostrando "Detectados=1".
- **Resultado Esperado:** Salida estándar indicando la detección.

### 5. Mostrar envío
- **Pantalla a mostrar:** Consola / Terminal del servidor.
- **Discurso Sugerido:** "El módulo de notificaciones despachó exitosamente el mensaje. Los logs muestran 'Enviados=1'."
- **Evidencia:** Log de consola mostrando el estado de envío.
- **Resultado Esperado:** Log claro y sin excepciones de API.

### 6. Mostrar alerta en Telegram
- **Pantalla a mostrar:** Aplicación de Telegram (Móvil o Web).
- **Discurso Sugerido:** "Pasemos a Telegram. Aquí, nuestro grupo de Mantenimiento acaba de recibir la alerta. El mensaje incluye la severidad, la zona, el valor crítico registrado y el timestamp exacto."
- **Evidencia:** Alerta formateada visible en la interfaz de chat.
- **Resultado Esperado:** Mensaje renderizado correctamente en HTML.

### 7. Mostrar audit log
- **Pantalla a mostrar:** Archivo `audit.jsonl` abierto en la terminal (usando `tail` o un editor).
- **Discurso Sugerido:** "Todo el ciclo de vida de este evento ha quedado registrado de manera inmutable y estructurada en nuestro Audit Log, asegurando trazabilidad para auditorías futuras."
- **Evidencia:** Registro JSON con evento `SENT` y detalles.
- **Resultado Esperado:** Validación del registro.

### 8. Explicar cooldown/anti-spam
- **Pantalla a mostrar:** Consola / Terminal ejecutando nuevamente el script.
- **Discurso Sugerido:** "Si la anomalía persiste y el script vuelve a ejecutarse, el sistema no inundará Telegram con el mismo mensaje. Veamos qué ocurre." *(Ejecutar el script)*. "Como ven, el sistema suprime el envío aplicando el 'Cooldown', mostrando 'Suprimidos=1'."
- **Evidencia:** Log de consola mostrando `SUPPRESSED`.
- **Resultado Esperado:** Ningún mensaje nuevo en Telegram.

### 9. Mostrar recuperación o estado normal
- **Pantalla a mostrar:** Consola y/o InfluxDB.
- **Discurso Sugerido:** "Finalmente, una vez que el flujo se normaliza por debajo del umbral, el sistema resetea sus estados y cierra su ciclo."
- **Evidencia:** Logs sin anomalías.
- **Resultado Esperado:** Ejecución limpia (Detectados=0).

---

## Plan B (Plan de Contingencia si falla la demo)

Las demostraciones en vivo pueden sufrir imprevistos externos. Si algo falla, mantén la calma, no inventes resultados, y procede con estas alternativas apoyándote en las evidencias pre-capturadas:

1. **Si InfluxDB no responde o la red falla:**
   - **Acción:** Muestra las capturas de pantalla de la matriz de evidencias y el archivo `audit_integration.jsonl` generado localmente previamente. Explica: *"Tuvimos una pérdida de conectividad con la base de datos externa, pero podemos ver en nuestras corridas de prueba integradas de ayer cómo el sistema recuperó y evaluó este mismo caso exitosamente."*
2. **Si Telegram no responde o el Token está vencido:**
   - **Acción:** Muestra los logs de consola donde el módulo hace el intento y aplica el *Backoff / Retry*. Explica: *"La API de Telegram está caída/rechazando el token. Podemos ver que nuestro sistema es resiliente: está encolando los reintentos y documentando el error en el audit log sin crashear."* Muestra una captura de pantalla del móvil del día anterior demostrando el formato de la alerta.
3. **Si no aparecen lecturas o el sensor no genera anomalías en el momento:**
   - **Acción:** Modifica temporalmente el umbral en `.env` o en código a un valor bajísimo (ej. 0.1 L/min) para forzar la anomalía con el flujo normal base, y re-corre la aplicación para demostrar el disparo.
4. **Si todo el flujo de red se cae:**
   - **Acción:** Corre la suite de pruebas automatizada (`pytest tests/unit -v`). Explica: *"Como nuestro entorno está completamente unitarizado con Mocks, podemos demostrar matemáticamente que toda la lógica de detección, cooldown y formatos funciona perfectamente a nivel de código, independientemente de la infraestructura externa."*
