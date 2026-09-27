# book-manager

Gestor de libros por terminal. Lleva el registro de libros, editoriales, géneros,
stock y precios en archivos CSV, sin base de datos. CRUD completo desde un menú
interactivo.

## Requisitos

- Python 3.14
- [uv](https://docs.astral.sh/uv/)

## Instalación

```bash
uv sync
```

## Uso

```bash
uv run book-manager
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
| Tipos de cotización | tipo (Blue, MEP, Oficial) |
| Cotizaciones | tipo, fecha, valor en pesos |

## Datos de ejemplo

Los CSV de seed se generan con:

```bash
uv run python -m book_manager.migrations.migrations
```

Incluye monedas según ISO 4217, diez editoriales, treinta libros, stock y precios
aleatorios, y cotizaciones del año 2026. Los archivos quedan en
`src/book_manager/migrations/csv/`.

## Estructura

```
src/book_manager/
  entities/       modelos Pydantic
  repositories/   interfaces (ABC) de repositorios
  services/       implementaciones CRUD sobre CSV
  migrations/     generación de datos de seed
  ui/             consola interactiva y formateo de tablas
```

## Tests

```bash
uv run pytest
```
