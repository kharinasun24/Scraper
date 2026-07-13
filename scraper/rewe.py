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

        # 1. Globale REWE-Suchseite direkt aufrufen
        direkt_such_url = f"https://www.rewe.de/suche/uebersicht?searchTerm={kategorie}&searchtype=standardSearch"
        log.info(f"Rufe korrekte REWE-Such-URL auf: {direkt_such_url}")
        try:
            page.goto(direkt_such_url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(3000)
        except Exception as e:
            log.warning(f"Direktaufruf dauerte lang, fahre fort... {e}")

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

        # =====================================================================
        # 3. Aggressiver PLZ- / Markt-Auswahl-Bypass
        # =====================================================================
        aktuelle_plz = self.plz if self.plz else "68161"
        log.info(f"Prüfe auf Markt-Auswahl Overlay (PLZ: {aktuelle_plz})...")

        try:
            plz_selectors = [
                "input[placeholder*='Postleitzahl']",
                "input[placeholder*='PLZ']",
                "input[id*='market-search']",
                "input[id*='plz']",
                ".uc-marketplace-input",
                "input[type='text']"
            ]

            plz_feld = None
            for sel in plz_selectors:
                locator = page.locator(sel).first
                if locator.is_visible(timeout=1500):
                    plz_feld = locator
                    log.info(f"PLZ-Eingabefeld gefunden via: {sel}")
                    break

            if plz_feld:
                plz_feld.click(force=True)
                plz_feld.fill("", force=True)
                plz_feld.type(aktuelle_plz, delay=100)
                page.wait_for_timeout(500)
                plz_feld.press("Enter")
                page.wait_for_timeout(2000)

                btn_selectors = [
                    "button:has-text('Markt auswählen')",
                    "button:has-text('Auswählen')",
                    "button:has-text('Speichern')",
                    "button[type='submit']",
                    ".uc-marketplace-submit"
                ]
                for btn_sel in btn_selectors:
                    btn_locator = page.locator(btn_sel).first
                    if btn_locator.is_visible(timeout=1500):
                        log.info(f"Klicke Bestätigungsbutton: {btn_sel}")
                        btn_locator.click(force=True)
                        page.wait_for_timeout(3000)
                        break
        except Exception as e:
            log.debug(f"Keine PLZ-Abfrage blockiert den Weg: {e}")

        # =====================================================================
        # 4. Suchergebnisse verifizieren & nachladen
        # =====================================================================
        try:
            log.info("Warte auf Suchergebnisse der Produkte...")

            # KORREKTUR: Wir warten nur darauf, dass die Elemente im DOM existieren (state="attached")
            page.wait_for_selector(
                "main, div[class*='product'], div[class*='tiles'], [data-testid='product-tile'], .spr-landing-page-products-grid",
                timeout=15000,
                state="attached"
            )
            page.wait_for_timeout(2000)

            log.info("Scrolle nach unten, um dynamische Inhalte zu laden...")
            for i in range(5):
                page.evaluate("window.scrollBy(0, 1000);")
                page.wait_for_timeout(1500)

            log.info("Scrollen beendet. Übergebe an HTML-Auswertung.")

        except Exception as e:
            log.error(f"Fehler beim Laden der Suchergebnis-Seite: {e}")
            try:
                page.screenshot(path="rewe_error_fallback.png")
                log.info("Fehler-Screenshot 'rewe_error_fallback.png' wurde gespeichert.")
            except:
                pass
            return []

        # =====================================================================
        # 5. HTML auslesen & parsen
        # =====================================================================
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

        # =====================================================================
        # 6. Filter & Synonyme
        # =====================================================================
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

        # =====================================================================
        # 7. Duplikate entfernen
        # =====================================================================
        seen = set()
        unique = []
        for p in gefilterte_produkte:
            key = (p["name"].lower(), p["preis"])
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique