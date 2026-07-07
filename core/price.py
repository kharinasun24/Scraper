# core/price.py
from scraper.penny import PennyScraper
from scraper.aldi import AldiScraper
from scraper.rewe import ReweScraper
from core.products import Product
from typing import List

class PriceManager:
    def __init__(self, plz: str = None):
        self.plz = plz
        self.scraper_liste = {
            "Penny": PennyScraper(plz=self.plz),
            "Aldi": AldiScraper(plz=self.plz),
            "Rewe": ReweScraper(plz=self.plz)
        }

    def alle_produkte(self, kategorie: str = "butter") -> List[Product]:
        alle_produkte: List[Product] = []

        for name, scraper in self.scraper_liste.items():
            try:
                roh_produkte = scraper.scrape(kategorie=kategorie)  # Übergabe der Kategorie

                for p in roh_produkte:
                    if isinstance(p, dict):
                        p["markt"] = name
                        p["kategorie"] = kategorie
                        alle_produkte.append(Product(**p))
                    elif isinstance(p, Product):
                        p.markt = name
                        alle_produkte.append(p)
            except Exception as e:
                # WICHTIG: Verwende dein Logging oder mach es hier auffälliger
                print(f"\n!!! CRASH BEI SCRAPER {name} !!!: {e}\n")

            finally:
                # FIX: Hier räumen wir rigoros auf!
                # Prüfe, ob dein BaseScraper eine Methode wie 'close', 'close_browser' oder 'cleanup' hat.
                # Meistens heißt sie close() oder close_browser().
                try:
                    if hasattr(scraper, 'close_browser'):
                        scraper.close_browser()
                    elif hasattr(scraper, 'close'):
                        scraper.close()
                except Exception as close_error:
                    print(f"Fehler beim Schließen des Browsers von {name}: {close_error}")

        return alle_produkte