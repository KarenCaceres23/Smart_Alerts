# Nota Técnica: Decisión de Arquitectura de Ejecución

Actualmente, el módulo `MonitoringService` (`python -m src.main`) está configurado para ejecutarse como un **ciclo único**. Esto significa que lee los datos una vez, procesa y se cierra.

Al implementar en producción (Semana 10 y posteriores), el equipo deberá tomar una decisión arquitectónica sobre cómo se mantendrá vivo este proceso en el tiempo, ya que esto tiene impacto directo sobre las políticas de Debounce (anti-ruido) y Cooldown (anti-spam) que actualmente dependen de la memoria RAM.

### A. Servicio Continuo (Demonio / While True)
La aplicación se envuelve en un ciclo infinito con un `sleep` entre llamadas.
- **Ventajas:** Es la forma más rápida de mantener el estado de memoria vivo. El Debounce y Cooldown actuales (`MemoryCooldownManager`) funcionarán a la perfección sin requerir bases de datos extras.
- **Desventajas:** Si el servicio se cae, el estado de las alertas (cooldowns activos y contadores de tiempo de anomalía) se reinicia por completo. Requiere un gestor de procesos (como `systemd` o Docker `restart: always`).

### B. Ejecución Cronometrada (Cron / Tareas Programadas)
Se invoca `python -m src.main` cada 1 o 5 minutos utilizando un `cronjob`.
- **Ventajas:** No hay demonios en memoria. Si una ejecución falla o se cuelga, muere aisladamente y el cron levanta otra limpia después.
- **Desventajas:** **Rompe la implementación actual de Debounce y Cooldown.** Dado que la RAM se libera en cada finalización, el script nunca "recordará" que ya envió una alerta o cuánto tiempo lleva una anomalía activa. Generaría alertas spam en cada invocación de Cron o jamás dispararía el Debounce si este exige >5 minutos consecutivos y el Cron dura 1 segundo.

### C. Servicio Continuo o Cron con Persistencia Externa (Redis)
Migrar el estado a una base de datos In-Memory (Redis).
- **Ventajas:** Combina lo mejor de ambos mundos. Si el servicio crashea o se ejecuta de forma efímera por Cron, al conectarse a Redis leerá su "memoria externa" y sabrá exactamente qué alertas están silenciadas y cuánto tiempo lleva una anomalía activa. Arquitectura escalable lista para Kubernetes / Cloud.
- **Desventajas:** Añade complejidad de infraestructura. Requiere levantar un contenedor Redis y reescribir parte de la abstracción actual de Cooldown para usar un adaptador de Redis en vez de diccionarios locales.

### Conclusión Pendiente
Antes de lanzar v1.0.0, **NO SE HA TOMADO UNA DECISIÓN DEFINITIVA**. El equipo deberá evaluar la ruta que mejor balancee la capacidad técnica actual y los requerimientos de la demo de la Semana 10.
