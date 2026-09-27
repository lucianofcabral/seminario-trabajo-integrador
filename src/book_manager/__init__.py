def main() -> None:
    """Punto de entrada del paquete (entry point `book-manager`)."""
    from book_manager.ui.console import main as console_main

    console_main()
