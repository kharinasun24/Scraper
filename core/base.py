# core/base.py

import os
import tempfile
import getpass
import time
from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright
from typing import List
from core.logger import get_logger

log = get_logger("base_scraper")


class BaseScraper(ABC):

    def __init__(self, url: str, plz: str = None):
    # Wir speichern die übergebene 'url' als 'start_url' ab
        self.start_url = url
        self.plz = plz  # Hier wird die PLZ für alle Kind-Scraper verankert!
        self.zusatz_urls: List[str] = []
        self.stoppwoerter = self._load_stoppwoerter()

    def _load_stoppwoerter(self) -> List[str]:
        """Lädt die Stoppwörter aus einer externen Textdatei, absolut sicher."""
        # Wir testen die 3 wahrscheinlichsten Pfade, wo deine Datei liegen könnte:
        moegliche_pfade = [
            "stoppwoerter.txt",  # Direkt im Hauptordner
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stoppwoerter.txt"),
            # Ein Ordner über core/
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "stoppwoerter.txt")  # Direkt im core/ Ordner
        ]

        for pfad in moegliche_pfade:
            if os.path.exists(pfad):
                try:
                    with open(pfad, "r", encoding="utf-8-sig") as f:
                        inhalt = [line.strip().lower() for line in f if line.strip()]
                        log.info(f"   [BASE SUCCESS] {len(inhalt)} Stoppwörter geladen aus: {os.path.abspath(pfad)}")
                        return inhalt
                except Exception as e:
                    log.error(f"Fehler beim Lesen von {pfad}: {e}")

        log.error("!!! FATAL: stoppwoerter.txt wurde an KEINEM der bekannten Orte gefunden !!!")
        return []

    def ist_stoppwort(self, produkt_name: str, kategorie: str) -> bool:
        """
        Prüft, ob ein Produkt aufgrund eines Stoppworts ignoriert werden soll.
        """
        # SICHERHEITS-NETZ: Falls die Liste aus irgendeinem Grund leer war,
        # versuchen wir jetzt beim ersten echten Filter-Einsatz noch einmal, sie zu laden!
        if not self.stoppwoerter:
            self.stoppwoerter = self._load_stoppwoerter()

        if kategorie.lower() == "butter":
            name_lower = produkt_name.lower().replace("-", "").strip()

         # Wenn sie IMMER NOCH leer ist, füllen wir sie manuell mit den wichtigsten Notfall-Wörtern,
         # damit mein Scraper JETZT SOFORT funktioniert, selbst wenn die Textdatei gelöscht wurde!
            effektive_stoppwoerter = self.stoppwoerter if self.stoppwoerter else ["keks", "schmalz", "milch", "toast",
                                                                                  "waffel"]

            for sw in effektive_stoppwoerter:
                sauberes_stoppwort = sw.strip().lower()
                if not sauberes_stoppwort:
                    continue

                if sauberes_stoppwort in name_lower:
                    log.info(f"   [STOPPWORT BLOCK] '{sauberes_stoppwort}' hat '{produkt_name}' blockiert!")
                    return True
        return False

    def scrape(self, kategorie: str = "butter") -> list:
        # Initialisiere context als None, um den 'cannot access local variable'-Fehler im finally-Block zu verhindern
        context = None

        with sync_playwright() as p:
            username = getpass.getuser()

            #user_data_dir = f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data\\PlaywrightProfile"

            # 1. Namen des Scrapers holen (z.B. aldiscraper)
            scraper_name = self.__class__.__name__.lower()

            # 2. RADIKAL-FIX: Ich meide den Benutzer-Ordner komplett wegen DOS-8.3-Kürzeln (A591F~1.GOE)
            user_data_dir = f"C:\\playwright_profiles\\profile_{scraper_name}"

            log.info(f"Nutze isoliertes Profil-Verzeichnis: {user_data_dir}")

            # Kleiner Kontroll-Log, damit du genau siehst, wo er hinspringt:
            log.info(f"Nutze isoliertes Profil-Verzeichnis: {user_data_dir}")

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

        # Zur Startseite surfen - page goto machen aber die Kindklassen, hier will ich also Ressourcen schonen, daher habe ich das ding auskommentiert.

                #page.goto(self.start_url, wait_until="domcontentloaded", timeout=30000)
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