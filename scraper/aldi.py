from core.base import BaseScraper
from bs4 import BeautifulSoup
import re

from babel.support import Translations
translations = Translations.load(
    dirname='locales',
    locales=['de']   # oder ['en']
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

        # HIER LIEGT DER FEHLER: Dieses return MUSS außerhalb von try/except stehen!
        return produkte

    ############################################################

    def _collect_product_links(self, page, kategorie):

        search_url = (
            f"https://www.aldi-sued.de/de/suchergebnisse.html?searchterm={kategorie}"
        )

        page.goto(search_url)

        page.wait_for_load_state("networkidle")

        soup = BeautifulSoup(page.content(), "html.parser")

        links = set()

        for a in soup.find_all("a", href=True):

            href = str(a["href"])

            if "/produkt/" not in href:
                continue

            if href.startswith("/"):

                href = "https://www.aldi-sued.de" + href

            links.add(href)

        return links

    ############################################################

    # FIX 2: kategorie hier in der Methodendefinition eintragen!
    def _parse_product_page(self, page, kategorie):

        html = page.content()

        soup = BeautifulSoup(html, "html.parser")

        ##############################################
        # NAME
        ##############################################

        title = soup.select_one(".product-details__title")

        if not title:

            print(_("   Kein Produktname gefunden."))

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

        # Quick & Dirty: Wenn das Suchwort nicht im Text vorkommt, gib nix zurück
        if kategorie.lower() not in ausgabe_text.lower():
            return None

        # Wenn es doch drin ist: Drucken und Produkt zurückgeben!
        log.info(ausgabe_text)

        return {
            "name": vollstaendiger_name,
            "preis": preis,
            "url": url
        }