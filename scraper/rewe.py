# TODO: Implement this further!

from core.base import BaseScraper

from core.logger import get_logger

log = get_logger("rewe")


class ReweScraper(BaseScraper):
    def __init__(self, plz: str = None):
        super().__init__("https://www.rewe.de/lese-vorausgewaehlten-markt-oder-suchseite", plz=plz)

    def extract_logic(self, page, kategorie: str):
        log.info(f"Scrape REWE für: {kategorie}")

        # 1. Cookie-Banner weghauen, falls es da ist
        if page.is_visible("#uc-btn-accept-banner"):
            page.click("#uc-btn-accept-banner")
            page.wait_for_timeout(1000)

        # 2. Markt-Auswahl via PLZ steuern
        if self.plz:
            print(f"[REWE] Stelle Markt auf PLZ {self.plz} ein...")

            # REWE hat oben rechts einen Button "Markt wählen"
            page.click("header #market-chooser-toggle, .market-selector-trigger")
            page.wait_for_selector("input[placeholder*='Postleitzahl']")

            # PLZ eintippen und abschicken
            page.fill("input[placeholder*='Postleitzahl']", self.plz)
            page.press("input[placeholder*='Postleitzahl']", "Enter")

            # Den ersten vorgeschlagenen Markt in der Liste anklicken
            page.wait_for_selector(".market-search-result-list-item, .select-market-btn")
            page.click(".market-search-result-list-item:first-child, .select-market-btn")
            page.wait_for_timeout(2000)  # Kurz warten, bis der Markt geladen ist

            #TODO: Ab hier geht es dann weiter, z. B. mit butter