# Comparación de precios y alertas (Sprint 3, Ejercicio 04)

Compara el precio interno (USD) de cada libro contra el precio web de Cúspide
(ARS) y genera un CSV de alertas cuando la diferencia supera un umbral que
ingresa el usuario antes de cada corrida del scraper.

## Specs

- **S1**: "Comparar el precio interno con el precio web y generar alertas."
- **S2**: "Cada vez que se ejecuta el scraper se debe generar un archivo de alertas del tipo CSV que se debe poder descargar para analizar los precios."
- **S3**: "La diferencia de precios debe ser ingresada por el usuario antes de cada ejecución del scraper."

## Tasks

- **T1** (S1): servicio de comparación: precio interno (USD) → ARS con la última cotización "Oficial" (`valor_venta`), contra el último `precio_web` (ARS) por libro; `diferencia = precio_web - precio_interno`.
- **T2** (S1, S3): umbral como parámetro de la ejecución; alerta cuando `abs(diferencia) > umbral` (umbral en pesos).
- **T3** (S2): exportar alertas a CSV en `exports/` (columnas: isbn, titulo, precio_interno, precio_web, diferencia, fecha_extraccion).
- **T4** (S1, S2): integrar en `ejecutar_scraping`: tras el crawl, generar el CSV de alertas (el prompt interactivo del umbral lo aporta el menú del Ej 07).
- **T5**: tests de la comparación, el umbral, el CSV y la integración (sin red).
- **T6**: README + CHANGELOG + commit de cierre.

## Log

- **L1**: "Comparar el precio interno con el precio web y generar alertas. Cada vez que se ejecuta el scraper se debe generar un archivo de alertas del tipo CSV que se debe poder descargar para analizar los precios. La diferencia de precios debe ser ingresada por el usuario antes de cada ejecución del scraper." (notebook 03, celda Ejercicio 04).
- **L2**: Decisiones: comparación en ARS (interno USD → ARS con cotización "Oficial", `valor_venta`); `diferencia = precio_web - precio_interno` (con signo); alerta si `abs(diferencia) > umbral`; umbral en pesos; CSV en `exports/alertas_precios.csv`; la entrada interactiva del umbral la agrega el menú del Ej 07.
- **L3**: Migración previa: la tabla `cotizacion` en Supabase quedó con esquema viejo (`valor_pesos`) tras la corrección 982eb27; se migró in-place a `valor_compra` + `valor_venta` (NUMERIC(12,2)) antes de este ejercicio.
- **L4**: Decisión de arquitectura (por qué sobre la base): el precio web ya vive en `precio_web` (pipeline del Ej 03), el precio interno y la cotización ya son tablas, y el Ej 05 pide `fecha_extraccion`, que exige histórico persistido. Comparar en memoria sería un retroceso frente al Sprint 2 (todo SQLAlchemy/Supabase).
- **L5**: Nota de diseño (claves): el ISBN es la clave natural del dominio (identidad en `entities.py`, `unique=True` en `libro`), pero la PK física es el `id` subrogado. El scraper matchea por `libro_id` (subrogado, viaja por `cb_kwargs`), no por ISBN, para no depender del ISBN scrapeado de la página.
