-- =====================================================================
-- Demodaten -- Fall 1: Kühlschrank ohne Funktion im 230V-Betrieb
-- HINWEIS: gerundete Demowerte, anonymisierte Fabrikate.
-- =====================================================================

-- --- Fachgebiete -----------------------------------------------------
INSERT INTO fachgebiet (id, name) VALUES
    ('ELEKTRIK',           'Elektrik'),
    ('MECHANIK',           'Mechanik'),
    ('MOEBELBAU',          'Möbelbau'),
    ('WASSER_GAS_HEIZUNG', 'Wasser / Gas / Heizung'),
    ('ALLGEMEIN',          'Allgemein / Dokumentation');


-- --- Fahrzeugmodelle --------------------------------------------------
INSERT INTO fahrzeugmodell
    (id, hersteller, modell, baujahr_von, baujahr_bis, aufbautyp, ist_hausmarke)
VALUES
    (1, 'Marke A', 'Serie 1', 2021, 2026, 'Wohnwagen',      1),   -- Vertragsmarke
    (2, 'Marke B', 'Serie 2', 2020, 2025, 'Teilintegriert', 0);   -- Fremdfabrikat


-- --- Vorgänge ---------------------------------------------------------
-- 1. Fehlersuche: EIGENSTÄNDIGER Vorgang, kein Teilschritt der Reparatur.
--    Das Symptom ist nicht der Fehler. Solange der Fehler nicht gefunden ist,
--    steht die Reparatur nicht fest -> höchste Streuung im ganzen Katalog.
INSERT INTO arbeitsvorgang
    (id, code, bezeichnung, fachgebiet_id, basiszeit_min, streuung_pct, parent_id)
VALUES
    (10, 'EL-DIAG-230V', '230V-Fehlersuche Kühlschrank', 'ELEKTRIK', 120, 0.40, NULL);

-- 2. Die Reparatur: Elternvorgang + vier Teilvorgänge.
--    Der Elternvorgang trägt KEINE eigene Zeit. Die Summe kommt von den Blättern.
INSERT INTO arbeitsvorgang
    (id, code, bezeichnung, fachgebiet_id, basiszeit_min, streuung_pct, parent_id)
VALUES
    (20, 'EL-KUEHL-HEIZ-TAUSCH', 'Heizpatrone 230V tauschen (Gesamt)', 'ELEKTRIK', NULL, 0.00, NULL),
    (21, 'EL-KUEHL-AUSBAU',      'Kühlschrank ausbauen',               'ELEKTRIK',   30, 0.15, 20),
    (22, 'EL-KUEHL-PATRONE',     'Heizpatrone 230V wechseln',          'ELEKTRIK',   30, 0.15, 20),
    (23, 'EL-KUEHL-EINBAU',      'Kühlschrank einbauen',               'ELEKTRIK',   30, 0.15, 20),
    (24, 'EL-KUEHL-TEST',        'Funktionstest Kühlbetrieb',          'ELEKTRIK',   30, 0.10, 20);

-- 3. Fotodokumentation: gehört zur GARANTIE, nicht zum Kühlschrank.
--    Darum eigenständig und fachgebietsübergreifend verwendbar --
--    sonst würde auch eine Reparatur ausserhalb der Garantie dafür zahlen.
INSERT INTO arbeitsvorgang
    (id, code, bezeichnung, fachgebiet_id, basiszeit_min, streuung_pct, parent_id)
VALUES
    (30, 'DOK-GARANTIE-FOTO', 'Fotodokumentation Garantiefall', 'ALLGEMEIN', 15, 0.20, NULL);


-- --- Modellfaktoren ---------------------------------------------------
-- Nur bei Abweichung existiert eine Zeile. Fehlend = 1.0.
-- Fremdfabrikat: engerer Einbau, unbekannte Verkabelung.
INSERT INTO modell_faktor (arbeitsvorgang_id, fahrzeugmodell_id, faktor) VALUES
    (10, 2, 1.30),   -- Fehlersuche am Fremdfabrikat
    (21, 2, 1.20),   -- kiszerelés
    (23, 2, 1.20);   -- beszerelés


-- --- Karte ------------------------------------------------------------
INSERT INTO auftrag
    (id, kartennummer, wkn, fahrzeugmodell_id, baujahr, eingang, wunschtermin,
     status, fehlerbeschreibung)
VALUES
    (4412, 'K-4412', 'WKN-DEMO-0001', 1, 2024, '2026-08-28', '2026-09-04',
     'offen', 'Kühlschrank kühlt nicht auf 230V-Betrieb. Garantie.');


