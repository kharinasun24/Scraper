# main.py
import sys

from core.price import PriceManager
from babel.support import Translations
translations = Translations.load(
    dirname='locales',
    locales=['de']   # oder ['en']
)

_ = translations.gettext

from core.fuzzy import korrigiere_kategorie

if __name__ == "__main__":

    print(_("Nach was wird gesucht?"))

    eingabe = input("butter, kefir, milch, joghurt, pizza ?")

    kategorie_ziel = korrigiere_kategorie(eingabe)

    if kategorie_ziel is None:
        print(_("Eine solche Kategorie kenne ich nicht."))
        sys.exit()

    manager = PriceManager()
    produkte = manager.alle_produkte(kategorie=kategorie_ziel)

    if not produkte:
        print(_("Keine Produkte gefunden."))
        exit()

    # Nach Preis sortieren
    produkte.sort(key=lambda p: p.preis)

    print("\n" + "=" * 50)
    print(f"      --- RESULT {kategorie_ziel.upper()} ---")
    print("=" * 50)
    for p in produkte:
        print(f"[{p.markt.upper()}] {p.name}: {p.preis:.2f} €")
    print("=" * 50)