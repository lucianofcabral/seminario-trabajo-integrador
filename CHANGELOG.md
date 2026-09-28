# Changelog

Cambios del proyecto por ejercicio. El más reciente está primero.

## [Ejercicio 04]

- Capa de lógica en `services.py`: un servicio por entidad sobre su repositorio, con los repositorios inyectables.
- Integridad referencial: libros, stock, precios y cotizaciones exigen que existan las entidades que referencian.
- No se pueden borrar géneros, editoriales, monedas ni tipos de cotización en uso; borrar un libro borra su stock y sus precios.
- Relaciones entre objetos: editorial, género, stock y precios de un libro; libros de un género o de una editorial.
- `modificar_stock`, `modificar_precio` e histórico de cotizaciones del dólar.

## [Ejercicio 03]

- Las clases de persistencia CSV pasan de `services.py` a `repositories.py`, junto con sus interfaces.
- Interfaces con los nombres de la consigna: `IRepositorioCotizacionDolar` con `leer_por_tipo_y_fecha` y `leer_historico_por_tipo`, y `leer_por_libro` en stock y precios.
- `crear` lanza `ValueError` ante un duplicado (antes devolvía el existente sin avisar) y `actualizar` también controla que no se repitan claves.
- Nuevas consultas para las relaciones: libros por editorial y por género, precios por moneda.
- `csv_config.py` pasa a `repositories/`.

## [Ejercicio 02]

- `EntidadBase`: clase base común que valida los datos al crear y al modificar cada atributo (encapsulamiento).
- `Cotizacion` pasa a llamarse `CotizacionDolar`, como en la consigna.
- Se quitan las listas `libros` de `Genero` y `Editorial`, que nunca se completaban; las relaciones se resuelven en los servicios.
- Validaciones: precio no negativo y cotización mayor a cero.
- La edición en consola valida todos los cambios juntos antes de aplicarlos.

## [Ejercicio 01]

- Versiones mínimas de dependencias más bajas, para usar las que ya trae Colab.
- `uv.lock` regenerado (quita `pycountries`); tests verificados en Python 3.12.

## [Ejercicio 07]

- Punto de entrada que abre la consola.
- `main(import_default_data)` en `main.py`: con True regenera los datos de ejemplo, con False usa los CSV existentes.
- El comando `book-manager` apunta a `book_manager.main:main`.

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
