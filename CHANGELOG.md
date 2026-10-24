# Changelog

Cambios del proyecto por ejercicio. El más reciente está primero.

## [Correcciones]

- **Ej 02** — Manejo de error de conexión: `ConexionDB` lanza `ErrorConexion` con mensaje claro cuando falta una variable de entorno, `DB_PORT` no es numérico o la base no responde al conectar, en lugar de un `KeyError` o un traceback de SQLAlchemy.
- **Ej 07** — La cotización guarda compra y venta: `cotizacion.valor_pesos` se renombra a `valor_venta` y se agrega `valor_compra`. `obtener_cotizaciones` registra ambos valores y descarta las casas sin compra o sin venta. CSV, SQL y precarga de ejemplo regenerados.

## [Ejercicio 01]

- README al día con el Sprint 2: configuración (`.env`, `.env.local` y secrets de Colab), menú de reportes, reglas de unicidad y estructura sobre SQLAlchemy.
- Descripción de `pyproject.toml` actualizada (ya no es almacenamiento en CSV).
- `.python-version` en 3.12, la misma versión que Colab, para probar localmente con el mismo intérprete de la entrega.

## [Ejercicio 08]

- Lista bimonetaria por tipo de dólar: se elige un tipo (Oficial, Blue, MEP, ...) con su última cotización y se muestra cada libro en USD y en pesos a ese dólar. Antes ofrecía 178 monedas y solo convertía USD/ARS.
- Exportación a CSV con una columna `ARS <tipo>` por cada tipo de dólar con cotización, además de la moneda y el valor original.
- Nuevo `ServicioListaPrecios` con la lógica de los reportes (la consola solo muestra): lee precios y cotizaciones con una consulta por tabla (de ~150 consultas a menos de 10).
- El CSV se exporta a `exports/precios.csv` en la raíz del proyecto, ignorado por git.
- La opción de la API muestra las cotizaciones registradas y solo captura errores de red.
- Tests de la lista bimonetaria, la exportación y la conversión ARS→USD.

## [Ejercicio 07]

- `.env` versionado con `API_URL` únicamente, como pide la consigna; las credenciales de la base pasan a `.env.local` (ignorado) o a los secrets de Colab.
- `.env.example` renombrado a `.env.local.example`.
- `utils.cargar_entorno()` centraliza `load_dotenv` (antes repetido en conexión y servicios); nunca pisa variables ya definidas.
- La fecha de cada cotización se toma en hora argentina (`utils.fecha_argentina`): después de las 21 h la API ya informa el día siguiente en UTC.
- Se ignoran las casas sin valor de venta.
- Tests de zona horaria, idempotencia, casas sin venta y carga de `API_URL`.

## [Ejercicio 06]

- Listados ordenados por id: editar un registro ya no lo mueve de fila (la consola elige por número de fila).
- `RepoSqlBase` con `@abstractmethod`, type hints en los hooks y helpers `_listar` / `_leer_uno` que reemplazan los `leer_por_*` repetidos.
- `_id_por_clave` reemplaza los cinco `_id_*` casi idénticos.
- Nuevo `utils.py` con `normalizar_codigo`, usado por la entidad `Moneda` y los repositorios.
- Borrar un libro es atómico: el stock y los precios se borran por cascada en la misma transacción (antes eran tres transacciones).
- `leer_ultima_por_tipo` y `leer_ultimas` en el repositorio de cotizaciones: la última cotización se pide con una consulta en lugar de traer todo el histórico.
- Tests de orden estable, precio duplicado y últimas cotizaciones.

## [Ejercicio 05]

- `poblar_base_de_datos` corre todo en una sola transacción: si falla una tabla, la base no queda a medio poblar.
- Reseteo de secuencias con `setval(..., MAX(id) + 1, false)`, correcto también con tablas vacías.
- Cotizaciones de ejemplo: una por día durante los últimos 365 días, terminando una semana antes de hoy (antes llegaban a fin de 2026 y pisaban a la cotización real de la API, que para algunos tipos viene con días de atraso).
- `cotizacion.csv` y `cotizacion.sql` regenerados.
- Tests de atomicidad de la carga y de fechas de las cotizaciones de ejemplo.

## [Ejercicio 04]

- `UniqueConstraint` en `precio (libro_id, moneda_id)` y en `cotizacion (tipo_cotizacion_id, fecha)`: la base rechaza duplicados aunque se salteen los servicios.
- Montos (`precio.valor`, `cotizacion.valor_pesos`) como `Numeric(12, 2)` en lugar de `Float`.
- `cascade="all, delete-orphan"` en `Libro.stock` y `Libro.precios`: borrar un libro borra su stock y precios en la misma transacción.
- Tests de unicidad y de borrado en cascada en `tests/test_models.py`.

## [Ejercicio 08]

