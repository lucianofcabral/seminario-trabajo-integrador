# Auditoría del sistema (Sprint 3, Ejercicio 06)

Decorador que registra en una tabla `auditoria` cada operación que modifica el
sistema (y las acciones del sistema), con acción, fecha y detalles.

## Specs

- **S1**: "Crear un decorador para manejar las auditorias del sistema, cada operación debe estar auditada."
- **S2**: "La tabla de auditoria debe registrar: acción, fecha, detalles."

## Tasks

- **T1** (S2): modelo `Auditoria` (tabla `auditoria`: `accion`, `fecha`, `detalles`) + `RepoAuditoriaSQL`.
- **T2** (S1): decorador `@auditar` en `services/auditoria.py` que, tras ejecutar la operación, registra una entrada (no-op si la auditoría no está configurada).
- **T3** (S1): aplicar `@auditar` a las mutaciones (`ServicioBase.crear/actualizar/eliminar`) y a las acciones del sistema (`obtener_cotizaciones`, `ejecutar_scraping`, `generar_reporte`).
- **T4**: `ServicioAuditoria` para leer el historial (lo consume el menú del Ej 07) + `configurar_auditoria()` conectada en `main.py`.
- **T5**: tests sin red de la auditoría (registro de acción/fecha/detalles y no-op sin configurar).
- **T6**: README + CHANGELOG + commit de cierre.

## Log

- **L1**: "Crear un decorador para manejar las auditorias del sistema, cada operación debe estar auditada. Modificar todo lo necesario. La tabla de auditoria debe registrar: acción, fecha, detalles." (notebook 03, celda Ejercicio 06).
- **L2**: Alcance decidido con el usuario: auditar **mutaciones** (`crear`, `actualizar`, `eliminar` — `modificar_stock`/`modificar_precio` pasan por `actualizar`) y **acciones del sistema** (`obtener_cotizaciones`, `ejecutar_scraping`, `generar_reporte`). Las lecturas quedan fuera.
- **L3**: Diseño: la auditoría usa un repo a nivel de módulo configurado con `configurar_auditoria(conexion)`; si no se configura, el decorador es no-op (no rompe tests ni usos standalone).
