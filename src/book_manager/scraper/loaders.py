"""Loaders de ítems: extracción y limpieza de los datos de Cúspide.

Cúspide publica los precios en formato argentino (`$ 55.999,00`): el punto es
separador de miles y la coma es el separador decimal. Por eso el precio se
normaliza antes de convertirlo a `float`.
"""

from __future__ import annotations

from itemloaders.processors import Identity, Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader

from book_manager.scraper.items import CuspideItem

# Caracteres que separan el símbolo de moneda del monto. `&nbsp;` aparece como
# entidad en el HTML y como U+00A0 una vez que parsel decodifica el documento.
_SEPARADORES_MONEDA = ("&nbsp;", "\xa0", " ", "$")


def limpiar_precio(valor: str) -> float | None:
    """Convierte un precio argentino (`$ 55.999,00`) al float `55999.0`.

    Args:
        valor: Texto tal como aparece en la página.

    Returns:
        El monto como float, o None si el texto no tiene un número (por ejemplo
        una cadena vacía o un precio "a consultar").
    """
    texto = valor
    for separador in _SEPARADORES_MONEDA:
        texto = texto.replace(separador, "")
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


class CuspideLoader(ItemLoader):
    """Loader del detalle de un libro en Cúspide.

    Aplica a todos los campos un `strip` de entrada y toma el primer valor de
    salida: la página repite algunos textos y el modelo guarda un solo valor.
    Los campos que necesitan otro tratamiento lo declaran con sus procesadores
    `*_in` / `*_out`.
    """

    default_item_class = CuspideItem
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()

    # El precio viene con puntos de miles y coma decimal.
    precio_in = MapCompose(limpiar_precio)
    # Las formas de pago son varios `<li>`: se guardan como un solo texto.
    formas_pago_out = Join(", ")
    # `libro_id` es un int: el strip por defecto solo aplica a texto.
    libro_id_in = Identity()
