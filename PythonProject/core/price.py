# core/price.py
from scraper.penny import PennyScraper
from scraper.aldi import AldiScraper
import __main__  # Ermöglicht dem Manager, Variablen aus der main.py zu lesen!


class PriceManager:
    def alle_preise_abrufen(self):
        print("Starte den großen Preisabruf...")
        ergebnisse = {}

        # 1. Penny aufrufen (mit dem korrekten Methodennamen aus der Base)
        try:
            penny = PennyScraper()
            ergebnisse["Penny"] = penny.get_product_data()  # <-- HIER GEÄNDERT!
        except Exception as e:
            print(f"Fehler bei Penny-Scraper: {e}")
            ergebnisse["Penny"] = None

        # 2. Aldi aufrufen
        try:
            # Wir holen uns das 'kategorie_ziel' direkt aus der laufenden main.py
            kategorie = getattr(__main__, "kategorie_ziel", "butter")

            aldi = AldiScraper(kategorie=kategorie)
            ergebnisse["Aldi"] = aldi.get_product_data()  # <-- HIER GEÄNDERT!
        except Exception as e:
            print(f"Fehler bei Aldi-Scraper: {e}")
            ergebnisse["Aldi"] = None

        return ergebnisse