-- =====================================================================
-- Werkstatt-Kapazitätsmodell — séma v0.1
-- Lépés 1: hat tábla. Verziózás (gueltig_ab/bis) szándékosan kimarad.
-- =====================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS auftrag_position;
DROP TABLE IF EXISTS auftrag;
DROP TABLE IF EXISTS modell_faktor;
DROP TABLE IF EXISTS arbeitsvorgang;
DROP TABLE IF EXISTS fahrzeugmodell;
DROP TABLE IF EXISTS fachgebiet;


-- ---------------------------------------------------------------------
-- fachgebiet — szakterület
-- ---------------------------------------------------------------------
CREATE TABLE fachgebiet (
    id    TEXT PRIMARY KEY,
    name  TEXT NOT NULL
);


-- ---------------------------------------------------------------------
-- fahrzeugmodell — jármű-modellgeneráció
-- ist_hausmarke: 1 = Knaus/Tabbert (szakszerviz), 0 = idegen márka
-- ---------------------------------------------------------------------
CREATE TABLE fahrzeugmodell (
    id             INTEGER PRIMARY KEY,
    hersteller     TEXT NOT NULL,
    modell         TEXT NOT NULL,
    baujahr_von    INTEGER,
    baujahr_bis    INTEGER,
    aufbautyp      TEXT,
    ist_hausmarke  INTEGER NOT NULL DEFAULT 0
);


-- ---------------------------------------------------------------------
-- arbeitsvorgang — a katalógus magja
--
--   basiszeit_min : NULL a szülő soroknál. A szülő nem hordoz saját időt,
--                   az összeg a levelekből jön fölfelé.
--   streuung_pct  : 0.40 = ±40%. Ez az „eloszlás", nem az egy szám.
--   parent_id     : hierarchia. NULL = önálló művelet vagy gyökér.
-- ---------------------------------------------------------------------
CREATE TABLE arbeitsvorgang (
    id             INTEGER PRIMARY KEY,
    code           TEXT NOT NULL UNIQUE,
    bezeichnung    TEXT NOT NULL,
    fachgebiet_id  TEXT NOT NULL REFERENCES fachgebiet(id),
    basiszeit_min  REAL,
    streuung_pct   REAL NOT NULL DEFAULT 0.15,
    parent_id      INTEGER REFERENCES arbeitsvorgang(id),

    -- hányszor fordul elő ez a részművelet a szülőn belül?
    -- pl. fékbetét oldalanként megy, a szülő viszont tengelyre szól -> 2.0
    menge_je_eltern REAL NOT NULL DEFAULT 1.0,

    -- szülőnek nincs saját ideje, levélnek van
    CHECK (basiszeit_min IS NULL OR basiszeit_min > 0),
    CHECK (streuung_pct >= 0 AND streuung_pct <= 2),
    CHECK (menge_je_eltern > 0)
);

CREATE INDEX idx_av_parent     ON arbeitsvorgang(parent_id);
CREATE INDEX idx_av_fachgebiet ON arbeitsvorgang(fachgebiet_id);


-- ---------------------------------------------------------------------
-- modell_faktor — csak ott van sor, ahol eltér az alaptól. Hiányzó = 1.0
-- ---------------------------------------------------------------------
CREATE TABLE modell_faktor (
    arbeitsvorgang_id  INTEGER NOT NULL REFERENCES arbeitsvorgang(id),
    fahrzeugmodell_id  INTEGER NOT NULL REFERENCES fahrzeugmodell(id),
    faktor             REAL NOT NULL,

    PRIMARY KEY (arbeitsvorgang_id, fahrzeugmodell_id),
    CHECK (faktor > 0)
);


-- ---------------------------------------------------------------------
-- auftrag — a kártya. Ügyféladat NEM kerül bele.
-- ---------------------------------------------------------------------
CREATE TABLE auftrag (
    id                 INTEGER PRIMARY KEY,
    kartennummer       TEXT NOT NULL,
    wkn                TEXT,
    fahrzeugmodell_id  INTEGER REFERENCES fahrzeugmodell(id),
    baujahr            INTEGER,
    eingang            DATE NOT NULL,
    wunschtermin       DATE,
    status             TEXT NOT NULL DEFAULT 'offen',
    fehlerbeschreibung TEXT,

    CHECK (status IN ('offen','laufend','fertig'))
);


-- ---------------------------------------------------------------------
-- auftrag_position — kártya → műveletek
-- ---------------------------------------------------------------------
CREATE TABLE auftrag_position (
    id                 INTEGER PRIMARY KEY,
    auftrag_id         INTEGER NOT NULL REFERENCES auftrag(id),
    arbeitsvorgang_id  INTEGER NOT NULL REFERENCES arbeitsvorgang(id),
    menge              REAL NOT NULL DEFAULT 1.0,
    komplikation       TEXT
);

CREATE INDEX idx_pos_auftrag ON auftrag_position(auftrag_id);
