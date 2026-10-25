"""Configuración de scrapy para el scraper de Cúspide.

Se pasa tal cual a `CrawlerProcess`, así el crawl no depende de un
`scrapy.cfg` ni del directorio desde el que se ejecute.
"""

from __future__ import annotations

USER_AGENT = (
    "book_manager/0.1 (trabajo práctico académico; contacto: "
    "seminario-integrador@example.com)"
)

settings: dict[str, object] = {
    "BOT_NAME": "book_manager",
    # El scraper se lanza como programa de Python, sin `scrapy crawl`.
    "SPIDER_MODULES": ["book_manager.scraper.spiders"],
    "NEWSPIDER_MODULE": "book_manager.scraper.spiders",
    "USER_AGENT": USER_AGENT,
    # Respetamos el robots.txt del sitio y esperamos 1 s entre requests.
    "ROBOTSTXT_OBEY": True,
    "DOWNLOAD_DELAY": 1,
    "ITEM_PIPELINES": {"book_manager.scraper.pipelines.PrecioWebPipeline": 300},
    "LOG_LEVEL": "INFO",
    # scrapy 2.19 solo implementa el fingerprinting 2.7: el setting ya no se
    # lee, se deja explícito por compatibilidad con versiones anteriores.
    "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
}
