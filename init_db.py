#!/usr/bin/env python3
"""
Werkstatt-Kapazitätsmodell -- Datenbank anlegen.

Aufruf:  python init_db.py

Legt die Datei werkstatt.db im selben Verzeichnis an, lädt Schema und
Demodaten und gibt zur Kontrolle den Katalog aus.

Jeder Aufruf beginnt bei NULL -- schema.sql startet mit DROP TABLE.
Die Datenbank ist eine generierte Datei und gehört nicht ins Repository.
"""

import sqlite3
from pathlib import Path

HIER = Path(__file__).parent
DB = HIER / "werkstatt.db"


def sql_ausfuehren(conn, dateiname):
    text = (HIER / dateiname).read_text(encoding="utf-8")
    conn.executescript(text)
    print(f"  {dateiname} ausgeführt")


def main():
    print(f"Datenbank: {DB}")
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")

    sql_ausfuehren(conn, "schema.sql")
    sql_ausfuehren(conn, "seed_demo.sql")
    conn.commit()

    # --- Kontrolle: was steht im Katalog? ----------------------------
    print("\n--- arbeitsvorgang ---")
    zeilen = conn.execute("""
        SELECT code, bezeichnung, basiszeit_min, streuung_pct, parent_id
        FROM arbeitsvorgang
        ORDER BY id
    """).fetchall()

    for code, bez, zeit, streu, parent in zeilen:
        einzug = "  └ " if parent else ""
        # Elternvorgänge tragen keine eigene Zeit
        dauer = f"{zeit:.0f} min" if zeit else "(Eltern)"
        print(f"{einzug}{code:24} {dauer:>10}  ±{streu:.0%}  {bez}")

    print(f"\n{len(zeilen)} Vorgänge im Katalog.")
    conn.close()


if __name__ == "__main__":
    main()
