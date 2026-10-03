#!/usr/bin/env python3
"""
Werkstatt-Kapazitätsmodell -- Datenbank anlegen.

Aufruf:  python init_db.py

Legt die Datei werkstatt.db im selben Verzeichnis an, lädt Schema und
Demodaten und gibt zur Kontrolle den Katalog aus.

Jeder Aufruf beginnt von vorn -- schema.sql startet mit DROP TABLE.
Die Datenbank ist eine generierte Datei und gehört nicht ins Repository.

Danach:  python schaetzung.py 4412
         python report.py
"""

import sqlite3
import sys
from pathlib import Path

HIER = Path(__file__).parent
DB = HIER / "werkstatt.db"
SQL_DATEIEN = ("schema.sql", "seed_demo.sql")


def sql_ausfuehren(conn, dateiname):
    pfad = HIER / dateiname
    if not pfad.exists():
        sys.exit(f"Datei fehlt: {pfad}")
    conn.executescript(pfad.read_text(encoding="utf-8"))
    print(f"  {dateiname} ausgeführt")


def main():
    print(f"Datenbank: {DB}")
    conn = sqlite3.connect(DB)
    try:
        conn.execute("PRAGMA foreign_keys = ON")

        for datei in SQL_DATEIEN:
            sql_ausfuehren(conn, datei)
        conn.commit()

        # --- Kontrolle: was steht im Katalog? ------------------------
        print("\n--- arbeitsvorgang ---")
        zeilen = conn.execute("""
            SELECT code, bezeichnung, basiszeit_min, streuung_pct, parent_id
            FROM arbeitsvorgang
            ORDER BY id
        """).fetchall()

        for code, bez, zeit, streu, parent in zeilen:
            einzug = "  └ " if parent is not None else ""
            # Elternvorgänge tragen keine eigene Zeit (basiszeit_min IS NULL).
            # Bewusst "is not None": ein Vorgang mit 0 min ist kein Elternvorgang.
            dauer = f"{zeit:.0f} min" if zeit is not None else "(Eltern)"
            streuung = f"±{streu:.0%}" if streu is not None else ""
            print(f"{einzug}{code:24} {dauer:>10}  {streuung:>5}  {bez}")

        print(f"\n{len(zeilen)} Vorgänge im Katalog.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
