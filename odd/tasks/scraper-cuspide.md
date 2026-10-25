# Scraper Cúspide (Sprint 3, Ejercicio 03)

Scraper scrapy (`CuspideSpider`) que busca los libros del catálogo en Cúspide y
persiste precio, url de imagen, formas de pago y descripción en la base.

## Specs

- **S1**: "Implementar un scraper (CuspideSpider) con scrapy que obtenga del sitio de Cúspide los siguientes datos: Precio. url de la img. Formas de pago y precio. Descripción detallada."
- **S2**: "Solo vamos a trabajar con nuestros libros, es decir, solo debo buscar los 10 primeros resultados de cada búsqueda (por título). No puedo buscar libros que no tengo en mi catálogo."
- **S3**: "Implementar: Loaders, Pipelines"

## Tasks

- **T1** (S1): estructura del paquete `scraper/` (items, loaders, pipelines, settings, spiders).
- **T2** (S1, S3): `CuspideItem` + `CuspideLoader` con input/output processors.
- **T3** (S1, S2): `CuspideSpider` — búsqueda por título, 10 primeros resultados, detalle.
- **T4** (S3): pipeline que persiste en la base (`PrecioWeb`).
- **T5** (S1): modelo `PrecioWeb` + repositorio + servicio.
- **T6** (S2): helper de títulos del catálogo (CLI / base / CSV / manual).
- **T7** (S1–S3): tests con HTML mockeado (spider, loaders, pipeline, modelo).
- **T8**: README + CHANGELOG + commit de cierre.

## Log

- **L1**: "Implementar un scraper (CuspideSpider) con scrapy que obtenga del sitio de Cúspide los siguientes datos: Precio. url de la img. Formas de pago y precio. Descripción detallada. Solo vamos a trabajar con nuestros libros, es decir, solo debo buscar los 10 primeros resultados de cada búsqueda (por título). No puedo buscar libros que no tengo en mi catálogo. Implementar: Loaders, Pipelines" (notebook 03, celda Ejercicio 03).
- **L2**: Decisiones: búsqueda por título (endpoint `?s=<titulo>&post_type=product`, NO `/tienda/`); "formas de pago y precio" = medios de pago + precio ARS; salida en base (tabla `PrecioWeb`); fuente del catálogo flexible (CLI / base / CSV / manual).
- **L3**: `PrecioWeb` es un registro de observación generado por el scraper (no editable por el usuario): se modela solo como tabla ORM + `RepoPrecioWebSQL` (sin entidad Pydantic ni interfaz ABC), a diferencia del resto de las entidades CRUD.
