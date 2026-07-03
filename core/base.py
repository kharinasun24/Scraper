# core/base.py

import os
import getpass
import time
from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright
from typing import List
from core.logger import get_logger

log = get_logger("base_scraper")


class BaseScraper(ABC):
    def __init__(self, start_url: str):
        self.start_url = start_url
        self.zusatz_urls: List[str] = []

    def scrape(self, kategorie: str = "butter") -> list:
        # Initialisiere context als None, um den 'cannot access local variable'-Fehler im finally-Block zu verhindern
        context = None

        with sync_playwright() as p:
            username = getpass.getuser()

            # WICHTIGER FIX: Wir erstellen ein eigenes Unterverzeichnis im AppData-Ordner.
            # Dadurch umgehen wir die "non-default data directory" Sperre von Chrome komplett!
            user_data_dir = f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data\\PlaywrightProfile"

            # Falls der Ordner nicht existiert, erstellt Python ihn vollautomatisch
            os.makedirs(user_data_dir, exist_ok=True)

            log.info(f"Starte isolierten Chrome-Browser mit Profil aus: {user_data_dir}")

            try:
                # Verbinden mit Chrome über den persistenten, isolierten Pfad
                context = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=False,  # Zeigt das Browserfenster
                    channel="chrome",  # Nutzt mein installiertes Google Chrome
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized"
                    ],
                    no_viewport=True
                )

                page = context.pages[0] if context.pages else context.new_page()

                # Zur Startseite surfen
                page.goto(self.start_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(1)

                # Meine Scraper-Logik ausführen
                products = self.extract_logic(page, kategorie)
                return products if isinstance(products, list) else []

            except Exception as e:
                log.error(f"Schwerwiegender Fehler im BaseScraper: {e}")
                return []

            finally:
                # FIX: Nur schließen, wenn der Context auch wirklich erfolgreich erzeugt wurde!
                if context is not None:
                    try:
                        context.close()
                    except Exception:
                        pass

    @abstractmethod
    def extract_logic(self, page, kategorie: str) -> List[dict]:
        pass