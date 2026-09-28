from book_manager.preload_data.preload_data import precargar_datos
from book_manager.ui.console import main as console_main


def main(import_default_data: bool = False) -> None:
    """Ejecuta el sistema: prepara los datos y abre el menú de consola.

    Los CSV que falten se generan siempre con los datos de ejemplo, así el
    sistema arranca con datos aunque sea la primera vez.

    Args:
        import_default_data: Si es True, regenera todos los CSV de ejemplo antes
            de abrir el menú (pisa lo cargado). Con False conserva los datos
            existentes.
    """
    precargar_datos(renovar=import_default_data)
    console_main()


if __name__ == "__main__":
    main()
