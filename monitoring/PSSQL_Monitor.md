# Guía de Monitoreo para Azure Database for PostgreSQL Flexible Server

Esta guía resume las métricas esenciales para monitorear el rendimiento y la estabilidad de servidores PostgreSQL en Azure. Incluye algunas métricas importantes, por qué son importantes y qué acciones tomar. Incluye referencias oficiales a la [documentación de Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/supported-metrics/microsoft-dbforpostgresql-flexibleservers-metrics).

Además, recomendamos el uso de Alerts y Azure Performance Advisor para potenciar la monitorización, pudiendo usar el dashboard de Grafana oficial como punto de referencia,

- [Configure alerts - Azure portal - Azure Database for PostgreSQL flexible server | Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-alert-on-metrics)
- [Boost Your Postgres Server on Azure with Enhanced Azure Advisor Performance Recommendations! | Microsoft Community Hub](https://techcommunity.microsoft.com/blog/adforpostgresql/boost-your-postgres-server-on-azure-with-enhanced-azure-advisor-performance-reco/4370089)
- [Azure / Azure PostgreSQL / Flexible Server Monitoring | Grafana Labs](https://grafana.com/grafana/dashboards/19556-azure-azure-postgresql-flexible-server-monitoring/)

Y habilitar en los entornos de mayor criticidad las enhanced metrics,

[Monitoring and metrics - Azure Database for PostgreSQL flexible server | Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-monitoring#enabling-enhanced-metrics)




---

## 1. Utilización de CPU (`cpu_percent`)

**Descripción:** Porcentaje de CPU en uso en el servidor PostgreSQL. Indica qué fracción de los vCores asignados está consumiéndose en un momento dado.

**Importancia:** Un uso sostenido >80% puede generar latencia y reflejar cuellos de botella en consultas.

**Umbral sugerido:** Alerta si supera el 80% durante varios minutos. Microsoft sugiere alertar si alcanza 100% durante 5 minutos o 95% durante 2 horas.

**Buenas prácticas:**
- Revisar consultas con `pg_stat_statements`.
- Pooling con PgBouncer.
- Escalar si CPU sigue al límite tras optimización.

**Alerta recomendada:** Crear alerta en Azure Monitor cuando `cpu_percent` supere 80% durante al menos 5 minutos.

---

## 2. Uso de Memoria (`memory_percent`)

**Descripción:** Porcentaje de la memoria del servidor en uso.

**Importancia:** Un uso cercano al 100% puede provocar swapping o errores OOM.

**Umbral sugerido:** Alerta si supera 85-90% de forma sostenida.

**Buenas prácticas:**
- Revisar `work_mem`, `shared_buffers`, `maintenance_work_mem`.
- Usar PgBouncer para liberar memoria.
- Evitar conexiones ociosas.

**Alerta recomendada:** Crear alerta cuando `memory_percent` supere 90% durante más de 5 minutos.

---

## 3. Conexiones activas (`active_connections`)

**Descripción:** Número total de conexiones al servidor, incluyendo activas, inactivas y en espera.

**Importancia:** El exceso puede agotar memoria y CPU o llegar al límite de `max_connections`.

**Umbral sugerido:** Alerta si se supera el 80% de `max_connections`.

**Buenas prácticas:**
- Pooling de conexiones (modo transacción).
- Evitar fuga de conexiones.
- Revisar `pg_stat_activity` para estados de conexión.

**Alerta recomendada:** Alerta si `active_connections` excede el 80% del límite permitido.

---

## 4. IOPS y Throughput de Disco

**Métricas:** `read_iops`, `write_iops`, `read_throughput`, `write_throughput`, `disk_queue_depth`

**Importancia:** La saturación de I/O es un cuello de botella frecuente en rendimiento.

**Umbral sugerido:** Alerta si `Disk IOPS Consumed %` o `Throughput` superan 90% del límite provisionado.

**Buenas prácticas:**
- Aumentar almacenamiento para obtener más IOPS.
- Revisar consultas con alto uso de disco.
- Ajustar `shared_buffers` y evitar table scans.

**Alerta recomendada:** Alertar si `IOPS` o `Throughput` alcanzan el 90% del máximo disponible.

---

## 5. Uso de almacenamiento (`storage_used`, `storage_percent`)

**Descripción:** Espacio utilizado en disco en bytes y como porcentaje.

**Importancia:** Superar 95% vuelve al servidor read-only automáticamente.

**Umbral sugerido:** Alerta al superar 80% para reaccionar antes del límite crítico.

**Buenas prácticas:**
- Habilitar `autogrow` si es posible.
- Monitorear WAL y bloat.
- Eliminar objetos innecesarios.

**Alerta recomendada:** Alerta cuando `storage_percent` supere 80% del espacio disponible.

---

## 6. Retardo de replicación (`physical_replication_delay_in_seconds`)

**Descripción:** Retraso en segundos de la réplica respecto al primario.

**Importancia:** Un alto lag compromete lecturas actualizadas o failover correcto.

**Umbral sugerido:** Alerta si supera 300 segundos (5 minutos).

**Buenas prácticas:**
- Asegurar que la réplica tenga recursos suficientes.
- Monitorear WAL no aplicados.

**Alerta recomendada:** Alerta si `physical_replication_delay_in_seconds` supera 300 segundos.

---

## 7. Transacciones por segundo (`tps`)

**Descripción:** Cantidad de commits o rollbacks por segundo.

**Importancia:** Indica el throughput transaccional.

**Umbral sugerido:** Depende del sistema. Vigilar caídas anómalas o ausencia de transacciones.

**Buenas prácticas:**
- Usar para detectar caídas o congestión.
- Correlacionar con CPU y latencia.

**Alerta recomendada:** Alerta si `tps` = 0 en horario de carga habitual.

---

## 8. Deadlocks (`deadlocks`)

**Descripción:** Número de deadlocks detectados.

**Importancia:** Indican problemas de concurrencia.

**Umbral sugerido:** > 0 es ya crítico. Alerta con 1 o más deadlocks por intervalo.

**Buenas prácticas:**
- Revisar orden de acceso a objetos.
- Monitorear transacciones largas.
- Ver los logs para detalle de la consulta.

**Alerta recomendada:** Alerta inmediata si `deadlocks > 0`.

---

## 9. Eventos de espera (`sessions_by_wait_event_type`)

**Descripción:** Número de sesiones clasificadas por tipo de espera (I/O, lock, etc.).

**Importancia:** Permite detectar cuellos de botella específicos.

**Umbral sugerido:** No hay uno fijo, pero aumentos inusuales son señal de problema.

**Buenas prácticas:**
- Correlacionar esperas de tipo Lock con bloqueos.
- Usar Query Store para ver esperas por consulta.

**Alerta recomendada:** No se recomienda alerta fija. Usar para diagnóstico junto a otras métricas.

---

## 10. Autovacuum

**Métricas:** `autovacuum_count_user_tables`, `bloat_percent`, `n_dead_tup_user_tables`

**Importancia:** Un autovacuum ineficiente lleva a bloat, bajo rendimiento o riesgo de wraparound.

**Umbral sugerido:**
- `bloat_percent > 20-30%`
- `autovacuum_count_user_tables = 0` durante largos periodos

**Buenas prácticas:**
- Habilitar `metrics.autovacuum_diagnostics = ON`
- Ajustar `scale_factor` y `threshold` según tabla.
- Complementar con `pg_repack` si hay bloat alto.

**Alerta recomendada:**
- Alerta si `bloat_percent` supera 25%
- Alertar si `autovacuum_count_user_tables` no cambia en 24h en bases activas

---

## 11. Consultas largas (`longest_query_time_sec`)

**Descripción:** Duración en segundos de la consulta más larga en ejecución.

**Importancia:** Identifica posibles consultas colgadas o pesadas que impactan rendimiento.

**Umbral sugerido:** > 300 segundos en OLTP. Ajustable según SLA interno.

**Buenas prácticas:**
- Habilitar `pg_stat_statements` y Query Store.
- Revisar `EXPLAIN ANALYZE`.
- Optimizar o parametrizar queries.

**Alerta recomendada:** Crear alerta si `longest_query_time_sec` > 300s.

---

## 12. Alta disponibilidad – Estado de disponibilidad (`is_db_alive`)

**Descripción:** Indica si la base de datos está activa y disponible. Es una métrica booleana (1 = disponible, 0 = no disponible).

**Importancia:** Es fundamental en configuraciones con Alta Disponibilidad (HA) para detectar interrupciones del servicio, incluso si no hay presión sobre los recursos del sistema.

**Umbral sugerido:** Alerta si `is_db_alive` = 0 durante más de 1 minuto.

**Buenas prácticas:**
- Supervisar junto a otras métricas como `cpu_percent` y `memory_percent` para descartar fallos relacionados con carga.
- Verificar el estado de la réplica secundaria si el primario no responde.
- Utilizar dashboards para visualizar la continuidad de la métrica y detectar caídas intermitentes.

**Alerta recomendada:** Crear una alerta si `is_db_alive` = 0 durante más de 60 segundos, especialmente en instancias configuradas con Alta Disponibilidad.


---

## 13. Métricas cruzadas 

| Métricas combinadas | Posible síntoma | Impacto en la instancia | Recomendación |
|---------------------|------------------|--------------------------|----------------|
| `cpu_percent` alto + `tps` bajo | CPU ocupada sin tráfico real | Carga ineficiente; riesgo de saturación sin beneficio | Revisa `longest_query_time_sec` y `wait_event_type` |
| `memory_percent` alto + `disk_queue_depth` alto | Falta de caché, presión de I/O | Lentitud general, alto uso de disco | Ajusta `shared_buffers`, considera escalar |
| `active_connections` alto + `sessions_by_wait_event_type` en `Lock` | Sesiones bloqueadas por contención | Posibles errores de timeout o transacciones abortadas | Investiga `pg_stat_activity`, ajusta concurrencia |
| `deadlocks` > 0 + `longest_query_time_sec` alto | Transacciones largas causando bloqueos mutuos | Aborto de transacciones y pérdida de datos parciales | Optimiza acceso y reduce duración de transacciones |
| `autovacuum_count_user_tables` bajo + `bloat_percent` alto + `storage_percent` subiendo | Limpieza ineficaz, espacio desperdiciado | Rendimiento degradado, riesgo de quedarse sin espacio | Revisa autovacuum o usa `pg_repack` |
| `read_iops` muy alto + bajo cache hit ratio (custom) | Uso intensivo de disco por mala cacheabilidad | Latencia en consultas, sobrecarga de I/O | Aumenta `shared_buffers`, mejora índices |
| `tps` normal + `write_iops` muy alto | Transacciones escriben mucho | Alta presión en disco, posible throttling | Verifica índices, patrones de escritura |
| `cpu_percent` alto + `sessions_by_wait_event_type` en `LWLock` o `BufferPin` | Contención interna en motor de PostgreSQL | Cuellos de botella no evidentes, latencia | Revisar concurrencia en tablas críticas |
| `storage_percent` alto + `physical_replication_delay_in_seconds` alto | Réplica no avanza, WALs acumulados | Podría llevar a read-only si se llena el disco | Investigar réplica y limpieza de WAL |
| `longest_query_time_sec` alto + `read_iops` y `write_iops` elevados | Consulta lenta hace uso intensivo de disco | Recursos ocupados por una sola operación | Optimizar consulta, revisar `EXPLAIN ANALYZE` |

### Métricas cruzadas adicionales

| Métricas combinadas | Posible síntoma | Impacto en la instancia | Recomendación |
|---------------------|------------------|--------------------------|----------------|
| `tps` bajo + `deadlocks` > 0 | Carga baja por errores de concurrencia | Bajo rendimiento por abortos de transacciones | Optimizar acceso concurrente, analizar conflictos |
| `disk_queue_depth` alto + `write_iops` bajo | Escrituras atascadas, posibles locks | Latencia alta, riesgo de timeouts | Investigar esperas de I/O o locks sobre tabla caliente |
| `cpu_percent` bajo + `tps` bajo + `active_connections` alto | Aplicación conectada pero no activa | Conexiones colgadas o fuga de conexiones | Implementar pooling y revisiones periódicas |
| `sessions_by_wait_event_type` en `IO` + `longest_query_time_sec` alto | Consultas lentas bloqueadas esperando disco | Afecta SLA y experiencia de usuario | Indexar, revisar plan de consulta, aumentar IOPS |
| `bloat_percent` alto + `write_iops` alto + `autovacuum_count_user_tables` bajo | Tablas infladas provocan escrituras innecesarias | Alto consumo de disco, riesgo de llenado rápido | Configurar autovacuum agresivo o mantenimiento manual |
| `oldest_transaction_time_sec` alto + `sessions_by_wait_event_type` en 'Lock' | Transacciones antiguas bloqueando recursos | Bloqueos en cascada, timeouts, pérdida de rendimiento | Identificar y finalizar transacciones largas; optimizar lógica de commits |
| `sessions_by_state` en 'idle' alto + `active_connections` alto | Muchas sesiones inactivas pero abiertas | Fugas de conexiones, presión innecesaria sobre el servidor | Usar pooling, cerrar conexiones adecuadamente |
| `logical_replication_delay_in_bytes` alto + `storage_percent` creciendo | Réplica lógica retrasada impide liberación de WAL | Almacenamiento se llena, riesgo de modo read-only | Verificar salud de suscriptores, limpiar slots huérfanos |
| `oldest_transaction_time_sec` alto + `bloat_percent` alto | Transacciones largas impiden limpieza | Bloat no controlado, I/O innecesario y uso de espacio | Ejecutar vacuum, revisar configuración de autovacuum |
| `sessions_by_state` en 'active' alto + `longest_query_time_sec` alto | Muchas sesiones activas ejecutando consultas largas | Contención de CPU y disco, degradación general | Revisar planes de ejecución, optimizar consultas y agregaciones |

---


### Referencias

- [Supported metrics - Microsoft.DBforPostgreSQL/flexibleServers - Azure Monitor | Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/supported-metrics/microsoft-dbforpostgresql-flexibleservers-metrics)
- [Monitoring and metrics - Azure Database for PostgreSQL flexible server | Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-monitoring)
- [Configure alerts - Azure portal - Azure Database for PostgreSQL flexible server | Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-alert-on-metrics)
- [Query Performance Insight - Azure Database for PostgreSQL flexible server | Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-query-performance-insight)
- [High Availability (HA) Health Status Monitoring - Azure Database for PostgreSQL flexible server | Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-monitor-high-availability)
- [Troubleshooting guides - Azure portal - Azure Database for PostgreSQL flexible server | Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-troubleshooting-guides)
- [Track health of PostgreSQL connection pooling with PgBouncer metrics](https://techcommunity.microsoft.com/blog/adforpostgresql/monitoring-pgbouncer-in-azure-postgresql-flexible-server/3762146)
- [Optimize by using pg_repack - Azure Database for PostgreSQL flexible server | Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-perform-fullvacuum-pg-repack)
