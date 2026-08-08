# Recomendación sobre Archivos Generados

Durante la auditoría del repositorio se identificó el seguimiento (tracking de Git) de los siguientes archivos generados automáticamente durante el ciclo de vida y pruebas del software:

- `audit.jsonl`
- `audit_integration.jsonl`
- `e2e_output.txt`
- `reporte_v1.0.0.md` (y otros reportes)

### Diagnóstico Actual
Estos archivos contienen valiosa información temporal, logs de pruebas integradas y volcados de consola que sirven para respaldar funcionalmente la entrega de la **Semana 9**. Por instrucción expresa, **no se han borrado del repositorio** para preservar dicha evidencia académica.

### Recomendaciones para Release (Producción / v1.0.0)

Para el momento en que se decida transicionar el repositorio a la versión de producción oficial `v1.0.0`, se recomienda tomar una de estas dos acciones:

**Opción A (Recomendada): Mover a directorio de evidencias y congelar**
1. Crear una carpeta dedicada, por ejemplo: `docs/evidencias_semana9/`.
2. Mover `e2e_output.txt` y los `.jsonl` antiguos a esa carpeta.
3. Renombrarlos para que quede claro que son históricos (ej. `audit_evidencia_semana9.jsonl`).
4. Añadir `*.jsonl`, `*.txt` y los nombres originales a `.gitignore`.
*¿Por qué?* Mantiene la evidencia en el historial para revisiones académicas, pero previene que ejecuciones futuras ensucien el repositorio de Git con logs dinámicos, evitando conflictos de merge.

**Opción B: Ignorar completamente (Eliminación del Tracking)**
Si las evidencias ya han sido evaluadas y calificadas, se deben remover los archivos dinámicos del tracking:
1. Ejecutar: `git rm --cached audit.jsonl audit_integration.jsonl e2e_output.txt`.
2. Asegurar que estén en `.gitignore`.
3. Hacer commit del cambio.
*¿Por qué?* Un repositorio limpio solo debe contener código fuente, documentación y configuración estática. Los archivos de log y salida estándar (stdout) cambian con cada ejecución y generan ruido innecesario en el versionado.
