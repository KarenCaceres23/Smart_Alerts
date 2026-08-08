# Checklist de Cierre - Semana 9

Este checklist consolida el estado actual del proyecto Smart_Alerts y los pasos restantes para transicionar a la Semana 10.

### Tareas Técnicas Realizadas
- [x] Código consolidado
- [x] 5 sensores reales configurados en `src/main.py` (`AARD-EDIF-A-...`)
- [x] Esquema InfluxDB documentado (Bucket: `telemetria_agua`, Measurement: `consumo_agua`)
- [x] `.env.example` actualizado con variables alineadas al esquema
- [x] `README.md` actualizado con esquema y detalles de sensores
- [x] Tests unitarios adaptados y pasando (34/34 aprobados)
- [x] Validación de linter Ruff aprobada
- [x] Formateador Black aprobado
- [x] Escaneo de secretos superado exitosamente (repositorio limpio)

### Tareas Pendientes para Validación en Entorno
- [ ] Prueba E2E real en infraestructura
- [ ] Evidencias E2E capturadas (Log + Capturas Telegram)
- [ ] Validación final de umbrales con el equipo de dominio
- [ ] Decisión técnica sobre arquitectura de ejecución (Cron vs Servicio Continuo)
- [ ] Revisión final y depuración de archivos generados automáticamente (`.jsonl`, `.txt`)
- [ ] Crear release `v1.0.0`

---

## Condiciones Necesarias para crear v1.0.0

Para proceder a realizar el etiquetado y despliegue del release `v1.0.0`, se deben cumplir obligatoriamente los siguientes hitos técnicos:

1. **Integración Comprobada:** Se debe contar con al menos una prueba manual E2E exitosa que demuestre que el código base actual puede leer de un bucket InfluxDB real y despachar un mensaje a un bot de Telegram real.
2. **Ajuste de Umbrales:** Reemplazar los *umbrales provisionales* por los parámetros hidráulicos definidos y validados por el negocio.
3. **Estrategia de Ejecución Definida:** Debe documentarse o implementarse si la aplicación se invocará como proceso aislado (cron) o como demonio de larga duración. Si es cron, debe implementarse o documentarse la integración de almacenamiento de estado persistente (Redis) para que el Debounce y el Cooldown funcionen, o ajustar el sistema para aceptar esta limitación.
4. **Limpieza del Repositorio:** Asegurarse de que no se publiquen archivos generados (como `audit_integration.jsonl` o `e2e_output.txt`) dentro del commit correspondiente a la release oficial.
