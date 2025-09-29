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

CREATE INDEX idx_crawled_esercente ON dati_crawled(id_esercente);
CREATE INDEX idx_rilevazioni_esercente ON rilevazioni(id_esercente);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    id_esercente INT NULL REFERENCES esercenti(id_esercente) ON DELETE SET NULL
);

-- ========================
-- DATI SEED
-- ========================

-- 10 esercenti demo
INSERT INTO esercenti (nome, contatto, pagina_web_fb, pagina_ig, google_recensioni)
VALUES
('Pasticceria Blu', 'info@pasticceriablu.it', 'https://facebook.com/pasticceriablu', 'https://instagram.com/pasticceriablu', 'https://maps.google.com/?cid=111'),
('Caffetteria Aurora', 'aurora@caffe.it', 'https://facebook.com/caffetteriaaurora', 'https://instagram.com/caffetteria.aurora', 'https://maps.google.com/?cid=112'),
('Pizzeria Verde', 'contatti@pizzeriaverde.it', 'https://facebook.com/pizzeriaverde', 'https://instagram.com/pizzeriaverde', 'https://maps.google.com/?cid=113'),
('Forno Giallo', 'info@fornogiallo.it', NULL, NULL, 'https://maps.google.com/?cid=114'),
('Gelateria Rosa', 'ciao@gelros.it', 'https://facebook.com/gelros', 'https://instagram.com/gelros', 'https://maps.google.com/?cid=115'),
('Trattoria Mare', 'prenota@trattoriamare.it', NULL, NULL, 'https://maps.google.com/?cid=116'),
('Panetteria Sole', 'sole@pane.it', NULL, NULL, 'https://maps.google.com/?cid=117'),
('Bistrot Centro', 'hello@bistrotcentro.it', 'https://facebook.com/bistrotcentro', NULL, 'https://maps.google.com/?cid=118'),
('Osteria del Borgo', 'osteria@borgo.it', NULL, 'https://instagram.com/osteriadelborgo', 'https://maps.google.com/?cid=119'),
('Ristorante Stella', 'info@ristorantestella.it', 'https://facebook.com/ristorantestella', 'https://instagram.com/ristorantestella', 'https://maps.google.com/?cid=120');

-- Utenti (1 admin + 10 esercenti)
-- NB: bcrypt hash pre-calcolati con passlib. Qui tutti gli esercenti hanno password 'password123', l'admin 'admin123'.
INSERT INTO users (email, password_hash, id_esercente) VALUES
('admin@backend.local', '$2b$12$3nPoCfLwTn7rJSkVu3bE8O1VxQk4Vf5DYhhbZlYZMLgFjFqYk7IJe', NULL), -- admin123
('pasticceria.blu@demo.local',   '$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 1),
('caffetteria.aurora@demo.local','$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 2),
('pizzeria.verde@demo.local',    '$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 3),
('forno.giallo@demo.local',      '$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 4),
('gelateria.rosa@demo.local',    '$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 5),
('trattoria.mare@demo.local',    '$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 6),
('panetteria.sole@demo.local',   '$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 7),
('bistrot.centro@demo.local',    '$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 8),
('osteria.borgo@demo.local',     '$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 9),
('ristorante.stella@demo.local', '$2b$12$QjKZ8MhxU0.5OGQH3s/5Fe2upH7pRHbFh44Wbl9qS8Gq27RML27Uy', 10);

-- Alcuni dati_crawled di esempio
INSERT INTO dati_crawled (id_esercente, data, ora, n_fan_facebook, n_followers_ig, stelle_google) VALUES
(1, CURRENT_DATE, '10:00', 1200, 900, 4.5),
(2, CURRENT_DATE, '10:30', 800, 600, 4.2),
(3, CURRENT_DATE, '11:00', 1500, 1100, 4.7);

-- Alcune rilevazioni di esempio
INSERT INTO rilevazioni (id_esercente, gioia, tristezza, paura, rabbia, disgusto, sorpresa, neutro, n_passanti) VALUES
(1, 0.7, 0.1, 0.1, 0.05, 0.05, 0.1, 0.2, 100),
(2, 0.6, 0.15, 0.05, 0.1, 0.05, 0.05, 0.3, 80),
(3, 0.8, 0.05, 0.05, 0.05, 0.05, 0.1, 0.1, 120);