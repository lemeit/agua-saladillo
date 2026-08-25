-- Coordenadas de los puntos de muestreo de agua-saladillo.
-- Reemplaza el uso de localStorage: antes cada visitante guardaba (y podía
-- pisar) sus propias coordenadas solo en su navegador; ahora son un dato
-- compartido, servido por el Worker en worker/src/index.js, y solo se
-- pueden escribir con la clave de administrador (ADMIN_KEY, ver worker/README
-- o el mensaje de configuración).

CREATE TABLE IF NOT EXISTS coords (
  fuente          TEXT PRIMARY KEY,
  lat             REAL,
  lon             REAL,
  tipo            TEXT,
  dir             TEXT,
  actualizado_en  TEXT DEFAULT (datetime('now'))
);
