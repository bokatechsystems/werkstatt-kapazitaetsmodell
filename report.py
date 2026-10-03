#!/usr/bin/env python3
"""
Werkstatt-Kapazitätsmodell -- KW-Bericht.

Aufruf:  python riport.py

Das ist die Ausgabe, für die das ganze Modell existiert. Alle OFFENEN
Karten werden je Fachgebiet summiert und der Wochenkapazität
gegenübergestellt.

Was der Bericht bewusst NICHT tut:
  * niemanden einplanen (wer die Arbeit ausführt)
  * keine Umverteilung vorschlagen
  * keine Person bewerten
Der Werkstattleiter entscheidet -- nur erstmals mit Daten.
"""

import json
import sqlite3
from math import sqrt
from pathlib import Path

HIER = Path(__file__).parent
DB = HIER / "werkstatt.db"
CONFIG = HIER / "kapazitaet.json"

# Dieselbe rekursive Auflösung wie in schaetzung.py,
# nur für ALLE offenen Karten auf einmal.
SQL = """
WITH RECURSIVE baum(auftrag_id, av_id, menge) AS (

    SELECT p.auftrag_id, p.arbeitsvorgang_id, p.menge
    FROM auftrag_position p
    JOIN auftrag t ON t.id = p.auftrag_id
    WHERE t.status = 'offen'

    UNION ALL

    SELECT b.auftrag_id, a.id, b.menge * a.menge_je_eltern
    FROM baum b
    JOIN arbeitsvorgang a ON a.parent_id = b.av_id
)
SELECT
    b.auftrag_id,
    t.kartennummer,
    a.fachgebiet_id,
    a.basiszeit_min * COALESCE(mf.faktor, 1.0) * b.menge AS zeit_min,
    a.streuung_pct
FROM baum b
JOIN arbeitsvorgang a ON a.id = b.av_id
JOIN auftrag t        ON t.id = b.auftrag_id
LEFT JOIN modell_faktor mf
       ON mf.arbeitsvorgang_id = a.id
      AND mf.fahrzeugmodell_id = t.fahrzeugmodell_id
WHERE a.basiszeit_min IS NOT NULL
"""


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    kap = cfg["kapazitaet_h"]
    kw = cfg["kalenderwoche"]

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    zeilen = conn.execute(SQL).fetchall()

    fach = {}      # je Fachgebiet: [Zeit, Summe der Varianzen]
    karten = {}    # je Fachgebiet: welche Karten betroffen sind

    for z in zeilen:
        fg = z["fachgebiet_id"]
        zeit = z["zeit_min"]
        abw = zeit * z["streuung_pct"]

        d = fach.setdefault(fg, [0.0, 0.0])
        d[0] += zeit
        d[1] += abw ** 2                 # Varianzen addieren, nicht Streuungen
        karten.setdefault(fg, set()).add(z["kartennummer"])

    print(f"\nKW {kw} · Kapazitätsvorschau")
    print("=" * 66)
    print(f"{'Fachgebiet':<21}{'Offen':>16}{'Kapazität':>12}{'Auslastung':>17}")
    print("-" * 66)

    warnungen = []

    for fg in sorted(fach):
        zeit_h = fach[fg][0] / 60
        abw_h = sqrt(fach[fg][1]) / 60   # RSS -- Streuungen gleichen sich aus

        if fg not in kap:
            # ALLGEMEIN: keine eigene Kapazität. Die Dokumentation macht
            # kein eigener Mitarbeiter, sondern wer die Reparatur ausführt.
            # Eine Kapazität dafür wäre eine erfundene Ressource.
            print(f"{fg:<21}{zeit_h:>9.1f} h ± {abw_h:<3.1f}"
                  f"{'—':>10}{'keine eigene Kap.':>20}")
            continue

        k = kap[fg]
        pct = zeit_h / k * 100
        pct_min = (zeit_h - abw_h) / k * 100
        pct_max = (zeit_h + abw_h) / k * 100

        zeichen = " !" if pct_max > 100 else ""
        print(f"{fg:<21}{zeit_h:>9.1f} h ± {abw_h:<3.1f}{k:>8.1f} h"
              f"{pct:>8.0f} %{f'({pct_min:.0f}-{pct_max:.0f})':>9}{zeichen}")

        if pct_max > 100:
            warnungen.append((fg, zeit_h, abw_h, k, pct, pct_max))

    print("-" * 66)

    if warnungen:
        print()
        for fg, zeit_h, abw_h, k, pct, pct_max in warnungen:
            if pct > 100:
                print(f"! {fg}: Überlast. {zeit_h - k:.1f} h über Kapazität.")
            else:
                # Der Mittelwert hält, die Streuung reicht aber darüber
                # hinaus. Genau das zeigt eine übliche Auslastungszahl nicht.
                print(f"! {fg}: {pct:.0f} % ausgelastet, aber die Streuung "
                      f"reicht bis {pct_max:.0f} %.")
            print(f"  Betroffene Aufträge: {', '.join(sorted(karten[fg]))}\n")
    else:
        print("\nKeine Überlast.\n")

    # --- was eine einfache Tabelle nicht zeigen würde -----------------
    ges_zeit = sum(v[0] for v in fach.values()) / 60
    ges_abw = sqrt(sum(v[1] for v in fach.values())) / 60
    naiv_abw = sum(sqrt(v[1]) for v in fach.values()) / 60

    print(f"Gesamt: {ges_zeit:.1f} h  ± {ges_abw:.1f} h")
    print(f"  (linear addiert wären es ±{naiv_abw:.1f} h -- "
          f"die Streuungen gleichen sich aus)")

    anz = conn.execute(
        "SELECT COUNT(*) FROM auftrag WHERE status='offen'").fetchone()[0]
    print(f"  {anz} offene Karten\n")

    conn.close()


if __name__ == "__main__":
    main()
