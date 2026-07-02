# scraper/aldi.py
from core.base import BaseScraper
import time


class AldiScraper(BaseScraper):
    # Die URLs verwalten wir jetzt exklusiv HIER im Scraper, getrennt nach Kategorie
    ALDI_URLS = {
        "butter": [
            "https://www.aldi-sued.de/produkt/milsani-deutsche-markenbutter-250-g-000000000000202682",
            "https://www.aldi-sued.de/produkt/milsani-irische-butter-250-g-000000000000202698"
        ],
        "kefir": [
            "https://www.aldi-sued.de/produkt/mueller-kefir-500-g-000000000530678002"
        ]
    }

    def __init__(self, kategorie):
        # Wir holen uns die passende URL-Liste für die Kategorie
        self.urls = self.ALDI_URLS.get(kategorie.lower(), [])

        # Basis-Klasse mit der ersten URL initialisieren (oder Standardseite falls leer)
        start_url = self.urls[0] if self.urls else "https://www.aldi-sued.de/"
        super().__init__(start_url)

        # Die restlichen URLs für die Schleife merken
        self.zusatz_urls = self.urls[1:] if len(self.urls) > 1 else []

    def extract_logic(self, page):
        print("Aldi-Extraktion läuft...")
        if not self.urls:
            print("Keine URLs für diese Kategorie bei Aldi hinterlegt.")
            return ""

        # 1. HTML der ersten Seite holen
        komplettes_html = page.content()

        # 2. Die restlichen URLs abklappern
        for url in self.zusatz_urls:
            try:
                print(f"Öffne zusätzlich: {url}...")
                page.goto(url)
                time.sleep(2)  # Kurze Pause für das JavaScript-Rendern
                komplettes_html += f"\n\n\n"
                komplettes_html += page.content()
            except Exception as e:
                print(f"Fehler beim Laden von Aldi-URL {url}: {e}")
                continue

        return komplettes_html