# core/base.py

import time

from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright
from typing import List

class BaseScraper(ABC):
    def __init__(self, start_url: str):
        self.start_url = start_url
        self.zusatz_urls: List[str] = []


    def scrape(self, kategorie: str = "butter") -> list:

        with sync_playwright() as p:
            # 1. WICHTIG: headless=False, damit ALDI uns nicht blockiert!
            # 'args' schaltet die internen "Ich bin ein Bot"-Flaggen von Chromium aus.
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )

            # 2. Wir erstellen den Browser-Kontext mit einem echten User-Agent
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            page = context.new_page()

            try:
                products = self.extract_logic(page, kategorie)
                return products if isinstance(products, list) else []
            finally:
                browser.close()

    @abstractmethod
    def extract_logic(self, page, kategorie: str) -> List[dict]:
        pass