-- --- Positionen der Karte ---------------------------------------------
-- BEACHTE: Auf der Karte steht der Elternvorgang (20), nicht die vier
-- Teilvorgänge. Die Schätzung löst die Hierarchie selbst bis zu den Blättern auf.
INSERT INTO auftrag_position (auftrag_id, arbeitsvorgang_id, menge) VALUES
    (4412, 10, 1.0),   -- Fehlersuche
    (4412, 20, 1.0),   -- Heizpatrone (Eltern -> 4 Teilvorgänge)
    (4412, 30, 1.0);   -- Garantie-Foto


-- =====================================================================
-- FALL 2 -- Bremsanlage
--
-- Was hier anders ist als beim Kühlschrank:
--   * MECHANIK statt ELEKTRIK -> die Summierung nach Fachgebiet wird aussagekräftig
--   * KEIN modell_faktor: das Rad ist bei jedem Fabrikat gleich.
--     Das ist keine Lücke, sondern eine fachliche Aussage.
--   * Die Streuung sitzt in der MONTAGE, nicht in der Diagnose
--     -- beim Kühlschrank war es genau umgekehrt.
--   * Derselbe Vorgang zweimal auf der Karte: Bremsprüfstand als
--     Eingangsmessung und als Endkontrolle. Kein separater Vorgang.
--   * Zwei mögliche Ausgänge: Nachstellen ODER Tausch. Der Prüfstand entscheidet.
-- =====================================================================

-- --- Vorgänge ---------------------------------------------------------
-- Einheit: ACHSE, ausser wo anders vermerkt.
INSERT INTO arbeitsvorgang
    (id, code, bezeichnung, fachgebiet_id, basiszeit_min, streuung_pct,
     parent_id, menge_je_eltern)
VALUES
    (40, 'MECH-BREMSE-PRUEF', 'Bremsprüfstand (je Achse)', 'MECHANIK',
         20, 0.10, NULL, 1.0),

    -- A) noch nachstellbar -> kein Tausch
    (41, 'MECH-BREMSE-EINST', 'Bremse nachstellen (je Achse)', 'MECHANIK',
         15, 0.20, NULL, 1.0),

    -- B) nicht mehr nachstellbar -> Tausch, je Achse
    (50, 'MECH-BREMSE-TAUSCH', 'Bremsbacken tauschen (je Achse, Gesamt)', 'MECHANIK',
         NULL, 0.00, NULL, 1.0),
    (51, 'MECH-BREMSE-RAD',     'Rad de-/montieren',        'MECHANIK', 10, 0.20, 50, 1.0),
    (52, 'MECH-BREMSE-TROMMEL', 'Bremstrommel de-/montieren','MECHANIK', 20, 0.25, 50, 1.0),
    -- BEACHTE: je SEITE, der Elternvorgang gilt je ACHSE -> Faktor 2.0
    (53, 'MECH-BREMSE-BACKEN',  'Bremsbacken wechseln (je Seite)', 'MECHANIK',
         30, 0.33, 50, 2.0);


-- --- Karte: Tandemachse, Tausch erforderlich -------------------------
INSERT INTO auftrag
    (id, kartennummer, wkn, fahrzeugmodell_id, baujahr, eingang, wunschtermin,
     status, fehlerbeschreibung)
VALUES
    (4413, 'K-4413', 'WKN-DEMO-0002', 1, 2019, '2026-08-29', NULL,
     'offen', 'Bremswirkung ungleich links/rechts. Tandemachse.');

INSERT INTO auftrag_position (auftrag_id, arbeitsvorgang_id, menge, komplikation) VALUES
    (4413, 40, 2.0, 'Eingangsmessung'),   -- Prüfstand, 2 Achsen
    (4413, 50, 2.0, NULL),                -- Tausch, 2 Achsen
    (4413, 40, 2.0, 'Endkontrolle');      -- DERSELBE Vorgang erneut


-- --- Karte: Einachser, Nachstellen genügt ----------------------------
INSERT INTO auftrag
    (id, kartennummer, wkn, fahrzeugmodell_id, baujahr, eingang, wunschtermin,
     status, fehlerbeschreibung)
VALUES
    (4414, 'K-4414', 'WKN-DEMO-0003', 2, 2022, '2026-08-29', NULL,
     'offen', 'Bremse zieht leicht einseitig. Einachser.');

INSERT INTO auftrag_position (auftrag_id, arbeitsvorgang_id, menge, komplikation) VALUES
    (4414, 40, 1.0, 'Eingangsmessung'),
    (4414, 41, 1.0, NULL),                -- nur Nachstellen
    (4414, 40, 1.0, 'Endkontrolle');
