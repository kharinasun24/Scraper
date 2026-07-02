# scraper/base.py
from playwright.sync_api import sync_playwright


class BaseScraper:
    def __init__(self, url):
        self.url = url

    def get_product_data(self):
        """Die Schablonen-Methode: Steuert den gesamten Ablauf."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"Öffne {self.url}...")
            page.goto(self.url)
            page.wait_for_timeout(5000)  # Standard-Wartezeit für JS-Inhalte

            # Hier springen wir in die spezifische Logik des jeweiligen Marktes!
            raw_data = self.extract_logic(page)

            browser.close()
            return raw_data

    def extract_logic(self, page):
        """Muss von jeder Supermarkt-Klasse selbst überschrieben werden!"""
        raise NotImplementedError("Jeder Scraper muss seine eigene extract_logic definieren!")

