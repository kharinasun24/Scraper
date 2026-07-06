# TODO: Implement this further!

from core.base import BaseScraper

from core.logger import get_logger

log = get_logger("rewe")


# ... andere Imports

class ReweScraper(BaseScraper):
    def __init__(self):
        # Die Suchseite für Butter bei REWE
        super().__init__("https://www.rewe.de/lese-vorausgewaehlten-markt-oder-suchseite")

    def extract_logic(self, page, kategorie: str):
        log.info(f"Scrape REWE für: {kategorie}")

        # 1. TIPP: Falls REWE nach einem Markt fragt, tippe kurz eine PLZ ein
        # page.fill("input#market-search", "68161") # Beispiel Mannheim
        # page.click("button.select-market-btn")

        # 2. Danach kannst du die exakt gleichen CSS-Klassen wie bei Penny ansteuern!
        # Der Rest deines Codes mit der Bereinigung und dem Stoppwort-Filter
        # greift hier wieder perfekt.