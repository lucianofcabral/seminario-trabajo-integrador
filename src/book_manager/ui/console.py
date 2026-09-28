from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel, ValidationError

from book_manager.entities.entities import (
    Cotizacion,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.services.services import (
    RepoCotizacionCSV,
    RepoEditorialCSV,
    RepoGeneroCSV,
    RepoLibroCSV,
    RepoMonedaCSV,
    RepoPrecioCSV,
    RepoStock,
    RepoTipoCotizacionCSV,
)
from book_manager.ui.formatting import render_tabla


@dataclass(frozen=True)
class Campo:
    """Un campo editable de una tabla."""

    clave: str
    etiqueta: str
    tipo: str  # "str" | "int" | "float" | "fecha" | "fk"
    fk_tabla: str | None = None  # clave de la tabla referenciada (tipo "fk")


@dataclass(frozen=True)
class Tabla:
    """Descriptor de una tabla: modelo, repo, campos y columnas de vista."""

    clave: str
    etiqueta: str  # plural, p.ej. "Libros"
    singular: str  # p.ej. "libro"
    modelo: type[BaseModel]
    fabrica_repo: Callable[[], Any]
    campos: tuple[Campo, ...]
    columnas: tuple[tuple[str, str], ...]  # (clave, etiqueta) de la vista
    texto: Callable[[Any], str]  # representación para cuando otra tabla la referencia


TABLAS: list[Tabla] = [
    Tabla(
        clave="libro",
        etiqueta="Libros",
        singular="libro",
        modelo=Libro,
        fabrica_repo=RepoLibroCSV,
        campos=(
            Campo("isbn", "ISBN", "str"),
            Campo("titulo", "Título", "str"),
            Campo("autor", "Autor", "str"),
            Campo("editorial_id", "Editorial", "fk", "editorial"),
            Campo("genero_id", "Género", "fk", "genero"),
        ),
        columnas=(
            ("id", "ID"),
            ("isbn", "ISBN"),
            ("titulo", "Título"),
            ("autor", "Autor"),
            ("editorial_id", "Editorial"),
            ("genero_id", "Género"),
        ),
        texto=lambda e: e.titulo,
    ),
    Tabla(
        clave="editorial",
        etiqueta="Editoriales",
        singular="editorial",
        modelo=Editorial,
        fabrica_repo=RepoEditorialCSV,
        campos=(
            Campo("proveedor", "Proveedor", "str"),
            Campo("pais", "País", "str"),
            Campo("provincia", "Provincia", "str"),
            Campo("localidad", "Localidad", "str"),
            Campo("domicilio", "Domicilio", "str"),
            Campo("telefono", "Teléfono", "str"),
            Campo("email", "Email", "str"),
            Campo("responsable", "Responsable", "str"),
        ),
        columnas=(
            ("id", "ID"),
            ("proveedor", "Proveedor"),
            ("pais", "País"),
            ("localidad", "Localidad"),
            ("telefono", "Teléfono"),
            ("email", "Email"),
            ("responsable", "Responsable"),
        ),
        texto=lambda e: e.proveedor,
    ),
    Tabla(
        clave="genero",
        etiqueta="Géneros",
        singular="género",
        modelo=Genero,
        fabrica_repo=RepoGeneroCSV,
        campos=(Campo("genero", "Género", "str"),),
        columnas=(("id", "ID"), ("genero", "Género")),
        texto=lambda e: e.genero,
    ),
    Tabla(
        clave="stock",
        etiqueta="Stock",
        singular="stock",
        modelo=Stock,
        fabrica_repo=RepoStock,
        campos=(
            Campo("libro_id", "Libro", "fk", "libro"),
            Campo("existencia", "Existencia", "int"),
        ),
        columnas=(
            ("id", "ID"),
            ("libro_id", "Libro"),
            ("existencia", "Existencia"),
        ),
        texto=lambda e: f"#{e.id}",
    ),
    Tabla(
        clave="precio",
        etiqueta="Precios",
        singular="precio",
        modelo=Precio,
        fabrica_repo=RepoPrecioCSV,
        campos=(
            Campo("libro_id", "Libro", "fk", "libro"),
            Campo("moneda_id", "Moneda", "fk", "moneda"),
            Campo("valor", "Valor", "float"),
        ),
        columnas=(
            ("id", "ID"),
            ("libro_id", "Libro"),
            ("moneda_id", "Moneda"),
            ("valor", "Valor"),
        ),
        texto=lambda e: f"#{e.id}",
    ),
    Tabla(
        clave="moneda",
        etiqueta="Monedas",
        singular="moneda",
        modelo=Moneda,
        fabrica_repo=RepoMonedaCSV,
        campos=(
            Campo("codigo", "Código", "str"),
            Campo("nombre", "Nombre", "str"),
        ),
        columnas=(("id", "ID"), ("codigo", "Código"), ("nombre", "Nombre")),
        texto=lambda e: e.codigo,
    ),
    Tabla(
        clave="tipo_cotizacion",
        etiqueta="Tipos de cotización",
        singular="tipo de cotización",
        modelo=TipoCotizacion,
        fabrica_repo=RepoTipoCotizacionCSV,
        campos=(Campo("tipo", "Tipo", "str"),),
        columnas=(("id", "ID"), ("tipo", "Tipo")),
        texto=lambda e: e.tipo,
    ),
    Tabla(
        clave="cotizacion",
        etiqueta="Cotizaciones",
        singular="cotización",
        modelo=Cotizacion,
        fabrica_repo=RepoCotizacionCSV,
        campos=(
            Campo("tipo_cotizacion_id", "Tipo", "fk", "tipo_cotizacion"),
            Campo("fecha", "Fecha (AAAA-MM-DD)", "fecha"),
            Campo("valor_pesos", "Valor en pesos", "float"),
        ),
        columnas=(
            ("id", "ID"),
            ("tipo_cotizacion_id", "Tipo"),
            ("fecha", "Fecha"),
            ("valor_pesos", "Valor (ARS)"),
        ),
        texto=lambda e: f"#{e.id}",
    ),
]

CATALOGO: dict[str, Tabla] = {t.clave: t for t in TABLAS}


# --- resolución de referencias ---


def _campo_de(tabla: Tabla, clave: str) -> Campo | None:
    """Busca en la tabla el campo editable con esa clave, o None si no existe."""
    for campo in tabla.campos:
        if campo.clave == clave:
            return campo
    return None


def _resolver_fk(clave_tabla: str, entidad_id: Any) -> str:
    """Devuelve el texto legible de una referencia (id -> texto de la entidad)."""
    tabla = CATALOGO[clave_tabla]
    try:
        entidad = tabla.fabrica_repo().leer_por_id(int(entidad_id))
    except (TypeError, ValueError):
        return str(entidad_id)
    if entidad is None:
        return str(entidad_id)
    return tabla.texto(entidad)


def _entidad_a_fila(tabla: Tabla, entidad: Any) -> dict:
    """Convierte una entidad en un dict de vista, resolviendo referencias."""
    fila: dict[str, Any] = {}
    for clave, _ in tabla.columnas:
        if clave == "id":
            fila["id"] = entidad.id
            continue
        campo = _campo_de(tabla, clave)
        valor = getattr(entidad, clave, None)
        if campo is not None and campo.tipo == "fk":
            fila[clave] = _resolver_fk(campo.fk_tabla, valor)
        else:
            fila[clave] = valor
    return fila


def _contar(tabla: Tabla, n: int) -> str:
    """Arma el texto de conteo en singular o plural, p. ej. "3 libros"."""
    palabra = tabla.singular if n == 1 else tabla.etiqueta.lower()
    return f"{n} {palabra}"


# --- entrada del usuario ---


def _pedir_opcion(maximo: int) -> int:
    """Pide una opción de menú hasta que sea un entero entre 0 y `maximo`."""
    while True:
        raw = input("> ").strip()
        try:
            opcion = int(raw)
        except ValueError:
            print(f"Ingresá un número entre 0 y {maximo}.")
            continue
        if 0 <= opcion <= maximo:
            return opcion
        print(f"Ingresá un número entre 0 y {maximo}.")


def _pedir_seleccion(maximo: int) -> list[int] | None:
    """Pide uno o varios números (separados por coma). None si cancela."""
    while True:
        raw = input("Campos (números separados por coma): ").strip()
        if raw in ("", "0"):
            return None
        partes = raw.replace(",", " ").split()
        seleccion: list[int] = []
        valido = True
        for parte in partes:
            try:
                n = int(parte)
            except ValueError:
                valido = False
                break
            if not 1 <= n <= maximo:
                valido = False
                break
            seleccion.append(n)
        if valido and seleccion:
            return seleccion
        print(f"Ingresá números entre 1 y {maximo} separados por coma.")


def _texto_actual(actual: Any) -> str:
    """Texto de un valor para mostrarlo como sugerencia entre corchetes."""
    if isinstance(actual, date):
        return actual.isoformat()
    return str(actual)


def _valor_actual(campo: Campo, entidad: Any) -> str:
    """Texto legible del valor actual de un campo (resuelve referencias)."""
    valor = getattr(entidad, campo.clave)
    if campo.tipo == "fk":
        return _resolver_fk(campo.fk_tabla, valor)
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


def _pedir_fk(campo: Campo, actual: Any = None) -> Any:
    """Lista las opciones de la tabla referenciada y pide un id válido.

    Args:
        campo: Campo de tipo "fk".
        actual: Id actual; se devuelve si el usuario deja la entrada vacía.

    Returns:
        El id elegido, o `actual` si no se eligió ninguno.
    """
    tabla = CATALOGO[campo.fk_tabla]
    opciones = tabla.fabrica_repo().leer_todos()
    if not opciones:
        print(f"No hay {tabla.etiqueta.lower()} cargados.")
        return actual

    print()
    for e in opciones:
        print(f"  {e.id}. {tabla.texto(e)}")

    sufijo = f" [{actual}]" if actual is not None else ""
    while True:
        raw = input(f"{campo.etiqueta} (id){sufijo}: ").strip()
        if raw == "":
            return actual
        try:
            elegido = int(raw)
        except ValueError:
            print("Debe ser un número.")
            continue
        if any(e.id == elegido for e in opciones):
            return elegido
        print("Ese id no existe.")


def _pedir_campo(campo: Campo, actual: Any = None) -> Any:
    """Pide un valor por teclado. Devuelve None si el usuario cancela."""
    if campo.tipo == "fk":
        return _pedir_fk(campo, actual)

    sufijo = f" [{_texto_actual(actual)}]" if actual is not None else ""

    if campo.tipo == "fecha":
        while True:
            raw = input(f"{campo.etiqueta}{sufijo}: ").strip()
            if raw == "":
                return actual
            try:
                return date.fromisoformat(raw)
            except ValueError:
                print("Fecha inválida. Usá AAAA-MM-DD.")
    elif campo.tipo == "int":
        while True:
            raw = input(f"{campo.etiqueta}{sufijo}: ").strip()
            if raw == "":
                return actual
            try:
                return int(raw)
            except ValueError:
                print("Debe ser un número entero.")
    elif campo.tipo == "float":
        while True:
            raw = input(f"{campo.etiqueta}{sufijo}: ").strip()
            if raw == "":
                return actual
            try:
                return float(raw.replace(",", "."))
            except ValueError:
                print("Debe ser un número.")
    else:
        raw = input(f"{campo.etiqueta}{sufijo}: ").strip()
        if raw == "":
            return actual
        return raw


def _pedir_campos(tabla: Tabla, entidad: Any = None) -> dict | None:
    """Pide todos los campos editables. Devuelve None si el usuario cancela."""
    datos: dict[str, Any] = {}
    for campo in tabla.campos:
        actual = getattr(entidad, campo.clave, None) if entidad is not None else None
        valor = _pedir_campo(campo, actual)
        if valor is None:
            return None
        datos[campo.clave] = valor
    return datos


def _pedir_id() -> int | None:
    """Pide un id numérico. Devuelve None si el usuario deja la entrada vacía."""
    while True:
        raw = input("ID: ").strip()
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print("Debe ser un número.")


def _mostrar_error_validacion(error: ValidationError) -> None:
    """Muestra el primer error de validación de Pydantic en lenguaje simple."""
    errores = error.errors()
    if not errores:
        print("Datos inválidos.")
        return
    primero = errores[0]
    campo = ".".join(str(p) for p in primero.get("loc", []))
    print(f"Dato inválido en '{campo}': {primero.get('msg', '')}")


# --- operaciones CRUD ---


def _ver(tabla: Tabla) -> None:
    """Lista todos los registros de la tabla."""
    entidades = tabla.fabrica_repo().leer_todos()
    if not entidades:
        print("No hay nada cargado.")
        return
    filas = [_entidad_a_fila(tabla, e) for e in entidades]
    print()
    print(render_tabla(filas, tabla.columnas))
    print(_contar(tabla, len(entidades)) + ".")


def _crear(tabla: Tabla) -> None:
    """Pide los datos de un registro nuevo, lo valida y lo guarda."""
    datos = _pedir_campos(tabla)
    if datos is None:
        print("Cancelado.")
        return
    try:
        entidad = tabla.modelo(**datos)
    except ValidationError as error:
        _mostrar_error_validacion(error)
        return
    creada = tabla.fabrica_repo().crear(entidad)
    if creada is None:
        print("No se pudo guardar.")
    else:
        print("Quedó guardado.")


def _editar(tabla: Tabla) -> None:
    """Edita solo los campos que elija el usuario de un registro existente."""
    repo = tabla.fabrica_repo()
    if not repo.leer_todos():
        print("No hay nada cargado.")
        return

    _ver(tabla)
    entidad_id = _pedir_id()
    if entidad_id is None:
        return
    entidad = repo.leer_por_id(entidad_id)
    if entidad is None:
        print("No existe ese id.")
        return

    campos = list(tabla.campos)
    print()
    for i, campo in enumerate(campos, start=1):
        print(f"  {i}. {campo.etiqueta}: {_valor_actual(campo, entidad)}")

    seleccion = _pedir_seleccion(len(campos))
    if seleccion is None:
        print("Cancelado.")
        return

    for indice in seleccion:
        campo = campos[indice - 1]
        valor = _pedir_campo(campo, getattr(entidad, campo.clave))
        if valor is not None:
            setattr(entidad, campo.clave, valor)

    datos = {campo.clave: getattr(entidad, campo.clave) for campo in campos}
    datos["id"] = entidad.id
    try:
        nueva = tabla.modelo(**datos)
    except ValidationError as error:
        _mostrar_error_validacion(error)
        return

    repo.actualizar(nueva)
    print("Quedó guardado.")


def _eliminar(tabla: Tabla) -> None:
    """Borra un registro por id, previa confirmación."""
    repo = tabla.fabrica_repo()
    if not repo.leer_todos():
        print("No hay nada cargado.")
        return

    _ver(tabla)
    entidad_id = _pedir_id()
    if entidad_id is None:
        return
    if repo.leer_por_id(entidad_id) is None:
        print("No existe ese id.")
        return

    confirmar = input(f"¿Borrar el registro {entidad_id}? (s/N): ").strip().lower()
    if confirmar in ("s", "si", "sí"):
        repo.eliminar(entidad_id)
        print("Borrado.")
    else:
        print("Cancelado.")


def _buscar(tabla: Tabla) -> None:
    """Muestra los registros que contienen el texto en alguna columna."""
    texto = input("Buscar: ").strip()
    if not texto:
        return

    entidades = tabla.fabrica_repo().leer_todos()
    texto_l = texto.lower()
    coincidencias = [
        e
        for e in entidades
        if any(
            texto_l in str(valor).lower()
            for valor in _entidad_a_fila(tabla, e).values()
        )
    ]

    if not coincidencias:
        print("No encontré nada.")
        return

    filas = [_entidad_a_fila(tabla, e) for e in coincidencias]
    print()
    print(render_tabla(filas, tabla.columnas))
    print(_contar(tabla, len(coincidencias)) + ".")


# --- menús ---


def _menu_tabla(tabla: Tabla) -> None:
    """Menú CRUD de una tabla: ver, agregar, editar, borrar y buscar."""
    while True:
        print()
        print(tabla.etiqueta)
        print("  1. Ver")
        print("  2. Agregar")
        print("  3. Editar")
        print("  4. Borrar")
        print("  5. Buscar")
        print("  0. Volver")

        opcion = _pedir_opcion(5)
        if opcion == 0:
            return
        if opcion == 1:
            _ver(tabla)
        elif opcion == 2:
            _crear(tabla)
        elif opcion == 3:
            _editar(tabla)
        elif opcion == 4:
            _eliminar(tabla)
        elif opcion == 5:
            _buscar(tabla)


def _menu_principal() -> None:
    """Menú principal con la lista de tablas."""
    claves = [t.clave for t in TABLAS]
    while True:
        print()
        for i, tabla in enumerate(TABLAS, start=1):
            print(f"  {i}. {tabla.etiqueta}")
        print("  0. Salir")

        opcion = _pedir_opcion(len(TABLAS))
        if opcion == 0:
            print("Chau.")
            return
        _menu_tabla(CATALOGO[claves[opcion - 1]])


def main() -> None:
    """Punto de entrada de la aplicación de consola."""
    try:
        _menu_principal()
    except (KeyboardInterrupt, EOFError):
        print()
        print("Chau.")
