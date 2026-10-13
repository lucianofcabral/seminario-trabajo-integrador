# book-manager

**Sprint actual: Sprint 2**

Gestor de libros por terminal. Lleva el registro de libros, editoriales, géneros,
stock y precios en una base de datos relacional (SQLAlchemy sobre PostgreSQL/Supabase),
con migración desde CSV, consultas a la API del dólar y CRUD completo desde un menú
interactivo.

## Objetivo

Aplicar los conocimientos adquiridos en programación orientada a objetos, en bases
de datos relacionales y en consumo de APIs externas, migrando la persistencia en
archivos del Sprint 1 a una base de datos relacional con SQLAlchemy.

## Introducción y contexto

### Sprint 2

En esta entrega se migra la persistencia en archivos CSV a una base de datos
relacional usando SQLAlchemy sobre Supabase (PostgreSQL). Se normalizan las tablas,
se implementa una conexión segura mediante variables de entorno, se precarga la base
desde los CSV del Sprint 1 y se consulta la API del dólar para registrar cotizaciones
y ofrecer precios bimonetarios con exportación a CSV.

### Sprint 1

Una librería con venta al público necesita modernizar su sistema de gestión de
inventario de libros. Debido a la fluctuación en los costos de importación de
material bibliográfico, el sistema debe gestionar precios en diferentes monedas y
seguir de cerca la cotización del dólar para actualizar sus valores.

En este sprint se construye la base: las entidades del dominio, su persistencia en
CSV con CRUD completo, la precarga de datos y la interfaz de consola. Se toma como
referencia el sitio [Cúspide](https://www.cuspide.com/).

Entidades:

- **Libro**: título del catálogo (ISBN, título, autor, editorial, género).
- **Genero**: categoría literaria (novela, ensayo, infantil, técnico, etc.).
- **Editorial**: proveedor o distribuidora que provee los libros.
- **Moneda**: monedas en las que se expresa un precio (ARS, USD, etc.).
- **TipoCotizacion**: tipos de cotización del dólar (Oficial, Blue, MEP, etc.).
- **Precio**: valor de un libro en una moneda determinada.
- **Stock**: cantidad disponible de cada libro.
- **Cotizacion**: registro histórico de cotizaciones por tipo y fecha.

## Requisitos

- Python 3.12 (la misma versión que Colab)
- [uv](https://docs.astral.sh/uv/) (opcional; también se puede usar pip)
- Una base PostgreSQL (Supabase)

## Configuración

- `.env` (versionado): solo `API_URL`, la URL pública de la API del dólar.
- `.env.local` (no versionado): credenciales de la base. Copiá
  `.env.local.example` a `.env.local` y completalo.
- En Colab, las credenciales se cargan desde los secrets del notebook
  (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`). Las variables
  ya definidas nunca se pisan con las de los archivos.

## Instalación

```bash
uv sync
```

o, sin uv:

```bash
pip install -r requirements.txt
```

## Uso

```bash
uv run book-manager
```

Desde Python (por ejemplo, desde el notebook de Colab):

```python
from book_manager.main import main
main(import_default_data=False)  # conserva la base; solo la puebla si está vacía
main(import_default_data=True)   # borra las tablas, regenera los datos de ejemplo y repuebla
```

Al arrancar aparece el menú principal con las tablas y tres acciones: obtener
cotizaciones de la API, ver la lista de precios bimonetaria (USD y pesos al tipo de
dólar elegido) y exportar los precios a `exports/precios.csv` con una columna de
pesos por cada tipo de dólar.

Dentro de cada tabla: 
- **Ver** — listar los registros.
- **Agregar** — cargar uno nuevo.
- **Editar** — elegir qué atributo(s) modificar, no todo el registro.
- **Borrar** — eliminar por id.
- **Buscar** — filtrar por texto.

Las referencias se muestran legibles: al ver un libro ves la editorial y el género
por nombre, no por id.

## Reglas de negocio

- No se repiten ISBN, códigos de moneda, proveedores, géneros ni tipos de cotización;
  tampoco dos precios de un libro en la misma moneda ni dos cotizaciones de un tipo
  en la misma fecha (lo garantiza la base con restricciones únicas).
- Un libro necesita una editorial y un género existentes; stock y precios, un libro
  (y una moneda) existentes; una cotización, un tipo existente.
- No se puede borrar un género, una editorial, una moneda o un tipo de cotización
  que esté en uso.
- Al borrar un libro se borran también su stock y sus precios, en la misma transacción.

## Tablas

| Tabla | Campos |
|-------|--------|
| Libros | ISBN, título, autor, editorial, género |
| Editoriales | proveedor, país, provincia, localidad, domicilio, teléfono, email, responsable |
| Géneros | género |
| Stock | libro, existencia |
| Precios | libro, moneda, valor |
| Monedas | código, nombre |
| Tipos de cotización | tipo (Blue, MEP, Oficial, CCL, Mayorista, Cripto, Tarjeta, Solidario, Blend, Turista) |
| Cotizaciones | tipo, fecha, valor en pesos |

## Datos de ejemplo

Los CSV de seed se generan con:

```bash
uv run python -m book_manager.preload_data.preload_data
```

Incluye monedas según ISO 4217, diez editoriales, diez géneros, treinta libros,
stock y precios aleatorios en USD, diez tipos de cotización y un año de
cotizaciones que termina una semana antes de la generación (así las cotizaciones
reales de la API quedan como las más recientes). Los archivos quedan en
`src/book_manager/migrations/csv/`; la migración genera los `.sql` en
`src/book_manager/migrations/sql/`.

## Estructura

```
src/book_manager/
  database/       ConexionDB y context manager de transacciones
  entities/       entidades (Pydantic) con validación al crear y al modificar
  models/         tablas ORM (SQLAlchemy) con tipos, relaciones y restricciones
  repositories/   interfaces (ABC) e implementación sobre SQLAlchemy
  services/       lógica de negocio, API del dólar y reportes de precios
  preload_data/   generación de los datos de ejemplo
  migrations/     CSV del TP1, .sql generados y la migración
  ui/             consola interactiva y formateo de tablas
  utils.py        funciones auxiliares compartidas
  main.py         punto de entrada
tests/            tests con pytest (sobre SQLite)
```

La consola usa los servicios, los servicios usan los repositorios y los
repositorios usan los modelos ORM sobre la base. Cada capa depende solo de la de
abajo.

## Tests

```bash
uv run pytest
```
