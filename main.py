# main.py
import sys

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from core.price import PriceManager
from babel.support import Translations
from core.fuzzy import korrigiere_kategorie

translations = Translations.load(
    dirname='locales',
    locales=['de']   # oder ['en']
)

_ = translations.gettext

from core.logger import get_logger

log = get_logger("main")


def starte_suche_gui(entry_suche, entry_plz, text_output, label_status):

    eingabe = entry_suche.get().strip().lower()
    plz = entry_plz.get().strip().lower()

    # 1. Validierung
    if not eingabe or not plz:
        messagebox.showwarning("Fehlende Angaben", "Bitte gib ein Produkt und eine PLZ ein!")
        return

    kategorie_ziel = korrigiere_kategorie(eingabe)
    if kategorie_ziel is None:
        messagebox.showerror("Fehler", f"Die Kategorie '{eingabe}' kenne ich leider nicht.")
        return

    # Visuelles Feedback in der GUI
    label_status.config(text=f"Suche nach '{kategorie_ziel}' in {plz} läuft...")
    text_output.delete("1.0", tk.END)  # Altes Ergebnis löschen
    text_output.insert(tk.END, "Scraper wurden im Hintergrund gestartet...\nBitte kurz warten...\n")
    text_output.update()

    try:
        # 2. Deine bestehende Logik ausführen
        # (Hinweis: Wenn dein PriceManager die PLZ benötigt, übergib sie hier, z.B. PriceManager(plz=plz))
        manager = PriceManager(plz=plz)
        produkte = manager.alle_produkte(kategorie=kategorie_ziel)


        # Textfeld für die neuen Ergebnisse leeren
        text_output.delete("1.0", tk.END)

        if not produkte:
            text_output.insert(tk.END, f"Keine Produkte für '{kategorie_ziel}' gefunden.")
            label_status.config(text="Suche beendet (Keine Ergebnisse).")
            return

        # Nach Preis sortieren
        produkte.sort(key=lambda p: p.preis)

        # 3. Ergebnisse in das Tkinter-Textfeld schreiben statt ins Terminal
        text_output.insert(tk.END, "=" * 50 + "\n")
        text_output.insert(tk.END, f"      --- RESULT {kategorie_ziel.upper()} ---\n")
        text_output.insert(tk.END, "=" * 50 + "\n")

        for p in produkte:
            text_output.insert(tk.END, f"[{p.markt.upper()}] {p.name}: {p.preis:.2f} €\n")

        text_output.insert(tk.END, "=" * 50 + "\n")
        label_status.config(text="Suche erfolgreich abgeschlossen!")

    except Exception as e:
        label_status.config(text="Fehler bei der Suche.")
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, f"Ein Fehler ist aufgetreten:\n{str(e)}")
        messagebox.showerror("Scraper Fehler", f"Da lief etwas schief: {e}")


if __name__ == "__main__":
    # --- Hier wird das Tkinter-Fenster aufgebaut ---
    root = tk.Tk()
    root.title("Discounter Preis-Vergleicher")
    root.geometry("500x550")

    style = ttk.Style()
    style.theme_use("clam")

    # Hauptframe
    main_frame = ttk.Frame(root, padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Eingabe: Produkt
    ttk.Label(main_frame, text="Nach was wird gesucht?", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 2))
    entry_suche = ttk.Entry(main_frame, font=("Arial", 11))
    entry_suche.pack(fill=tk.X, pady=(0, 10))
    entry_suche.insert(0, "Butter")  # Standard-Vorschlag

    # Eingabe: Postleitzahl
    ttk.Label(main_frame, text="Postleitzahl für die Märkte:", font=("Arial", 10, "bold")).pack(anchor=tk.W,
                                                                                                pady=(0, 2))
    entry_plz = ttk.Entry(main_frame, font=("Arial", 11), width=12)
    entry_plz.pack(anchor=tk.W, pady=(0, 15))
    entry_plz.insert(0, "68161")  # Standard-Vorschlag

    # Ausgabebereich (Textfeld für die Ergebnisse)
    ttk.Label(main_frame, text="Ergebnisse:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 2))
    text_output = tk.Text(main_frame, font=("Courier", 10), height=18, bg="#f8f9fa", relief=tk.SOLID, bd=1)
    text_output.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

    # Status-Zeile ganz unten
    label_status = ttk.Label(root, text="Bereit.", relief=tk.SUNKEN, anchor=tk.W, padding=(5, 5))
    label_status.pack(fill=tk.X, side=tk.BOTTOM)

    # Start-Button (ruft die obige Logik auf und übergibt die GUI-Elemente)
    btn_start = ttk.Button(
        main_frame,
        text="Preise abfragen",
        command=lambda: starte_suche_gui(entry_suche, entry_plz, text_output, label_status)
    )
    btn_start.pack(fill=tk.X)

    # Startet die GUI-Schleife (hält das Fenster offen)
    root.mainloop()