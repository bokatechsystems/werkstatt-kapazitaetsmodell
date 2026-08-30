# Werkstatt-Kapazitätsmodell

**Eine Normzeit ist keine Zahl, sondern eine Verteilung.**

Datenmodell und Auswertung für die Kapazitätsvorschau einer
Caravan-/Reisemobil-Werkstatt. Kein Frontend, keine Cloud, keine API --
SQLite, Python, Kommandozeile.

*A time standard is not a number, it is a distribution.*
*Data model and capacity forecast for a caravan / motorhome workshop.*

---

## DE

### Worum es geht

Klassische Arbeitswert-Kataloge geben pro Vorgang eine Zahl aus: 30 Minuten.
Jeder in der Werkstatt weiss, dass diese Zahl selten stimmt -- und niemand
weiss, **wo** die Unsicherheit sitzt.

Dieses Modell trennt drei Dinge, die üblicherweise in einer einzigen Zahl
verschwinden:

```
geschätzte Zeit = Basiszeit
                  × Modellfaktor       (Vertragsmarke ≠ Fremdfabrikat)
                  × Altersfaktor       (Korrosion, Zugänglichkeit)
                  × Fähigkeitsfaktor   (Monteur ∩ Fachgebiet)
```

Dazu kommt pro Vorgang eine **Streuung** (`streuung_pct`). Sie ist der
eigentliche Kern: sie sagt, wo das Risiko entsteht.

### Zwei Fälle, zwei gegensätzliche Formen der Unsicherheit

| Vorgang | Basiszeit | Streuung | |
|---|---|---|---|
| `EL-DIAG-230V` Fehlersuche Kühlschrank | 120 min | **±40 %** | Elektrik: die **Diagnose** streut |
| `MECH-BREMSE-PRUEF` Bremsprüfstand | 20 min | ±10 % | Bremse: die Diagnose ist präzise |
| `MECH-BREMSE-BACKEN` Bremsbacken | 30 min | **±33 %** | Bremse: die **Montage** streut |

Beim Kühlschrank ist das Symptom nicht der Fehler -- 230V-Netz, FI-Schalter,
Elektronikbox oder Heizpatrone. Solange die Ursache nicht feststeht, ist die
Reparatur nicht planbar. Die Fehlersuche ist deshalb ein **eigenständiger
Vorgang**, kein Teilschritt.

Bei der Bremse ist es umgekehrt: der Prüfstand liefert in 20 Minuten ein
eindeutiges Ergebnis. Die Unsicherheit kommt erst beim Zerlegen --
festgebrannte Schrauben, Korrosion.

Ein Katalog mit nur einer Zahl pro Vorgang kann diesen Unterschied nicht
ausdrücken.

### Varianzen addieren sich nicht linear

Bei mehreren Vorgängen wird die Gesamtunsicherheit **nicht** durch Addition
der Einzelstreuungen gebildet. Nicht jede Position trifft am selben Tag den
schlechten Fall. Korrekt ist die Wurzel aus der Summe der Quadrate:

```
σ_gesamt = √(σ₁² + σ₂² + ... + σₙ²)
```

Am Beispiel Kühlschrank: naiv addiert ergäbe das ±68 Minuten, tatsächlich
sind es **±49 Minuten**. Wer linear addiert, plant systematisch zu viel
Puffer ein.

### Ein Effekt, der nicht einprogrammiert wurde

Dieselbe Reparatur, einmal an der Vertragsmarke, einmal am Fremdfabrikat:

| | Vertragsmarke | Fremdfabrikat | |
|---|---|---|---|
| Zeit | 255 min | 303 min | +19 % |
| Streuung | ±49 min | ±63 min | **+29 %** |

**Die Streuung wächst schneller als die Zeit.** Das steht nirgends im Code --
es entsteht, weil der grösste Modellfaktor (1,30) auf den Vorgang mit der
grössten Streuung fällt, die Fehlersuche. Bei unbekannter Verkabelung wird
nicht nur alles langsamer, es wird auch *unsicherer*.

### Der Bericht

