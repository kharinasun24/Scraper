# scraper/penny.py
import time

from core.base import BaseScraper
from core.logger import get_logger

class PennyScraper(BaseScraper):
    def __init__(self):
        # Wir übergeben der Basis-Klasse einfach die erste Haupt-URL
        super().__init__("https://www.penny.de/angebote/#ab-montag--kuehlregal")

        # Hier definieren wir alle zusätzlichen URLs, die wir AUCH noch abgrasen wollen
        self.zusatz_urls = [
            "https://www.penny.de/sortiment/",
            "https://www.penny.de/sortiment/milprima"
        ]

    def extract_logic(self, page):

        log = get_logger("scraper")
        log.info("Penny-Extraktion läuft...")

        # 1. Den Inhalt der allerersten URL (aus dem __init__) herbeiholen
        komplettes_html = page.content()

        # 2. Jetzt klappern wir nacheinander die Sortiments-Seiten ab
        for url in self.zusatz_urls:
            try:
                log.info(f"Öffne zusätzlich: {url}...")
                page.goto(url)

                # Kurze Verschnaufpause für den Browser, damit das JS sauber lädt
                time.sleep(2)

                # Wir hängen das HTML der neuen Seite einfach an unseren Gesamt-String an
                komplettes_html += "\n\n"
                komplettes_html += page.content()

            except Exception as e:
                log.error(f"Fehler beim Laden von {url}: {e}")
                continue

        # Am Ende geben wir das vereinte Riesen-HTML zurück an den PriceManager / die main.py
        return komplettes_html