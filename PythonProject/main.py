import re
from bs4 import BeautifulSoup
from core.price import PriceManager

# 1. ALLE DEINE KATALOGE AN EINEM ORT
KATALOGE = {
    "butter": {
        "arla": ["kærg", "krg"],
        "kerrygold": ["butter", "original"]
    },
    "kefir": { #Das hier ist rein fiktiv!
        "milprima": ["kefir", "mild"],
        "mueller": ["kefir", "mild", "kalinka"],
        "müller": ["kefir", "mild", "kalinka"]
    }
}

if __name__ == "__main__":

    print("=" * 40)
    # Wir fragen nach der Kategorie (z.B. 'butter' oder 'saft')
    kategorie_ziel = input("Nach welcher Produktgruppe suchst du? (z.B. butter, kefir, ...): ").lower().strip()
    print("=" * 40)

    # Prüfen, ob wir für diese Kategorie überhaupt Daten haben
    if kategorie_ziel not in KATALOGE:
        print(f"Fehler: Für '{kategorie_ziel}' ist kein Katalog hinterlegt!")
        exit()

    # HIER PASSIERT DER "CASE-SWITCH": Python holt sich genau den richtigen Katalog!
    aktiver_katalog = KATALOGE[kategorie_ziel]

    manager = PriceManager()
    rohe_marktdaten = manager.alle_preise_abrufen()

    print(f"\nStarte Vergleich für die Kategorie: {kategorie_ziel.capitalize()}")

###########################################################################

    vergleichs_liste = []

    for markt_name, daten in rohe_marktdaten.items():
        if not daten:
            continue

        if markt_name == "Penny":
            soup = BeautifulSoup(daten, "html.parser")
            gesehene_produkte = set()

            # Wir iterieren jetzt NUR durch den zuvor ausgewählten Katalog!
            for haupt_begriff, unter_begriffe in aktiver_katalog.items():
                kacheln = soup.find_all(string=re.compile(haupt_begriff, re.IGNORECASE))

                for treffer in kacheln:
                    parent = treffer.parent
                    while parent and parent.name != "body":
                        parent_text = parent.get_text().lower()

                        if any(sub.lower() in parent_text for sub in unter_begriffe):
                            if "€" in parent_text:
                                preise_im_text = re.findall(r'\b\d+[\.,]\d{2}\b', parent_text)
                                if preise_im_text:
                                    try:
                                        preis = float(preise_im_text[0].replace(",", "."))
                                        if preis > 0:
                                            identifikator = (haupt_begriff, preis)

                                            if identifikator not in gesehene_produkte:
                                                gesehene_produkte.add(identifikator)

                                                vergleichs_liste.append({
                                                    "markt": markt_name,
                                                    # Schreibt dynamisch z.B. "Arla Butter" oder "Hohes C Saft"
                                                    "produkt": f"{haupt_begriff.capitalize()} {kategorie_ziel.capitalize()}",
                                                    "preis": preis
                                                })
                                            break
                                    except ValueError:
                                        pass
                        parent = parent.parent

        elif markt_name == "Aldi":
            # Hier würdest du die Aldi-HTML-Struktur parsen, die du von aldi.py bekommen hast
            # (Das ist nur ein fiktives Beispiel, je nachdem wie aldi.py aufgebaut ist)
            pass

            # 3. Sortieren und Ergebnis ausgeben

        # Endergebnis sortiert ausgeben
        if vergleichs_liste:
            vergleichs_liste.sort(key=lambda x: x["preis"])
            print("\n" + "=" * 40)
            print("      --- PREISVERGLEICH ERGEBNIS ---")
            print("=" * 40)
            for eintrag in vergleichs_liste:
                print(f"[{eintrag['markt'].upper()}] {eintrag['produkt']}: {eintrag['preis']:.2f} €")
            print("=" * 40)
        else:
            print(f"\nIn dieser Kategorie wurden keine Angebote gefunden.")