- Menú principal con 3 opciones nuevas: obtener cotizaciones por API, precios bimonetarios y exportar precios a CSV.
- `_precio_en`: conversión entre USD y ARS usando la última cotización (Oficial o Blue).
- `_exportar_precios_csv`: exporta un pivote libros × monedas presentes.
- `ServicioPrecio.leer_por_libro` expuesto para los reportes.
- Tests en `tests/test_console.py`.

## [Ejercicio 07]

- `requests` como dependencia para consumir la API del dólar.
- `ServicioCotizacionDolar.obtener_cotizaciones()`: descarga desde `API_URL` (`.env`), crea los tipos que falten y registra una cotización por tipo (idempotente).
- Mapeo de `casa` de la API (oficial, blue, bolsa, contadoconliqui, ...) a los tipos del dominio.
- `API_URL` se lee de `.env` con un default público si no está configurada.
- Test en `tests/test_services.py`.

## [Ejercicio 06]

- Entidades sin `id`: la identidad es la clave natural (ISBN, código, proveedor, género, tipo) y las relaciones son referencias a objetos (`Libro.editorial` es un `Editorial`).
- Puertos (interfaces) con claves naturales en `repositories/repositories.py`.
- Adaptador SQL en `repositories/sql_repository.py`: mapea entidad ↔ modelo ORM y resuelve FKs por clave natural.
- Retirada la implementación CSV de repos; la migración lee los CSV directamente.
- Servicios y consola cableados a SQL, con selección por número de fila en lugar de id.
- `main.py` conecta a Supabase, puebla si está vacía y abre la consola.
- Reseteo de secuencias PostgreSQL tras la migración (ids explícitos).
- Tests reescritos para SQL (SQLite) y claves naturales.

## [Ejercicio 05]

- `migrations/migrations.py`: `migrar_datos(carpeta_csvs, carpeta_sqls)` lee los CSV del TP1 y genera un `.sql` con los INSERT por tabla.
- `poblar_base_de_datos(conexion, carpeta_sqls)`: crea las tablas y ejecuta los `.sql` en orden de dependencias (FK).
- `.sql` generados y almacenados en `migrations/sql/`.
- Tests en `tests/test_migrations.py`.

## [Ejercicio 04]

- Modelos ORM en `models/models.py`: 8 tablas con `Base` declarativa (SQLAlchemy 2.0, `Mapped`/`mapped_column`).
- Tipos y restricciones: `unique` en ISBN, código de moneda, proveedor, género y tipo de cotización.
- Relaciones: libro↔editorial, libro↔género, libro↔stock (1:1), libro↔precios, moneda↔precios, tipo de cotización↔cotizaciones.
- Tests en `tests/test_models.py`.

## [Ejercicio 03]

- Context manager `transaccion()` en `database/connection.py`: commit al salir sin error, rollback ante excepción y cierre de la sesión.
- Tests de commit y rollback en `tests/test_connection.py`.

## [Ejercicio 02]

- `ConexionDB` en `database/connection.py`: motor y fábrica de sesiones con SQLAlchemy.
- URL de conexión construida desde variables de entorno (`.env`) con `sslmode=require`.
- Tests de la conexión en `tests/test_connection.py`.

## [Ejercicio 01]

- Rama `Sprint_2` creada desde `Sprint_1`.
- Estructura del Sprint 2: paquetes `database/` y `models/`, carpeta `migrations/sql/` y `.env.example`.
- Dependencias: `sqlalchemy`, `python-dotenv` y `psycopg[binary]`.
- README actualizado al Sprint 2 con objetivo y contexto.

## [Ejercicio 05]

- Corrección del autor del libro 23 ("Órbita rota") en `libro.csv`.
- `preload_data.py`: imports ordenados y el `except` al generar monedas captura solo `KeyError` y `ValueError`.

## [Ejercicio 01]

- Se quita el notebook del repositorio: la entrega se arma en Colab.

## [Ejercicio 01]

- Notebook de entrega `01_Book_Manager_Grupo_XX.ipynb` sobre la plantilla: celda de librerías, clonado en la rama `Sprint_1` y una celda con título por ejercicio.
- README con la arquitectura en capas y las reglas de negocio.
- `.gitignore` ignora los checkpoints de Jupyter.

## [Ejercicio 07]

- `main()` ya no pisa los datos por defecto (`import_default_data=False`); los CSV que falten se generan igual con los datos de ejemplo.
- `main(import_default_data=True)` regenera todos los datos de ejemplo.

## [Ejercicio 06]

- La consola opera a través de los servicios, así las reglas de negocio se aplican también desde el menú.
- Los rechazos (duplicados, referencias inexistentes, registros en uso) se muestran con su motivo en lugar de cortar el programa.
- Los tests usan siempre CSV temporales y nunca tocan los datos reales.

## [Ejercicio 05]

- Los precios buscan el id del dólar por su código `USD` en lugar de usar el id 145 fijo.
- Test que verifica que la precarga completa tenga al menos 10 registros por tabla y referencias válidas.

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
