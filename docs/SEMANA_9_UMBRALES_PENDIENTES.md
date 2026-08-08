# Matriz de Umbrales Pendientes - Semana 9

> **IMPORTANTE:** Todos los valores aquí listados tienen estado **PROVISIONAL / PENDIENTE DE VALIDACIÓN**. Han sido reutilizados a partir del modelo académico original para permitir pruebas de integración (E2E), pero no deben considerarse valores finales de producción. Deben ser calibrados con datos reales de los sensores antes de crear el release estable de producción.

| Sensor | Zona | Umbral de Flujo Crítico Actual | Umbral Fuera de Horario Actual | Límite de Volumen Actual | Horario Operativo | Estado del Umbral | Responsable de Validar | Observaciones |
|--------|------|--------------------------------|--------------------------------|--------------------------|-------------------|-------------------|------------------------|---------------|
| `AARD-EDIF-A-CIST` | Cisterna | 20.0 L/min | 5.0 L/min | 1000.0 L | 07:00 - 19:00 | **PROVISIONAL / PENDIENTE DE VALIDACIÓN** | Equipo de Dominio / Datos | Umbral académico asignado temporalmente. |
| `AARD-EDIF-A-COCINA` | Cocina | 20.0 L/min | 5.0 L/min | 1000.0 L | 07:00 - 19:00 | **PROVISIONAL / PENDIENTE DE VALIDACIÓN** | Equipo de Dominio / Datos | Umbral académico asignado temporalmente. |
| `AARD-EDIF-A-RIEGO` | Riego | 20.0 L/min | 5.0 L/min | 1000.0 L | 07:00 - 19:00 | **PROVISIONAL / PENDIENTE DE VALIDACIÓN** | Equipo de Dominio / Datos | Umbral académico asignado temporalmente. |
| `AARD-EDIF-A-SAN1` | Sanitarios Piso 1 | 20.0 L/min | 5.0 L/min | 1000.0 L | 07:00 - 19:00 | **PROVISIONAL / PENDIENTE DE VALIDACIÓN** | Equipo de Dominio / Datos | Umbral académico asignado temporalmente. |
| `AARD-EDIF-A-SAN2` | Sanitarios Piso 2 | 20.0 L/min | 5.0 L/min | 1000.0 L | 07:00 - 19:00 | **PROVISIONAL / PENDIENTE DE VALIDACIÓN** | Equipo de Dominio / Datos | Umbral académico asignado temporalmente. |

---
**Nota para la Semana 10:** Se requiere confirmación por parte del equipo de dominio para actualizar el archivo `src/main.py` con los umbrales fisiológicos e hidráulicos reales de cada zona (por ejemplo, es probable que la Cisterna tolere un flujo mucho mayor que la Cocina).
