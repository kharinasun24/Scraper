# main.py
import sys
import threading  # <-- NEU: Für echtes Multithreading

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from core.price import PriceManager
from babel.support import Translations
from core.fuzzy import korrigiere_kategorie

translations = Translations.load(
    dirname='locales',
    locales=['de']  # oder ['en']
)

_ = translations.gettext

from core.logger import get_logger

log = get_logger("main")


def starte_suche_gui(entry_suche, entry_plz, text_output, label_status, btn_start):
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

    # Button deaktivieren, damit man nicht doppelt klickt
    btn_start.config(state=tk.DISABLED)

    # Visuelles Feedback in der GUI
    label_status.config(text=f"Suche nach '{kategorie_ziel}' in {plz} läuft...")
    text_output.delete("1.0", tk.END)
    text_output.insert(tk.END, "Scraper wurden im Hintergrund gestartet...\nBitte kurz warten...\n")

    # NEU: Wir verlagern die rechen- und zeitintensive Suche in einen eigenen Thread
    threading.Thread(
        target=suche_thread_arbeit,
        args=(kategorie_ziel, plz, text_output, label_status, btn_start),
        daemon=True  # Beendet den Thread automatisch, wenn das Fenster geschlossen wird
    ).start()


def suche_thread_arbeit(kategorie_ziel, plz, text_output, label_status, btn_start):
    """Diese Funktion läuft komplett im Hintergrund und blockiert die GUI nicht."""
    try:
        # 2. PriceManager initialisieren
        manager = PriceManager(plz=plz)

        # Scraper-Kette ausführen
        try:
            produkte = manager.alle_produkte(kategorie=kategorie_ziel)
        except Exception as scraper_error:
            log.error(f"Ein Scraper hat das Programm blockiert: {scraper_error}")
            produkte = getattr(manager, 'produkte', [])

            # UI-Interaktion aus dem Thread heraus ist mit root.after am sichersten,
            # aber Tkinter verzeiht direkte einfache Inserts meistens:
            text_output.insert(tk.END, f"⚠️ Warnung: Ein Scraper-Fehler ist aufgetreten.\n")
            text_output.insert(tk.END, f"Details: {scraper_error}\n\nZeige unvollständige Ergebnisse:\n")

        # UI aufräumen und Ergebnisse präsentieren
        text_output.delete("1.0", tk.END)

        if not produkte:
            text_output.insert(tk.END, f"Keine Produkte für '{kategorie_ziel}' gefunden.")
            label_status.config(text="Suche beendet (Keine Ergebnisse).")
            btn_start.config(state=tk.NORMAL)
            return

        # Sortieren
        try:
            produkte.sort(key=lambda p: p.preis)
        except Exception:
            pass

        # 3. Ergebnisse schreiben
        text_output.insert(tk.END, "=" * 50 + "\n")
        text_output.insert(tk.END, f"      --- RESULT {kategorie_ziel.upper()} ---\n")
        text_output.insert(tk.END, "=" * 50 + "\n")

        for p in produkte:
            text_output.insert(tk.END, f"[{p.markt.upper()}] {p.name}: {p.preis:.2f} €\n")

        text_output.insert(tk.END, "=" * 50 + "\n")
        label_status.config(text="Suche abgeschlossen!")

    except Exception as e:
        label_status.config(text="Fehler bei der Suche.")
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, f"Ein kritischer Fehler ist aufgetreten:\n{str(e)}")
        messagebox.showerror("Scraper Fehler", f"Da lief etwas komplett schief: {e}")

    finally:
        # Am Ende den Button in jedem Fall wieder freigeben
        btn_start.config(state=tk.NORMAL)


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
    # HINWEIS: btn_start wird jetzt als Argument übergeben, damit wir ihn deaktivieren können
    btn_start = ttk.Button(
        main_frame,
        text="Preise abfragen"
    )
    btn_start.config(command=lambda: starte_suche_gui(entry_suche, entry_plz, text_output, label_status, btn_start))
    btn_start.pack(fill=tk.X)

    # Startet die GUI-Schleife (hält das Fenster offen)
    root.mainloop()