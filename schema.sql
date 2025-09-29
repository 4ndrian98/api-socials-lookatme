CREATE TABLE esercenti (
  id_esercente        SERIAL PRIMARY KEY,
  nome                TEXT NOT NULL,
  contatto            TEXT,
  logo                TEXT,
  colore_sfondo       TEXT,
  colore_carattere    TEXT,
  pagina_web_fb       TEXT,
  pagina_ig           TEXT,
  google_recensioni   TEXT,
  certificazione_1            TEXT,
  immagine_certificazione_1   TEXT,
  certificazione_2            TEXT,
  immagine_certificazione_2   TEXT
);

CREATE TABLE dati_crawled (
  id                  SERIAL PRIMARY KEY,
  id_esercente        INTEGER NOT NULL REFERENCES esercenti(id_esercente) ON DELETE CASCADE,
  data                DATE,
  ora                 TIME,
  n_fan_facebook      INTEGER DEFAULT 0 CHECK (n_fan_facebook >= 0),
  n_followers_ig      INTEGER DEFAULT 0 CHECK (n_followers_ig >= 0),
  stelle_google       NUMERIC(2,1) CHECK (stelle_google >= 0 AND stelle_google <= 5)
);

CREATE TABLE rilevazioni (
  id                  SERIAL PRIMARY KEY,
  id_esercente        INTEGER NOT NULL REFERENCES esercenti(id_esercente) ON DELETE CASCADE,
  gioia               NUMERIC(3,2) CHECK (gioia >= 0 AND gioia <= 1),
  tristezza           NUMERIC(3,2) CHECK (tristezza >= 0 AND tristezza <= 1),
  paura               NUMERIC(3,2) CHECK (paura >= 0 AND paura <= 1),
  rabbia              NUMERIC(3,2) CHECK (rabbia >= 0 AND rabbia <= 1),
  disgusto            NUMERIC(3,2) CHECK (disgusto >= 0 AND disgusto <= 1),
  sorpresa            NUMERIC(3,2) CHECK (sorpresa >= 0 AND sorpresa <= 1),
  neutro              NUMERIC(3,2) CHECK (neutro >= 0 AND neutro <= 1),
  n_passanti          INTEGER CHECK (n_passanti >= 0)
);

-- Indici utili per velocizzare le join
CREATE INDEX idx_crawled_esercente ON dati_crawled(id_esercente);
CREATE INDEX idx_rilevazioni_esercente ON rilevazioni(id_esercente);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    id_esercente INT NULL REFERENCES esercenti(id_esercente) ON DELETE SET NULL
);
