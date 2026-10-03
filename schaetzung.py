#!/usr/bin/env python3
"""
Werkstatt-Kapazitätsmodell -- Schätzung für eine Karte.

Aufruf:  python schaetzung.py 4412

Ablauf:
  1. Die Positionen der Karte werden bis zu den BLÄTTERN aufgelöst
     (rekursive Abfrage). Ein Elternvorgang trägt keine eigene Zeit,
     seine Teilvorgänge tragen sie.
  2. Der Modellfaktor wird aufmultipliziert (fehlende Zeile = 1.0).
     Alters- und Fähigkeitsfaktor sind im Modell vorgesehen, in
     Version 0.1 aber noch nicht umgesetzt (siehe README).
  3. Die Zeiten werden je Fachgebiet summiert.
  4. Die Streuung (streuung_pct) ist eine Standardabweichung (1σ).
     Sie wird NICHT linear addiert, sondern quadratisch (RSS).
     Nicht jede Position trifft am selben Tag den schlechten Fall.
"""

import sqlite3
import sys
from math import sqrt
from pathlib import Path

DB = Path(__file__).parent / "werkstatt.db"
STANDARD_KARTE = 4412

# Rekursive Abfrage: von den Positionen der Karte abwärts bis zum Blatt.
SQL = """
WITH RECURSIVE baum(av_id, menge) AS (

    -- Startpunkt: was auf der Karte steht
    SELECT p.arbeitsvorgang_id, p.menge
    FROM auftrag_position p
    WHERE p.auftrag_id = :auftrag_id

    UNION ALL

    -- jeder Schritt: die Kinder.
    -- Menge des Kindes = Menge des Elternvorgangs * eigene Anzahl
    -- (z.B. Bremsbacken je SEITE, Elternvorgang je ACHSE -> Faktor 2)
    SELECT a.id, b.menge * a.menge_je_eltern
    FROM baum b
    JOIN arbeitsvorgang a ON a.parent_id = b.av_id
)
SELECT
    a.code,
    a.bezeichnung,
    a.fachgebiet_id,
    a.basiszeit_min,
    COALESCE(a.streuung_pct, 0.0)  AS streuung_pct,
    COALESCE(mf.faktor, 1.0)       AS modell_faktor,
    b.menge
FROM baum b
JOIN arbeitsvorgang a  ON a.id = b.av_id
JOIN auftrag t         ON t.id = :auftrag_id
LEFT JOIN modell_faktor mf
       ON mf.arbeitsvorgang_id = a.id
      AND mf.fahrzeugmodell_id = t.fahrzeugmodell_id
WHERE a.basiszeit_min IS NOT NULL      -- nur Blätter
ORDER BY a.id
"""


def karte_aus_argumenten(argv):
    """Kartennummer aus der Kommandozeile lesen, mit klarer Fehlermeldung."""
    if len(argv) < 2:
        return STANDARD_KARTE
    try:
        return int(argv[1])
    except ValueError:
        sys.exit(f"Ungültige Kartennummer: {argv[1]!r} (erwartet: Zahl, z.B. 4412)")


def main(auftrag_id):
    if not DB.exists():
        sys.exit("Datenbank fehlt. Bitte zuerst ausführen:  python init_db.py")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        kopf = conn.execute("""
            SELECT t.kartennummer, t.fehlerbeschreibung, t.baujahr,
                   f.hersteller, f.modell, f.ist_hausmarke
            FROM auftrag t
            LEFT JOIN fahrzeugmodell f ON f.id = t.fahrzeugmodell_id
            WHERE t.id = ?
        """, (auftrag_id,)).fetchone()

        if kopf is None:
            print(f"Karte nicht gefunden: {auftrag_id}")
            return

        marke = "Hausmarke" if kopf["ist_hausmarke"] else "Fremdfabrikat"
        print(f"\nKarte {kopf['kartennummer']} -- "
              f"{kopf['hersteller']} {kopf['modell']} ({kopf['baujahr']}, {marke})")
        print(f"{kopf['fehlerbeschreibung']}\n")

        zeilen = conn.execute(SQL, {"auftrag_id": auftrag_id}).fetchall()
        if not zeilen:
            print("Keine Positionen auf dieser Karte.")
            return

        print(f"{'Vorgang':<24}{'Basis':>7}{'Mng':>6}{'Fakt':>6}{'Zeit':>8}{'±':>7}")
        print("-" * 58)

        summe = 0.0
        varianz = 0.0                  # Summe der QUADRATE der Streuungen
        naiv = 0.0                     # lineare Summe, nur zum Vergleich
        je_fach = {}

        for z in zeilen:
            zeit = z["basiszeit_min"] * z["modell_faktor"] * z["menge"]
            abw = zeit * z["streuung_pct"]     # absolute Streuung (1σ) in Minuten

            summe += zeit
            # KERN DES MODELLS: Varianzen werden addiert, nicht Streuungen.
            varianz += abw ** 2
            naiv += abw

            fg = je_fach.setdefault(z["fachgebiet_id"], [0.0, 0.0])
            fg[0] += zeit
            fg[1] += abw ** 2

            print(f"{z['code']:<24}{z['basiszeit_min']:>6.0f}m"
                  f"{z['menge']:>6.1f}{z['modell_faktor']:>6.2f}"
                  f"{zeit:>7.0f}m{abw:>6.0f}m")

        # Wurzel aus der Summe der Quadrate (RSS) -- NICHT lineare Addition.
        gesamt_abw = sqrt(varianz)

        print("-" * 58)
        print(f"{'GESAMT':<24}{'':>7}{'':>6}{'':>6}{summe:>7.0f}m{gesamt_abw:>6.0f}m")
        print(f"\n  Schätzung: {summe/60:.1f} h   "
              f"(Bereich ±1σ: {(summe-gesamt_abw)/60:.1f} - {(summe+gesamt_abw)/60:.1f} h)")

        # Zum Vergleich: die naive lineare Addition überschätzt die Unsicherheit.
        print(f"  (linear addiert wären es ±{naiv:.0f} min, "
              f"korrekt sind ±{gesamt_abw:.0f} min)")

        print("\n  Je Fachgebiet:")
        for fg, (zeit, var) in sorted(je_fach.items()):
            print(f"    {fg:<22}{zeit/60:>5.1f} h  ± {sqrt(var)/60:.1f} h")
    finally:
        conn.close()


if __name__ == "__main__":
    main(karte_aus_argumenten(sys.argv))
