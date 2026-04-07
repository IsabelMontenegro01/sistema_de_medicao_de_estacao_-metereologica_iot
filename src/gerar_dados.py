"""
gerar_dados.py — Popula o banco com 30 leituras de exemplo

Execute uma vez antes de demonstrar o projeto:
    python gerar_dados.py

Gera dados realistas com variação temporal simulada.
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'dados.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')


def init_db():
    with open('schema.sql', encoding='utf-8') as f:
     schema = f.read()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.commit()
    conn.close()


def gerar_leituras(n: int = 30) -> None:
    init_db()
    conn = sqlite3.connect(DB_PATH)

    agora = datetime.now()
    temp_base = 22.0  # temperatura inicial
    umid_base = 55.0  # umidade inicial

    for i in range(n):
        # Simula variação gradual + ruído pequeno
        temp_base += random.uniform(-0.8, 0.8)
        umid_base += random.uniform(-2.0, 2.0)

        # Mantém dentro de faixas realistas
        temp = max(18.0, min(35.0, temp_base))
        umid = max(30.0, min(90.0, umid_base))

        # Timestamp retroativo: uma leitura a cada 5 minutos
        ts = agora - timedelta(minutes=5 * (n - i))

        conn.execute(
            """INSERT INTO leituras (temperatura, umidade, pressao, localizacao, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (
                round(temp, 1),
                round(umid, 1),
                None,  # sem sensor de pressão
                'Lab Tinkercad',
                ts.strftime('%Y-%m-%d %H:%M:%S')
            )
        )

    conn.commit()
    conn.close()
    print(f"✓ {n} leituras inseridas em {DB_PATH}")


if __name__ == '__main__':
    gerar_leituras(30)