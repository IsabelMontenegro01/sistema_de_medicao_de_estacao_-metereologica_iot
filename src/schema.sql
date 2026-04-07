-- schema.sql — Estrutura do banco de dados
-- Executado automaticamente pelo init_db() na primeira inicialização

CREATE TABLE IF NOT EXISTS leituras (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    temperatura REAL     NOT NULL,
    umidade     REAL     NOT NULL,
    pressao     REAL,                                          -- opcional (não usado no Tinkercad)
    localizacao TEXT     DEFAULT 'Lab Tinkercad',
    timestamp   DATETIME DEFAULT (datetime('now','localtime'))
);

-- Índice para acelerar consultas por data (histórico, gráficos)
CREATE INDEX IF NOT EXISTS idx_leituras_timestamp
    ON leituras (timestamp DESC);