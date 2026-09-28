# book-manager

**Sprint actual: Sprint 1**

Gestor de libros por terminal. Lleva el registro de libros, editoriales, géneros,
stock y precios en archivos CSV, sin base de datos. CRUD completo desde un menú
interactivo.

## Objetivo

Aplicar los conocimientos adquiridos en programación orientada a objetos y en
almacenamiento de datos en archivos para su persistencia.

## Introducción y contexto

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

- Python 3.12 o superior
- [uv](https://docs.astral.sh/uv/) (opcional; también se puede usar pip)

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

Desde Python (por ejemplo, en el notebook):

```python
from book_manager.main import main
main(import_default_data=False)  # False: usa los CSV existentes sin regenerarlos
```

Al arrancar aparece el menú principal con las tablas. Elegís una con su número y
dentro de cada una tenés:

- **Ver** — listar los registros.
- **Agregar** — cargar uno nuevo.
- **Editar** — elegir qué atributo(s) modificar, no todo el registro.
- **Borrar** — eliminar por id.
- **Buscar** — filtrar por texto.

Las referencias se muestran legibles: al ver un libro ves la editorial y el género
por nombre, no por id.

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
stock y precios aleatorios, diez tipos de cotización y cotizaciones del año 2026.
Los archivos quedan en `src/book_manager/migrations/csv/`.

## Estructura

```
src/book_manager/
  entities/       modelos Pydantic
  repositories/   interfaces (ABC) de repositorios
  services/       implementaciones CRUD sobre CSV
  preload_data/   generación de datos de seed
  migrations/csv/ archivos CSV con los datos
  ui/             consola interactiva y formateo de tablas
  main.py         punto de entrada
```

## Tests

```bash
uv run pytest
```
