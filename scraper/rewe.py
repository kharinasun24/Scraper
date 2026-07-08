import logging
from typing import List
from bs4 import BeautifulSoup
from core.base import BaseScraper

log = logging.getLogger(__name__)


class ReweScraper(BaseScraper):
    def __init__(self, plz: str = None):
        super().__init__("https://www.rewe.de/shop/", plz=plz)

    def extract_logic(self, page, kategorie: str = "butter") -> List[dict]:
        log.info(f"REWE-Extraktion läuft für Kategorie: {kategorie}...")

        # 1. Hauptseite aufrufen
        log.info(f"Rufe REWE auf: {self.start_url}")
        try:
            page.goto(self.start_url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)
        except Exception as e:
            log.warning(f"Hauptseite laden dauerte lang, fahre fort... {e}")

        # 2. Cookie-Banner per JavaScript restlos entfernen
        try:
            page.evaluate("""
                const root = document.getElementById('usercentrics-root');
                if (root) root.remove();
                const overlay = document.querySelector('.uc-block-ui');
                if (overlay) overlay.remove();
                document.body.style.overflow = 'auto';
            """)
            page.wait_for_timeout(1000)
            log.info("Cookie-Banner erfolgreich entfernt.")
        except Exception as e:
            log.debug(f"Cookie-Bypass fehlgeschlagen: {e}")

        # 3. Marktauswahl (nur wenn PLZ übergeben wurde und der Button da ist)
        if self.plz:
            log.info(f"Versuche Markt auf PLZ {self.plz} einzustellen...")
            try:
                market_btn = page.locator(
                    "header button:has-text('Markt'), button:has-text('Service'), .market-selector-trigger")
                # Wir prüfen, ob der Button sichtbar und KLICKBAR (enabled) ist
                if market_btn.first.is_visible(timeout=3000) and market_btn.first.is_enabled():
                    market_btn.first.click(force=True)
                    page.wait_for_timeout(1500)

                    input_field = page.locator(
                        "input[placeholder*='Postleitzahl'], input[placeholder*='PLZ'], input[id*='market']")
                    if input_field.first.is_visible(timeout=2000):
                        input_field.first.fill(self.plz)
                        page.wait_for_timeout(500)
                        input_field.first.press("Enter")
                        page.wait_for_timeout(1500)

                        # Ersten Markt bestätigen falls nötig
                        select_btn = page.locator("button:has-text('Auswählen'), .select-market-btn").first
                        if select_btn.is_visible(timeout=2000):
                            select_btn.click(force=True)
                            page.wait_for_timeout(2000)
                        log.info(f"Markt erfolgreich auf {self.plz} gesetzt.")
            except Exception as market_error:
                log.warning(f"Marktauswahl übersprungen oder fehlgeschlagen (nicht kritisch): {market_error}")

        # 4. Suche ausführen
        try:
            log.info(f"Suche nach Begriff: {kategorie}")
            search_input = page.locator(
                "input[type='search'], input[name='searchWord'], input[placeholder*='suchen']").first

            search_input.focus()
            search_input.fill(kategorie, force=True)
            page.wait_for_timeout(500)
            search_input.press("Enter")

            # Warten auf Suchergebnisse
            page.wait_for_selector("main, div[class*='product'], div[class*='tiles'], .search-service-productTile",
                                   timeout=12000)

            # Scrollen für Lazy-Loading
            page.evaluate("window.scrollBy(0, 800);")
            page.wait_for_timeout(2000)
        except Exception as e:
            log.error(f"Fehler bei der Ausführung der Suche: {e}")
            return []

        # 5. HTML auslesen & parsen
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        rewe_karten = soup.select(
            "[class*='product-card'], [class*='ProductCard'], [data-testid='product-tile'], article")
        log.info(f"Anzahl gefundener HTML-Strukturen bei REWE: {len(rewe_karten)}")

        alle_produkte = []
        for karte in rewe_karten:
            try:
                name_elem = karte.select_one(
                    "[class*='title'], [class*='Title'], h3, h4, [data-testid='product-title']")
                preis_elem = karte.select_one("[class*='price'], [class*='Price'], [data-testid='product-price']")
                link_elem = karte.select_one("a")

                if not name_elem or not preis_elem:
                    continue

                name = name_elem.get_text(strip=True)
                preis_raw = preis_elem.get_text(strip=True)

                if "€" in preis_raw:
                    preis_raw = preis_raw.split("€")[0]

                preis_clean = preis_raw.replace(",", ".").replace(" ", "").strip()
                preis_digits = "".join([c for c in preis_clean if c.isdigit() or c == "."])

                if not preis_digits:
                    continue
                preis = float(preis_digits)

                if preis > 50.0 and "." not in preis_clean:
                    preis = preis / 100.0

                url = link_elem["href"] if link_elem and link_elem.has_attr("href") else ""
                if url and not url.startswith("http"):
                    url = "https://www.rewe.de" + url

                if name and preis > 0:
                    alle_produkte.append({
                        "name": name,
                        "preis": preis,
                        "url": url,
                        "raw_card": karte
                    })
            except Exception:
                continue

        # 6. Filter & Synonyme
        gefilterte_produkte = []
        suchwort = kategorie.lower()
        synonyme = [suchwort]

        if suchwort == "butter":
            synonyme.extend(["margarine", "kerrygold", "meggle", "milsani", "streichzart", "rama", "butter"])

        for p in alle_produkte:
            produkt_name_original = p["name"]
            produkt_name_lower = produkt_name_original.lower()

            if self.ist_stoppwort(produkt_name_original, kategorie):
                continue

            if any(syn in produkt_name_lower for syn in synonyme):
                gefilterte_produkte.append({
                    "name": produkt_name_original,
                    "preis": p["preis"],
                    "url": p["url"]
                })
                log.info(f"   [REWE-TREFFER] {produkt_name_original} -> {p['preis']:.2f} €")

        # 7. Duplikate entfernen
        seen = set()
        unique = []
        for p in gefilterte_produkte:
            key = (p["name"].lower(), p["preis"])
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique