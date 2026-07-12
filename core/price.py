# core/price.py
from scraper.penny import PennyScraper
from scraper.aldi import AldiScraper
from scraper.rewe import ReweScraper
from core.products import Product
from typing import List

import logging

log = logging.getLogger("price.py")

class PriceManager:
    #def __init__(self, plz: str = None):
    #    self.plz = plz
    #    self.scraper_liste = {
    #        "Penny": PennyScraper(plz=self.plz),
    #        "Aldi": AldiScraper(plz=self.plz),
    #        "Rewe": ReweScraper(plz=self.plz)
    #    }

    def __init__(self, plz: str = None):
        self.plz = plz
        # Wir speichern nur die Klassen, wir instanziieren sie noch nicht!
        self.scraper_klassen = {
            "Penny": PennyScraper,
            "Aldi": AldiScraper,
            "Rewe": ReweScraper
        }

    def alle_produkte(self, kategorie: str = "butter") -> List[Product]:
        alle_produkte: List[Product] = []

        for name, ScraperKlasse in self.scraper_klassen.items():
            # Erst HIER im Ablauf wird der Scraper exakt im richtigen Moment geboren:
            scraper = ScraperKlasse(plz=self.plz)

            try:
                log.info(f"========== {name.upper()}: Suche nach '{kategorie}' ==========")
                roh_produkte = scraper.scrape(kategorie=kategorie)

                for p in roh_produkte:
                    if isinstance(p, dict):
                        p["markt"] = name
                        p["kategorie"] = kategorie
                        alle_produkte.append(Product(**p))
                    elif isinstance(p, Product):
                        p.markt = name
                        alle_produkte.append(p)
            except Exception as e:
                print(f"\n!!! CRASH BEI SCRAPER {name} !!!: {e}\n")
            finally:
                # Nach der Arbeit sofort den Browser dieses einen Scrapers schließen
                try:
                    if hasattr(scraper, 'close_browser'):
                        scraper.close_browser()
                    elif hasattr(scraper, 'close'):
                        scraper.close()
                except Exception as close_error:
                    print(f"Fehler beim Schließen von {name}: {close_error}")

                # Objekt zerstören, um Sperren im Dateisystem zu lösen
                del scraper

        return alle_produkte