```
KW 36 · Kapazitätsvorschau

Fachgebiet                      Offen   Kapazität       Auslastung
ALLGEMEIN                  0.2 h ± 0.1         —   keine eigene Kap.
ELEKTRIK                   4.0 h ± 0.8    38.0 h      11 %   (8-13)
MECHANIK                   5.2 h ± 0.7    76.0 h       7 %    (6-8)
```

Die Auslastung ist ein **Bereich**, keine Zahl. Bei 90 % Auslastung
entscheidet genau dieser Bereich darüber, ob die Woche hält.

`ALLGEMEIN` (Fotodokumentation für Garantiefälle) erscheint ohne Kapazität:
diese Arbeit macht kein eigener Mitarbeiter, sondern derjenige, der auch die
Reparatur ausführt. Eine Kapazität dafür wäre eine erfundene Ressource.

### Was das System bewusst NICHT tut

- **Es plant nicht ein.** Kapazitätsbeschränkte Ressourcenplanung mit
  eingeschränkten Qualifikationen ist NP-schwer. Auch ERP-Systeme lösen das
  nicht -- sie machen es sichtbar.
- **Es bewertet keine Personen.** Die Ausgabe beschreibt die Verteilung der
  Arbeit, nicht die Leistung eines Monteurs.
- **Es entscheidet nicht.** Der Werkstattleiter entscheidet -- nur erstmals
  mit Daten.

Ausserdem: **keine Kundendaten im System.** Die Fahrzeugnummer genügt zur
Identifikation. Damit entfällt der gesamte DSGVO-Aufwand.

### Aufbau

| Datei | Inhalt |
|---|---|
| `schema.sql` | sechs Tabellen |
| `seed_demo.sql` | Demodaten: Kühlschrank + Bremsanlage |
| `init_db.py` | legt `werkstatt.db` an |
| `schaetzung.py` | Schätzung für eine Karte |
| `riport.py` | KW-Bericht über alle offenen Karten |
| `kapazitaet.json` | Wochenkapazität je Fachgebiet |

```bash
python init_db.py
python schaetzung.py 4412    # Kühlschrank
python schaetzung.py 4413    # Bremse, Tandemachse
python riport.py
```

Kein Setup, keine Abhängigkeiten -- SQLite ist Teil von Python.

### Hinweis zu den Daten

Alle Zeitwerte sind gerundete Demowerte, Fabrikate anonymisiert. Es handelt
sich nicht um einen realen Arbeitswert-Katalog.

---

## EN

### The idea

A standard time is not a number, it is a distribution. Conventional labour
catalogues emit a single figure per operation; everyone on the shop floor
knows it is rarely accurate, and nobody knows *where* the uncertainty lives.

This model separates base time, model factor, age factor and skill factor --
and adds a per-operation **spread** that shows where the risk originates.

### Two cases, opposite shapes

Refrigerator fault: the symptom is not the fault. Mains supply, RCD,
electronics box or heating element -- until the cause is known, the repair
cannot be planned. Fault-finding is therefore a **standalone operation** with
the highest spread in the catalogue (±40 %).

Brakes: the test bench gives an unambiguous result in 20 minutes (±10 %). The
uncertainty appears during disassembly -- seized bolts, corrosion (±33 %).

A single-number catalogue cannot express this difference.

### Variances do not add linearly

Total uncertainty is the root sum of squares, not the sum of the individual
spreads -- not every job hits its bad case on the same day. For the
refrigerator case: naive addition gives ±68 minutes, the correct figure is
**±49 minutes**.

### An emergent result

Same repair on a franchise brand vs. a foreign make: time +19 %, spread
+29 %. **The spread grows faster than the time.** This is not coded anywhere.
It emerges because the largest model factor lands on the operation with the
largest spread. Unfamiliar wiring does not only make work slower, it makes it
less predictable.

### Deliberate limits

No scheduling (capacity-constrained scheduling with limited qualifications is
NP-hard -- ERP systems do not solve it either, they make it visible). No
performance evaluation of individuals. No decisions -- the workshop manager
decides, now with data. No customer data in the database.

### Running it

```bash
python init_db.py
python riport.py
```

Python 3 and nothing else; SQLite ships with the standard library.
All time values are rounded demo figures; makes are anonymised.
