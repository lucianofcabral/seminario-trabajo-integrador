"""Precarga de datos: genera los CSV de ejemplo en `migrations/csv`."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pycountry
from babel.numbers import get_currency_name

from book_manager.repositories.csv_config import csv_config
from book_manager.rutas import CSV_FOLDER_PATH

CSV_FOLDER: Path = CSV_FOLDER_PATH

TIPOS_COTIZACION: list[str] = [
    "Blue",
    "MEP",
    "Oficial",
    "CCL",
    "Mayorista",
    "Cripto",
    "Tarjeta",
    "Solidario",
    "Blend",
    "Turista",
]


def _generar_csv(
    data: list[dict[str, Any]],
    path: Path,
    renovar: bool = False,
    asignar_id: bool = False,
) -> None:
    """Escribe una lista de diccionarios como CSV.

    Args:
        data: Filas a escribir; las claves de la primera fila son la cabecera.
        path: Ruta del archivo CSV.
        renovar: Si es False y el archivo ya existe, no hace nada.
        asignar_id: Si es True, agrega una columna `id` numerada desde 1.
    """

    if not renovar and path.exists():
        return

    if len(data) == 0:
        return

    if asignar_id:
        campos = list(data[0].keys())
        campos.insert(0, "id")
    else:
        campos = list(data[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos, **csv_config)
        writer.writeheader()
        if asignar_id:
            for i, item in enumerate(data, start=1):
                item["id"] = i
        writer.writerows(data)
    print(f"CSV generado: {path} ({len(data)} filas)")


def generar_csv_monedas(renovar: bool = False) -> None:
    """Genera un CSV con las monedas vigentes según ISO 4217.

    Combina la lista oficial de códigos (pycountry) con nombres,
    símbolos y decimales provenientes de Unicode CLDR (babel).

    Args:
        renovar: Si se debe regenerar el archivo CSV, incluso si ya existe.
    """

    path: Path = CSV_FOLDER / "moneda.csv"
    if not renovar and path.exists():
        return

    monedas: list[dict] = []

    for moneda in pycountry.currencies:
        codigo = moneda.alpha_3

        try:
            nombre_es = get_currency_name(codigo, locale="es")
        except (KeyError, ValueError) as e:
            print(f"Error al obtener datos para {codigo}: {e}")
            continue

        monedas.append(
            {
                "codigo": codigo,
                "nombre": nombre_es,
            }
        )

    monedas.sort(key=lambda r: r["codigo"])

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "codigo", "nombre"],
            **csv_config,
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "id": i,
                    "codigo": m["codigo"],
                    "nombre": m["nombre"],
                }
                for i, m in enumerate(monedas, start=1)
            ]
        )

    print(f"CSV generado: {path} ({len(monedas)} monedas)")


def generar_csv_generos(renovar: bool = False, asignar_id: bool = True) -> None:
    """Genera el archivo CSV de géneros.

    Args:
        renovar: Si se debe regenerar el archivo CSV, incluso si ya existe.
        asignar_id: Si se debe numerar cada género con un id.
    """

    path: Path = CSV_FOLDER / "genero.csv"
    if not renovar and path.exists():
        return

    generos = [
        {"genero": genero}
        for genero in [
            "Ficción",
            "Terror",
            "Ciencia ficción",
            "Fantasía",
            "Romance",
            "Misterio / Policial",
            "Thriller / Suspenso",
            "Biografía",
            "Ensayo",
            "Poesía",
        ]
    ]

    _generar_csv(data=generos, path=path, renovar=renovar, asignar_id=asignar_id)


def generar_csv_editoriales(renovar: bool = False) -> None:
    """Genera el archivo CSV de editoriales.

    Args:
        renovar: Si se debe regenerar el archivo CSV, incluso si ya existe.
    """

    path: Path = CSV_FOLDER / "editorial.csv"
    if not renovar and path.exists():
        return

    editoriales = [
        {
            "proveedor": "Editorial Alba",
            "pais": "Argentina",
            "provincia": "Buenos Aires",
            "localidad": "CABA",
            "domicilio": "Av. Siempre Viva 123",
            "telefono": "1145678901",
            "email": "contacto@editorialalba.com",
            "responsable": "Juan Pérez",
        },
        {
            "proveedor": "Ediciones del Sur",
            "pais": "Argentina",
            "provincia": "Santa Fe",
            "localidad": "Rosario",
            "domicilio": "Calle Córdoba 456",
            "telefono": "3414567890",
            "email": "info@edicionesdelsur.com",
            "responsable": "María Gómez",
        },
        {
            "proveedor": "Editorial Andes",
            "pais": "Chile",
            "provincia": "Santiago",
            "localidad": "Providencia",
            "domicilio": "Av. Providencia 789",
            "telefono": "+56223456789",
            "email": "ventas@editorialandes.cl",
            "responsable": "Pedro Rodríguez",
        },
        {
            "proveedor": "Casa Letras",
            "pais": "México",
            "provincia": "Ciudad de México",
            "localidad": "Coyoacán",
            "domicilio": "Calle Allende 321",
            "telefono": "5555123456",
            "email": "contacto@casaletras.mx",
            "responsable": "Ana Torres",
        },
        {
            "proveedor": "Editorial Ibérica",
            "pais": "España",
            "provincia": "Madrid",
            "localidad": "Chamberí",
            "domicilio": "Calle Fuencarral 654",
            "telefono": "+34911234567",
            "email": "info@editorialiberica.es",
            "responsable": "Carlos Fernández",
        },
        {
            "proveedor": "Ediciones Australis",
            "pais": "Uruguay",
            "provincia": "Montevideo",
            "localidad": "Pocitos",
            "domicilio": "Bulevar España 987",
            "telefono": "+59829876543",
            "email": "editorial@australis.uy",
            "responsable": "Lucía Fernández",
        },
        {
            "proveedor": "Editorial Boreal",
            "pais": "Canadá",
            "provincia": "Quebec",
            "localidad": "Montreal",
            "domicilio": "Rue Sainte-Catherine 159",
            "telefono": "+15145551234",
            "email": "contact@editorialboreal.ca",
            "responsable": "Sophie Tremblay",
        },
        {
            "proveedor": "Editorial Meridiano",
            "pais": "Colombia",
            "provincia": "Bogotá D.C.",
            "localidad": "Chapinero",
            "domicilio": "Carrera 13 #45-67",
            "telefono": "6013456789",
            "email": "info@editorialmeridiano.co",
            "responsable": "Diego Ramírez",
        },
        {
            "proveedor": "Ediciones Norte Fuerte",
            "pais": "Perú",
            "provincia": "Lima",
            "localidad": "Miraflores",
            "domicilio": "Av. Larco 234",
            "telefono": "014567890",
            "email": "contacto@nortefuerte.pe",
            "responsable": "Valentina Castro",
        },
        {
            "proveedor": "Editorial Austral Sur",
            "pais": "Brasil",
            "provincia": "São Paulo",
            "localidad": "Pinheiros",
            "domicilio": "Rua Augusta 852",
            "telefono": "+551134567890",
            "email": "contato@australsur.com.br",
            "responsable": "Rafael Souza",
        },
    ]

    _generar_csv(data=editoriales, path=path, renovar=renovar, asignar_id=True)


def generar_csv_libros(renovar: bool = False, asignar_id: bool = True) -> None:
    """Genera el archivo CSV de libros.

    Args:
        renovar: Si se debe regenerar el archivo CSV, incluso si ya existe.
        asignar_id: Si se debe numerar cada libro con un id.
    """

    libros = [
        {
            "isbn": "9780306406157",
            "titulo": "El eco del silencio",
            "autor": "Marina Solís",
            "editorial_id": 1,
            "genero_id": 1,
        },
        {
            "isbn": "9781234567897",
            "titulo": "Sombras en la niebla",
            "autor": "Diego Ferrari",
            "editorial_id": 2,
            "genero_id": 2,
        },
        {
            "isbn": "9780451524935",
            "titulo": "Estación Marte 7",
            "autor": "Laura Kim",
            "editorial_id": 3,
            "genero_id": 3,
        },
        {
            "isbn": "9781408855652",
            "titulo": "El reino de las cenizas",
            "autor": "Tomás Beltrán",
            "editorial_id": 4,
            "genero_id": 4,
        },
        {
            "isbn": "9780141439600",
            "titulo": "Cartas al mar",
            "autor": "Valentina Ríos",
            "editorial_id": 5,
            "genero_id": 5,
        },
        {
            "isbn": "9780062315007",
            "titulo": "El último testigo",
            "autor": "Andrés Molina",
            "editorial_id": 6,
            "genero_id": 6,
        },
        {
            "isbn": "9780307474278",
            "titulo": "La cuenta regresiva",
            "autor": "Sofía Nardone",
            "editorial_id": 7,
            "genero_id": 7,
        },
        {
            "isbn": "9780553380163",
            "titulo": "Vida de un forastero",
            "autor": "Ricardo Peña",
            "editorial_id": 8,
            "genero_id": 8,
        },
        {
            "isbn": "9780679783268",
            "titulo": "Pensamientos dispersos",
            "autor": "Camila Duarte",
            "editorial_id": 9,
            "genero_id": 9,
        },
        {
            "isbn": "9780679732761",
            "titulo": "Versos de otoño",
            "autor": "Julián Esparza",
            "editorial_id": 10,
            "genero_id": 10,
        },
        {
            "isbn": "9780743273565",
            "titulo": "El jardín olvidado",
            "autor": "Marina Solís",
            "editorial_id": 1,
            "genero_id": 10,
        },
        {
            "isbn": "9780345391803",
            "titulo": "La casa que gritaba",
            "autor": "Diego Ferrari",
            "editorial_id": 2,
            "genero_id": 9,
        },
        {
            "isbn": "9780765348281",
            "titulo": "Colonia Andrómeda",
            "autor": "Laura Kim",
            "editorial_id": 3,
            "genero_id": 8,
        },
        {
            "isbn": "9780765326355",
            "titulo": "El dragón de hielo",
            "autor": "Tomás Beltrán",
            "editorial_id": 4,
            "genero_id": 7,
        },
        {
            "isbn": "9780061120084",
            "titulo": "Bajo el mismo cielo",
            "autor": "Valentina Ríos",
            "editorial_id": 5,
            "genero_id": 6,
        },
        {
            "isbn": "9780316069359",
            "titulo": "El expediente perdido",
            "autor": "Andrés Molina",
            "editorial_id": 6,
            "genero_id": 5,
        },
        {
            "isbn": "9780385504201",
            "titulo": "Doce horas para morir",
            "autor": "Sofía Nardone",
            "editorial_id": 7,
            "genero_id": 4,
        },
        {
            "isbn": "9780679644777",
            "titulo": "Memorias de un náufrago",
            "autor": "Ricardo Peña",
            "editorial_id": 8,
            "genero_id": 3,
        },
        {
            "isbn": "9780140449266",
            "titulo": "Fragmentos del pensamiento",
            "autor": "Camila Duarte",
            "editorial_id": 9,
            "genero_id": 2,
        },
        {
            "isbn": "9780156012195",
            "titulo": "El río y la ceniza",
            "autor": "Julián Esparza",
            "editorial_id": 10,
            "genero_id": 1,
        },
        {
            "isbn": "9780307387899",
            "titulo": "La ciudad invisible",
            "autor": "Marina Solís",
            "editorial_id": 2,
            "genero_id": 1,
        },
        {
            "isbn": "9780307949486",
            "titulo": "El sótano de Meridian",
            "autor": "Diego Ferrari",
            "editorial_id": 3,
            "genero_id": 2,
        },
        {
            "isbn": "9780765356150",
            "titulo": "Órbita rota",
            "autor": "Laura Kim",
            "editorial_id": 4,
            "genero_id": 3,
        },
        {
            "isbn": "9780756404079",
            "titulo": "La espada del norte",
            "autor": "Tomás Beltrán",
            "editorial_id": 5,
            "genero_id": 4,
        },
        {
            "isbn": "9780743299573",
            "titulo": "Un verano en Toscana",
            "autor": "Valentina Ríos",
            "editorial_id": 6,
            "genero_id": 5,
        },
        {
            "isbn": "9780312364815",
            "titulo": "El informante silencioso",
            "autor": "Andrés Molina",
            "editorial_id": 7,
            "genero_id": 6,
        },
        {
            "isbn": "9780345803481",
            "titulo": "Cuenta atrás en Berlín",
            "autor": "Sofía Nardone",
            "editorial_id": 8,
            "genero_id": 7,
        },
        {
            "isbn": "9780679601886",
            "titulo": "El hombre que caminó solo",
            "autor": "Ricardo Peña",
            "editorial_id": 9,
            "genero_id": 8,
        },
        {
            "isbn": "9780679751818",
            "titulo": "Apuntes sobre la nada",
            "autor": "Camila Duarte",
            "editorial_id": 10,
            "genero_id": 9,
        },
        {
            "isbn": "9780156030472",
            "titulo": "Hojas al viento",
            "autor": "Julián Esparza",
            "editorial_id": 1,
            "genero_id": 10,
        },
    ]
    _generar_csv(
        data=libros,
        path=CSV_FOLDER / "libro.csv",
        renovar=renovar,
        asignar_id=asignar_id,
    )


def generar_csv_stock(renovar: bool = False) -> None:
    """Genera el stock de los 30 libros con existencias aleatorias.

    Args:
        renovar: Si se debe regenerar el archivo CSV, incluso si ya existe.
    """

    path: Path = CSV_FOLDER / "stock.csv"
    if not renovar and path.exists():
        return

    stocks = [
        {"libro_id": n, "existencia": random.randint(0, 5000)} for n in range(1, 31)
    ]

    _generar_csv(data=stocks, path=path, renovar=renovar, asignar_id=True)


def _id_de_moneda(codigo: str) -> int:
    """Busca el id de una moneda por su código en el CSV de monedas.

    Args:
        codigo: Código ISO 4217, p. ej. "USD".

    Returns:
        El id de la moneda.

    Raises:
        ValueError: Si la moneda no está en el CSV.
    """
    with open(CSV_FOLDER / "moneda.csv", newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila["codigo"] == codigo:
                return int(fila["id"])
    raise ValueError(f"No se encontró la moneda {codigo} en moneda.csv")


def generar_csv_precio(renovar: bool = False) -> None:
    """Genera un precio aleatorio en dólares (USD) por libro.

    Necesita que ya exista el CSV de monedas para obtener el id del dólar.

    Args:
        renovar: Si se debe regenerar el archivo CSV, incluso si ya existe.
    """

    path: Path = CSV_FOLDER / "precio.csv"
    if not renovar and path.exists():
        return

    usd_id = _id_de_moneda("USD")
    precios = [
        {
            "libro_id": n,
            "moneda_id": usd_id,
            "valor": abs(round(random.normalvariate(mu=75, sigma=50), 2)),
        }
        for n in range(1, 31)
    ]

    _generar_csv(data=precios, path=path, renovar=renovar, asignar_id=True)


def generar_csv_tipo_cotizacion(renovar: bool = False) -> None:
    """Genera el archivo CSV de tipos de cotización del dólar.

    Args:
        renovar: Si se debe regenerar el archivo CSV, incluso si ya existe.
    """

    path: Path = CSV_FOLDER / "tipo_cotizacion.csv"
    if not renovar and path.exists():
        return

    tipos = [{"tipo": n} for n in TIPOS_COTIZACION]

    _generar_csv(data=tipos, path=path, renovar=renovar, asignar_id=True)


def generar_csv_cotizacion(renovar: bool = False) -> None:
    """Genera una cotización aleatoria por día para todo 2026.

    Args:
        renovar: Si se debe regenerar el archivo CSV, incluso si ya existe.
    """

    path: Path = CSV_FOLDER / "cotizacion.csv"
    if not renovar and path.exists():
        return

    cotis = []
    fecha = date(2026, 1, 1)
    while True:
        cotis.append(
            {
                "tipo_cotizacion_id": random.randint(1, len(TIPOS_COTIZACION)),
                "fecha": fecha.isoformat(),
                "valor_pesos": round(random.randint(140000, 180000) / 100, 2),
            }
        )
        fecha += timedelta(days=1)
        if fecha > date(2026, 12, 31):
            break

    _generar_csv(data=cotis, path=path, renovar=renovar, asignar_id=True)


def precargar_datos(renovar: bool = True) -> None:
    """Genera todos los CSVs de datos iniciales.

    El orden importa: los precios necesitan que ya existan las monedas.

    Args:
        renovar: Si es True, regenera cada CSV aunque ya exista (pisa datos).
            Si es False, solo crea los que faltan.
    """

    generar_csv_monedas(renovar=renovar)
    generar_csv_generos(renovar=renovar)
    generar_csv_editoriales(renovar=renovar)
    generar_csv_libros(renovar=renovar)
    generar_csv_stock(renovar=renovar)
    generar_csv_precio(renovar=renovar)
    generar_csv_tipo_cotizacion(renovar=renovar)
    generar_csv_cotizacion(renovar=renovar)


if __name__ == "__main__":
    precargar_datos()
