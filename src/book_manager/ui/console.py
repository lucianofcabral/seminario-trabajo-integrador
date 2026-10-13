"""Interfaz de consola interactiva, cableada a los servicios SQL.

Cada tabla se describe con sus campos editables y su clave natural. Las
referencias entre entidades se muestran y piden como objetos completos, no por id.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, ValidationError

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.rutas import EXPORTS_FOLDER_PATH
from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioListaPrecios,
    ServicioMoneda,
    ServicioPrecio,
    ServicioStock,
    ServicioTipoCotizacion,
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
    """Descriptor de una tabla: modelo, servicio, campos y columnas de vista."""

    clave: str
    etiqueta: str  # plural, p.ej. "Libros"
    singular: str  # p.ej. "libro"
    modelo: type[BaseModel]
    fabrica_servicio: Callable[[], Any]
    campos: tuple[Campo, ...]
    columnas: tuple[tuple[str, str], ...]  # (clave, etiqueta) de la vista
    texto: Callable[[Any], str]  # representación legible de una entidad
    clave_de: Callable[[Any], object]  # clave natural de una entidad


CATALOGO: dict[str, Tabla] = {}


def _construir_tablas(conexion: ConexionDB) -> list[Tabla]:
    """Arma los descriptores de tabla con los servicios cableados a `conexion`."""

    def fabrica(servicio_cls: type) -> Callable[[], Any]:
        return lambda: servicio_cls(conexion=conexion)

    return [
        Tabla(
            clave="libro",
            etiqueta="Libros",
            singular="libro",
            modelo=Libro,
            fabrica_servicio=fabrica(ServicioLibro),
            campos=(
                Campo("isbn", "ISBN", "str"),
                Campo("titulo", "Título", "str"),
                Campo("autor", "Autor", "str"),
                Campo("editorial", "Editorial", "fk", "editorial"),
                Campo("genero", "Género", "fk", "genero"),
            ),
            columnas=(
                ("isbn", "ISBN"),
                ("titulo", "Título"),
                ("autor", "Autor"),
                ("editorial", "Editorial"),
                ("genero", "Género"),
            ),
            texto=lambda e: e.titulo,
            clave_de=lambda e: e.isbn,
        ),
        Tabla(
            clave="editorial",
            etiqueta="Editoriales",
            singular="editorial",
            modelo=Editorial,
            fabrica_servicio=fabrica(ServicioEditorial),
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
                ("proveedor", "Proveedor"),
                ("pais", "País"),
                ("localidad", "Localidad"),
                ("telefono", "Teléfono"),
                ("email", "Email"),
            ),
            texto=lambda e: e.proveedor,
            clave_de=lambda e: e.proveedor,
        ),
        Tabla(
            clave="genero",
            etiqueta="Géneros",
            singular="género",
            modelo=Genero,
            fabrica_servicio=fabrica(ServicioGenero),
            campos=(Campo("genero", "Género", "str"),),
            columnas=(("genero", "Género"),),
            texto=lambda e: e.genero,
            clave_de=lambda e: e.genero,
        ),
        Tabla(
            clave="stock",
            etiqueta="Stock",
            singular="stock",
            modelo=Stock,
            fabrica_servicio=fabrica(ServicioStock),
            campos=(
                Campo("libro", "Libro", "fk", "libro"),
                Campo("existencia", "Existencia", "int"),
            ),
            columnas=(("libro", "Libro"), ("existencia", "Existencia")),
            texto=lambda e: e.libro.titulo,
            clave_de=lambda e: e.libro.isbn,
        ),
        Tabla(
            clave="precio",
            etiqueta="Precios",
            singular="precio",
            modelo=Precio,
            fabrica_servicio=fabrica(ServicioPrecio),
            campos=(
                Campo("libro", "Libro", "fk", "libro"),
                Campo("moneda", "Moneda", "fk", "moneda"),
                Campo("valor", "Valor", "float"),
            ),
            columnas=(("libro", "Libro"), ("moneda", "Moneda"), ("valor", "Valor")),
            texto=lambda e: f"{e.libro.titulo} ({e.moneda.codigo})",
            clave_de=lambda e: (e.libro.isbn, e.moneda.codigo),
        ),
        Tabla(
            clave="moneda",
            etiqueta="Monedas",
            singular="moneda",
            modelo=Moneda,
            fabrica_servicio=fabrica(ServicioMoneda),
            campos=(
                Campo("codigo", "Código", "str"),
                Campo("nombre", "Nombre", "str"),
            ),
            columnas=(("codigo", "Código"), ("nombre", "Nombre")),
            texto=lambda e: e.codigo,
            clave_de=lambda e: e.codigo,
        ),
        Tabla(
            clave="tipo_cotizacion",
            etiqueta="Tipos de cotización",
            singular="tipo de cotización",
            modelo=TipoCotizacion,
            fabrica_servicio=fabrica(ServicioTipoCotizacion),
            campos=(Campo("tipo", "Tipo", "str"),),
            columnas=(("tipo", "Tipo"),),
            texto=lambda e: e.tipo,
            clave_de=lambda e: e.tipo,
        ),
        Tabla(
            clave="cotizacion",
            etiqueta="Cotizaciones",
            singular="cotización",
            modelo=CotizacionDolar,
            fabrica_servicio=fabrica(ServicioCotizacionDolar),
            campos=(
                Campo("tipo_cotizacion", "Tipo", "fk", "tipo_cotizacion"),
                Campo("fecha", "Fecha (AAAA-MM-DD)", "fecha"),
                Campo("valor_pesos", "Valor en pesos", "float"),
            ),
            columnas=(
                ("tipo_cotizacion", "Tipo"),
                ("fecha", "Fecha"),
                ("valor_pesos", "Valor (ARS)"),
            ),
            texto=lambda e: f"{e.tipo_cotizacion.tipo} {e.fecha}",
            clave_de=lambda e: (e.tipo_cotizacion.tipo, e.fecha),
        ),
    ]


# --- resolución de referencias ---


def _campo_de(tabla: Tabla, clave: str) -> Campo | None:
    """Busca en la tabla el campo editable con esa clave, o None si no existe."""
    for campo in tabla.campos:
        if campo.clave == clave:
            return campo
    return None


def _entidad_a_fila(tabla: Tabla, entidad: Any) -> dict:
    """Convierte una entidad en un dict de vista, resolviendo referencias."""
    fila: dict[str, Any] = {}
    for clave, _ in tabla.columnas:
        campo = _campo_de(tabla, clave)
        valor = getattr(entidad, clave, None)
        if campo is not None and campo.tipo == "fk":
            fila[clave] = (
                CATALOGO[campo.fk_tabla].texto(valor) if valor is not None else ""
            )
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
        return CATALOGO[campo.fk_tabla].texto(valor) if valor is not None else ""
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


def _pedir_fk(campo: Campo, actual: Any = None) -> Any:
    """Lista las opciones de la tabla referenciada y devuelve el objeto elegido."""
    tabla = CATALOGO[campo.fk_tabla]
    opciones = tabla.fabrica_servicio().leer_todos()
    if not opciones:
        print(f"No hay {tabla.etiqueta.lower()} cargados.")
        return actual

    print()
    for i, e in enumerate(opciones, start=1):
        print(f"  {i}. {tabla.texto(e)}")

    sufijo = f" [{tabla.texto(actual)}]" if actual is not None else ""
    while True:
        raw = input(f"{campo.etiqueta} (número){sufijo}: ").strip()
        if raw == "":
            return actual
        try:
            elegido = int(raw)
        except ValueError:
            print("Debe ser un número.")
            continue
        if 1 <= elegido <= len(opciones):
            return opciones[elegido - 1]
        print("Ese número no existe.")


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


def _pedir_numero(maximo: int) -> int | None:
    """Pide un número de fila entre 1 y `maximo`. None si cancela."""
    while True:
        raw = input("Número: ").strip()
        if raw == "":
            return None
        try:
            n = int(raw)
        except ValueError:
            print("Debe ser un número.")
            continue
        if 1 <= n <= maximo:
            return n
        print(f"Ingresá un número entre 1 y {maximo}.")


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
    """Lista todos los registros de la tabla, con número de fila."""
    entidades = tabla.fabrica_servicio().leer_todos()
    if not entidades:
        print("No hay nada cargado.")
        return
    filas = []
    for i, e in enumerate(entidades, start=1):
        fila = _entidad_a_fila(tabla, e)
        fila["#"] = i
        filas.append(fila)
    print()
    print(render_tabla(filas, (("#", "#"),) + tabla.columnas))
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
    try:
        tabla.fabrica_servicio().crear(entidad)
    except ValueError as error:
        print(f"No se pudo guardar: {error}")
        return
    print("Quedó guardado.")


def _editar(tabla: Tabla) -> None:
    """Edita solo los campos que elija el usuario de un registro existente."""
    servicio = tabla.fabrica_servicio()
    entidades = servicio.leer_todos()
    if not entidades:
        print("No hay nada cargado.")
        return

    _ver(tabla)
    numero = _pedir_numero(len(entidades))
    if numero is None:
        return
    entidad = entidades[numero - 1]
    clave = tabla.clave_de(entidad)

    campos = list(tabla.campos)
    print()
    for i, campo in enumerate(campos, start=1):
        print(f"  {i}. {campo.etiqueta}: {_valor_actual(campo, entidad)}")

    seleccion = _pedir_seleccion(len(campos))
    if seleccion is None:
        print("Cancelado.")
        return

    datos = {campo.clave: getattr(entidad, campo.clave) for campo in campos}
    for indice in seleccion:
        campo = campos[indice - 1]
        valor = _pedir_campo(campo, datos[campo.clave])
        if valor is not None:
            datos[campo.clave] = valor

    try:
        nueva = tabla.modelo(**datos)
    except ValidationError as error:
        _mostrar_error_validacion(error)
        return

    try:
        servicio.actualizar(clave, nueva)
    except ValueError as error:
        print(f"No se pudo guardar: {error}")
        return
    print("Quedó guardado.")


def _eliminar(tabla: Tabla) -> None:
    """Borra un registro por número de fila, previa confirmación."""
    servicio = tabla.fabrica_servicio()
    entidades = servicio.leer_todos()
    if not entidades:
        print("No hay nada cargado.")
        return

    _ver(tabla)
    numero = _pedir_numero(len(entidades))
    if numero is None:
        return
    entidad = entidades[numero - 1]
    clave = tabla.clave_de(entidad)

    confirmar = input(f"¿Borrar '{tabla.texto(entidad)}'? (s/N): ").strip().lower()
    if confirmar not in ("s", "si", "sí"):
        print("Cancelado.")
        return
    try:
        servicio.eliminar(clave)
    except ValueError as error:
        print(f"No se pudo borrar: {error}")
        return
    print("Borrado.")


def _buscar(tabla: Tabla) -> None:
    """Muestra los registros que contienen el texto en alguna columna."""
    texto = input("Buscar: ").strip()
    if not texto:
        return

    entidades = tabla.fabrica_servicio().leer_todos()
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


# --- reportes y acciones globales ---


def _obtener_cotizaciones_api(conexion: ConexionDB) -> None:
    """Descarga y registra las cotizaciones actuales de la API del dólar."""
    servicio = ServicioCotizacionDolar(conexion=conexion)
    try:
        registradas = servicio.obtener_cotizaciones()
    except requests.RequestException as error:
        print(f"No se pudo consultar la API: {error}")
        return
    for cotizacion in registradas:
        print(
            f"  {cotizacion.tipo_cotizacion.tipo:<10} {cotizacion.fecha}"
            f"  $ {cotizacion.valor_pesos:.2f}"
        )
    print(f"Se registraron {len(registradas)} cotización(es) nuevas.")


def _pedir_cotizacion(servicio: ServicioListaPrecios) -> CotizacionDolar | None:
    """Lista la última cotización de cada tipo de dólar y devuelve la elegida."""
    cotizaciones = servicio.cotizaciones_vigentes()
    if not cotizaciones:
        print("No hay cotizaciones del dólar. Obtenelas primero desde la API.")
        return None
    print()
    for i, cotizacion in enumerate(cotizaciones, start=1):
        print(
            f"  {i}. {cotizacion.tipo_cotizacion.tipo:<10}"
            f" $ {cotizacion.valor_pesos:.2f} ({cotizacion.fecha})"
        )
    numero = _pedir_numero(len(cotizaciones))
    return cotizaciones[numero - 1] if numero is not None else None


def _precios_bimonetarios(conexion: ConexionDB) -> None:
    """Muestra el precio de cada libro en dólares y en pesos al dólar elegido."""
    servicio = ServicioListaPrecios(conexion=conexion)
    cotizacion = _pedir_cotizacion(servicio)
    if cotizacion is None:
        return
    tipo = cotizacion.tipo_cotizacion.tipo
    _, precios = servicio.lista_bimonetaria(tipo)
    if not precios:
        print("No hay precios en USD o ARS para mostrar.")
        return

    filas = [
        {"titulo": p.titulo, "usd": f"{p.usd:.2f}", "ars": f"{p.ars:.2f}"}
        for p in precios
    ]
    print()
    print(f"Dólar {tipo} del {cotizacion.fecha}: $ {cotizacion.valor_pesos:.2f}")
    print(
        render_tabla(
            filas,
            (
                ("titulo", "Libro"),
                ("usd", "Precio (USD)"),
                ("ars", f"Precio (ARS {tipo})"),
            ),
        )
    )


def _exportar_precios_csv(
    conexion: ConexionDB, ruta: Path = EXPORTS_FOLDER_PATH / "precios.csv"
) -> None:
    """Exporta los precios en pesos para todos los tipos de dólar a un CSV."""
    cotizaciones = ServicioListaPrecios(conexion=conexion).exportar_csv(ruta)
    tipos = ", ".join(c.tipo_cotizacion.tipo for c in cotizaciones) or "ninguno"
    print(f"Exportado a {ruta} (tipos de dólar: {tipos}).")


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


def _menu_principal(tablas: list[Tabla], conexion: ConexionDB) -> None:
    """Menú principal: tablas CRUD + acciones globales."""
    n = len(tablas)
    while True:
        print()
        for i, tabla in enumerate(tablas, start=1):
            print(f"  {i}. {tabla.etiqueta}")
        print(f"  {n + 1}. Obtener cotizaciones por API")
        print(f"  {n + 2}. Precios bimonetarios (USD y pesos por tipo de dólar)")
        print(f"  {n + 3}. Exportar precios a CSV")
        print("  0. Salir")

        opcion = _pedir_opcion(n + 3)
        if opcion == 0:
            print("Chau.")
            return
        if opcion <= n:
            _menu_tabla(tablas[opcion - 1])
        elif opcion == n + 1:
            _obtener_cotizaciones_api(conexion)
        elif opcion == n + 2:
            _precios_bimonetarios(conexion)
        elif opcion == n + 3:
            _exportar_precios_csv(conexion)


def main(conexion: ConexionDB | None = None) -> None:
    """Punto de entrada de la aplicación de consola."""
    conexion = conexion or ConexionDB()
    tablas = _construir_tablas(conexion)
    CATALOGO.update({t.clave: t for t in tablas})
    try:
        _menu_principal(tablas, conexion)
    except (KeyboardInterrupt, EOFError):
        print()
        print("Chau.")
