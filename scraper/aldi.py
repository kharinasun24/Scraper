from core.base import BaseScraper
from bs4 import BeautifulSoup
import re
import time

from babel.support import Translations

translations = Translations.load(
    dirname='locales',
    locales=['de']  # oder ['en']
)

_ = translations.gettext

from core.logger import get_logger

log = get_logger("aldi")


class AldiScraper(BaseScraper):

    def __init__(self):
        super().__init__("https://www.aldi-sued.de")

    def extract_logic(self, page, kategorie="butter"):

        log.info(f"\n========== ALDI: Suche nach '{kategorie}' ==========")

        produkt_links = self._collect_product_links(page, kategorie)

        log.info(f"{len(produkt_links)} Produktseiten gefunden.\n")

        produkte = []

        for url in sorted(produkt_links):
            try:
                log.info(f"Öffne Produktseite: {url}")
                page.goto(url, wait_until="networkidle", timeout=30000)

                # kategorie wird übergeben
                produkt = self._parse_product_page(page, kategorie)

                if produkt:
                    produkte.append(produkt)

            except Exception as e:
                log.error(f"Fehler bei URL {url}: {e}")

        return produkte

    ############################################################

    def _collect_product_links(self, page, kategorie):
        # Das Suchwort wird nun voll übergeben (kein Abschneiden zu "pizz" mehr)
        suchbegriff = kategorie.strip()
        direkte_produkt_links = set()

        # FIX: Exakt die URL-Struktur, die du im Browser siehst
        search_url = f"https://www.aldi-sued.de/suchergebnisse?q={suchbegriff}"
        log.info(f"[ALDI] Rufe Suchseite über echtes Profil auf: {search_url}")

        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(3000) # Kurz warten, bis die Kacheln geladen sind

            # 3x sanft scrollen für das Lazy-Loading der Produkte
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 1500)")
                page.wait_for_timeout(1000)

            soup = BeautifulSoup(page.content(), "html.parser")

            # LINKS EXTRAHIEREN
            for a in soup.find_all("a", href=True):
                href = str(a["href"])
                link_text = a.get_text(" ", strip=True).lower()

                # Systemseiten ignorieren
                ignoriere = ["/k/", "/kategorie/", "/c/", "filter=", "hilfe", "impressum", "datenschutz"]
                if any(x in href.lower() for x in ignoriere):
                    continue

                # Prüfen, ob der Link oder Text relevant ist
                ist_relevant = (
                        suchbegriff.lower() in link_text
                        or href.lower().find(suchbegriff.lower()) != -1
                )

                # Typische ALDI-Produktmerkmale in der URL
                ist_produkt_pfad = "/p." in href or "/p/" in href or "/produkte/" in href

                if ist_relevant or ist_produkt_pfad:
                    if href.startswith("/"):
                        href = "https://www.aldi-sued.de" + href

                    if "aldi-sued.de" in href and "/suchergebnisse" not in href:
                        direkte_produkt_links.add(href)

        except Exception as e:
            log.error(f"[ALDI] Fehler beim Sammeln der Produktlinks: {e}")

        log.info(f"[ALDI] Fertig! {len(direkte_produkt_links)} echte Produktlinks extrahiert.")
        return direkte_produkt_links

    ############################################################

    def _parse_product_page(self, page, kategorie):

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        ##############################################
        # NAME
        ##############################################
        title = soup.select_one(".product-details__title")
        if not title:
            log.info("Kein Produktname gefunden.")
            return None

        name = title.get_text(" ", strip=True)

        ##############################################
        # PREIS
        ##############################################
        preis_tag = soup.select_one(".base-price__regular")
        if not preis_tag:
            print("   Kein Preis gefunden.")
            return None

        preis_text = preis_tag.get_text(" ", strip=True)
        match = re.search(r"\d+[.,]\d{2}", preis_text)
        if not match:
            print(_("   Preis konnte nicht gelesen werden."))
            return None

        preis = float(match.group().replace(",", "."))

        ##############################################
        # MARKE
        ##############################################
        brand = ""
        brand_tag = soup.select_one(".product-details__brand")
        if brand_tag:
            brand = brand_tag.get_text(" ", strip=True)

        ##############################################
        # URL
        ##############################################
        url = page.url

        ##############################################
        vollstaendiger_name = f"{brand} {name}".strip()
        ausgabe_text = f"   {vollstaendiger_name} -> {preis:.2f} €"

        # Suchbegriff-Filter für den finalen Output
        if kategorie.lower() == "pizza":
            kategorie = "pizz"

        if kategorie.lower() not in ausgabe_text.lower():
            return None

        log.info(ausgabe_text)

        return {
            "name": vollstaendiger_name,
            "preis": preis,
            "url": url
        }