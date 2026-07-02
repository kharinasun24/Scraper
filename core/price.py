# core/price.py
from scraper.penny import PennyScraper
from scraper.aldi import AldiScraper
from core.products import Product
from typing import List

class PriceManager:
    def __init__(self):
        self.scraper_liste = {
            "Penny": PennyScraper(),
            "Aldi": AldiScraper()
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
                print(f"Fehler beim Scrapen von {name}: {e}")

        return alle_produkte