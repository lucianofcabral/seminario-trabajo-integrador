# Changelog

Cambios del proyecto por ejercicio. El más reciente está primero.

## [Ejercicio 07]

- Punto de entrada que abre la consola.

## [Ejercicio 06]

- Interfaz de terminal interactiva: ver, agregar, editar, borrar y buscar en cada tabla, con referencias resueltas a texto legible.
- Edición selectiva: al editar se elige qué atributo(s) modificar.
- Formateo de tablas en texto plano.
- `except` con múltiples excepciones entre paréntesis (compatibilidad con Python 3.12).
- Docstrings en las funciones de la consola.

## [Ejercicio 05]

- Generadores de datos de seed: monedas ISO 4217, géneros, editoriales, libros, stock, precios y cotizaciones.
- Corrección de esquemas entre modelo y CSV (`existencia`, `tipo_cotizacion_id`, `valor_pesos`).
- La precarga de datos pasa a `preload_data/preload_data.py` (`precargar_datos`).
- Diez tipos de cotización (mínimo de 10 registros por clase).
- Las cotizaciones usan todos los tipos de cotización.

## [Ejercicio 04]

- Repositorios CRUD sobre CSV para las ocho tablas, con unicidad por campo (ISBN, código de moneda, proveedor, etc.).
- Corrección de la instanciación de los repositorios de editorial, stock, precio, tipo de cotización y cotización.
- Corrección de búsquedas por clave foránea que comparaban strings contra enteros.
- Corrección de `modificar_stock` y `modificar_precio`, que creaban el registro sin id.
- Corrección de la búsqueda por texto de género y de la firma de `leer_cotizacion`.
- Docstrings y type hints en los repositorios CSV.

## [Ejercicio 03]

- Interfaces (ABC) de repositorio con CRUD para las ocho entidades.
- Docstrings en todos los métodos de las interfaces de repositorio.

## [Ejercicio 02]

- Entidades Pydantic: Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock y Cotizacion.
- `Libro` se define antes que `Genero` y `Editorial`, que lo referencian (compatibilidad con Python 3.12).
- Docstrings en todas las entidades.

## [Ejercicio 01]

- Estructura inicial del proyecto.
- Configuración de build y dependencias con uv.
- Suite de tests con pytest.
- Compatibilidad con Python 3.12 (`requires-python >= 3.12`) para poder ejecutarlo en Colab.
- `requirements.txt` instalable con pip y sin la dependencia sin uso `pycountries`.
- README con el sprint actual, el objetivo y el contexto del sprint.
- CHANGELOG con el formato por ejercicio.
