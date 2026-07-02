import sys
from rapidfuzz import process

kategorien = ["butter", "kefir", "milch", "joghurt", "pizza"]

def korrigiere_kategorie(eingabe: str) -> str | None:
    eingabe = eingabe.lower().strip()

    # exakter Treffer
    if eingabe in kategorien:
        return eingabe

    # fuzzy matching
    treffer, score, _ = process.extractOne(eingabe, kategorien)

    if score > 80:
        return treffer

    return None
