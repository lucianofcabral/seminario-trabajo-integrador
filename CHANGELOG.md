# Changelog

Todas las modificaciones notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/)
y el proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.1.0] - 2026-09-27

### Añadido

- Entidades Pydantic para libros, editoriales, géneros, stock, precios, monedas,
  tipos de cotización y cotizaciones.
- Repositorios CRUD sobre CSV para las ocho tablas, con unicidad por campo
  (ISBN, código de moneda, proveedor, etc.).
- Interfaz de terminal interactiva: ver, agregar, editar, borrar y buscar en
  cada tabla, con referencias resueltas a texto legible.
- Edición selectiva: al editar se elige qué atributo(s) modificar.
- Generadores de datos de seed (monedas ISO 4217, editoriales, libros, stock,
  precios y cotizaciones).
- Suite de tests con pytest.

### Corregido

- Instanciación de los repositorios de editorial, stock, precio, tipo de
  cotización y cotización.
- Alineación de esquemas entre modelo y CSV (`existencia`, `tipo_cotizacion_id`,
  `valor_pesos`).
- Búsquedas por clave foránea que comparaban strings contra enteros.
- `modificar_stock` y `modificar_precio`, que creaban el registro sin id.
- Búsqueda por texto de género, que comparaba la cadena al revés.
- Firma de `leer_cotizacion` y typo `menda_id` → `moneda_id`.
