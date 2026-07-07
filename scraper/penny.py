import time
import re

from core.base import BaseScraper
from core.products import Product
from bs4 import BeautifulSoup
from babel.support import Translations
translations = Translations.load(
    dirname='locales',
    locales=['de']   # oder ['en']
)

_ = translations.gettext

from core.logger import get_logger

log = get_logger("penny")

class PennyScraper(BaseScraper):
    def __init__(self, plz: str = None):
        super().__init__("https://www.penny.de/angebote", plz=plz)

        # Hier definieren wir alle zusätzlichen URLs, die wir AUCH noch abgrasen wollen
        self.zusatz_urls = [
            "https://www.penny.de/sortiment/",
            "https://www.penny.de/sortiment/milprima",
            "https://www.penny.de/angebote/#ab-montag--kuehlregal",
            "https://www.penny.de/angebote/#ab-dienstag--kuehlregal",
            "https://www.penny.de/angebote/#ab-mittwoch--kuehlregal",
            "https://www.penny.de/angebote/#ab-donnerstag--kuehlregal",
            "https://www.penny.de/angebote/#ab-freitag--kuehlregal",
            "https://www.penny.de/angebote/#ab-samstag--kuehlregal"
        ]

    def _parse_page(self, page) -> list:
        """Extrahiert Produkte von einer Penny-Seite mit präziser Elementen-Trennung und raw_card."""
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        produkte = []

        # Wir nehmen meine funktionierenden Produktkarten-Selektoren
        produkt_karten = soup.find_all(["div", "article", "li"], class_=lambda x: x and any(
            keyword in x.lower() for keyword in ["product", "angebot", "tile", "card", "item"]
        ))

        if not produkt_karten:
            produkt_karten = soup.find_all(["div", "section"], class_=lambda x: x and any(
                k in (x.lower() if x else "") for k in ["offer", "product", "promo"]
            ))

        log.info(f"Gefundene potenzielle Produktkarten: {len(produkt_karten)}")

        for karte in produkt_karten:
            try:
                # 1. NAME EXTRAHIEREN (Präzise aus Überschrift)
                name_tag = (
                        karte.find(["h2", "h3", "h4", "strong", "a"], class_=lambda x: x and any(
                            w in (x.lower() if x else "") for w in ["title", "name", "heading", "product"]
                        ))
                        or karte.find(["h2", "h3", "h4"])
                )

                if not name_tag:
                    continue
                name = name_tag.get_text(strip=True)

                if not name or len(name) < 3:
                    continue

                # 2. PREIS EXTRAHIEREN (Wir suchen gezielt nach dem Preis-Element)
                preis_tag = karte.find(class_=lambda x: x and "price" in x.lower() and "base" not in x.lower())

                if not preis_tag:
                    preis_tag = karte.find(string=re.compile(r'€|EUR'))

                if not preis_tag:
                    continue

                preis_text = preis_tag.get_text()
                preise = re.findall(r'\b\d+[.,]\d{2}\b', preis_text)

                if not preise:
                    continue

                preis_str = preise[0].replace(",", ".")
                preis = float(preis_str)

                # 3. URL EXTRAHIEREN
                link_tag = karte.find("a", href=True)
                url = link_tag["href"] if link_tag else ""
                if url and not url.startswith("http"):
                    url = "https://www.penny.de" + url

                # HIER IST DIE RETTUNG: raw_card wieder mit aufnehmen!
                produkte.append({
                    "name": name,
                    "preis": preis,
                    "url": url,
                    "raw_card": karte
                })

            except Exception:
                continue

        return produkte

    def extract_logic(self, page, kategorie: str = "butter"):
        log.info("Penny-Extraktion läuft...")

        # =========================================================================
        # NEU: REGIONALE MARKT-AUSWAHL GANZ AM ANFANG
        # =========================================================================
        try:
            # 1. Cookie-Banner weghauen, falls es da ist
            if page.is_visible("#onetrust-accept-btn-handler"):
                log.info("Penny Cookie-Banner erkannt, akzeptiere...")
                page.click("#onetrust-accept-btn-handler")
                page.wait_for_timeout(1000)

            # 2. Markt mit der zentralen PLZ aus der Basisklasse auswählen
            if self.plz:
                log.info(f"Stelle Penny-Markt auf PLZ {self.plz} ein...")

                # Klick auf den Markt-Wähler oben in der Navigation
                # (Penny nutzt oft diese Klassen oder IDs für den Picker)
                page.click(".market-navigation__button, #market-picker-trigger, .header-market-search")
                page.wait_for_selector("input.market-search__input, input[placeholder*='PLZ']")

                # PLZ eintippen und abschicken
                page.fill("input.market-search__input, input[placeholder*='PLZ']", self.plz)
                page.press("input.market-search__input, input[placeholder*='PLZ']", "Enter")

                # Den ersten vorgeschlagenen Markt in der Liste anklicken
                page.wait_for_selector(".market-search__result-item .btn, .penny-market-select-btn")
                page.click(".market-search__result-item .btn, .penny-market-select-btn")

                # Wichtig: Kurz warten, damit Penny die Seite mit den neuen regionalen Preisen neu lädt
                page.wait_for_timeout(2500)

        except Exception as market_error:
            # Falls sich ein Selektor geändert hat, bricht nicht der ganze Scraper ab,
            # sondern nutzt die Standard-Preise
            log.warning(f"Marktauswahl bei Penny fehlgeschlagen (nutze Standard-Preise): {market_error}")

        # =========================================================================
        # ENDE NEUER BLOCK - AB HIER DEIN ORIGINALER CODE
        # =========================================================================

        alle_produkte = []

        # 1. Alle Produkte von allen Seiten einsammeln
        alle_produkte.extend(self._parse_page(page))

        for url in self.zusatz_urls:
            try:
                log.info(f"Öffne zusätzlich: {url}")
                page.goto(url, wait_until="networkidle")
                time.sleep(2.5)
                alle_produkte.extend(self._parse_page(page))
            except Exception as e:
                log.error(f"Fehler bei Zusatz-URL {url}: {e}")

        # 2. INTELLIGENTER FILTER
        gefilterte_produkte = []
        suchwort = kategorie.lower()

        # Falls nach Butter gesucht wird, erweitern wir die Schlagworte automatisch
        synonyme = [suchwort]
        if suchwort == "butter":
            synonyme.extend(["margarine", "kerrygold", "meggle", "milsani", "streichzart", "kaerntnermilch"])

        for p in alle_produkte:
            produkt_name_original = p["name"]
            produkt_name_lower = produkt_name_original.lower()

            karte_text = p["raw_card"].get_text().lower()
            karte_html = str(p["raw_card"]).lower()

            # 1. ZENTRALE PRÜFUNG ÜBER DIE BASISKLASSE:
            if self.ist_stoppwort(produkt_name_original, kategorie):
                continue

            # 2. SYNONYM- UND RELEVANZ-FILTER
            if any(syn in produkt_name_lower or syn in karte_text or syn in karte_html for syn in synonyme):
                sauberes_produkt = {
                    "name": produkt_name_original,
                    "preis": p["preis"],
                    "url": p["url"]
                }
                gefilterte_produkte.append(sauberes_produkt)
                log.info(f"   [TREFFER] {produkt_name_original} -> {p['preis']:.2f} €")

        # 3. Duplikate entfernen
        seen = set()
        unique = []
        for p in gefilterte_produkte:
            key = (p["name"].lower(), p["preis"])
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique