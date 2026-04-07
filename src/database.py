"""
database.py — Camada de acesso ao SQLite

Todas as funções são independentes e testáveis isoladamente.
Usa WAL mode para permitir escrita simultânea do Flask e do serial_reader.
"""

import sqlite3
import os

# Caminho absoluto do banco de dados (mesmo diretório deste arquivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'dados.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')


# ── Conexão ────────────────────────────────────────────────────────────────────

def get_db_connection() -> sqlite3.Connection:
    """
    Retorna uma conexão configurada com:
      - WAL mode: permite leitura/escrita simultânea entre Flask e serial_reader
      - busy_timeout: espera até 5s antes de lançar OperationalError em conflito
      - row_factory: resultados acessíveis como dicionários (conn["campo"])
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')  # espera até 5s em caso de lock
    conn.row_factory = sqlite3.Row
    return conn


# ── Inicialização ──────────────────────────────────────────────────────────────

def init_db() -> None:
    """Cria as tabelas se ainda não existirem, lendo o schema.sql."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = f.read()

    conn = get_db_connection()
    try:
        conn.executescript(schema)
        conn.commit()
        print(f"[DB] Banco inicializado em: {DB_PATH}")
    finally:
        conn.close()


# ── CREATE ─────────────────────────────────────────────────────────────────────

def inserir_leitura(temperatura: float, umidade: float,
                    pressao: float = None,
                    localizacao: str = 'Lab Tinkercad') -> int:
    """
    Insere uma nova leitura no banco.
    Retorna o id gerado automaticamente.

    Parâmetros:
        temperatura : valor em °C
        umidade     : valor em % (0–100)
        pressao     : valor em hPa — opcional (None se não disponível)
        localizacao : string descritiva da fonte dos dados
    """
    sql = """
        INSERT INTO leituras (temperatura, umidade, pressao, localizacao)
        VALUES (?, ?, ?, ?)
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute(sql, (temperatura, umidade, pressao, localizacao))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# ── READ ───────────────────────────────────────────────────────────────────────

def listar_leituras(limite: int = 50, offset: int = 0) -> list[sqlite3.Row]:
    """
    Retorna leituras ordenadas da mais recente para a mais antiga.
    Suporta paginação via limite + offset.
    """
    sql = """
        SELECT * FROM leituras
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """
    conn = get_db_connection()
    try:
        rows = conn.execute(sql, (limite, offset)).fetchall()
        return rows
    finally:
        conn.close()


def contar_leituras() -> int:
    """Retorna o total de leituras no banco (usado para paginação)."""
    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]
        return total
    finally:
        conn.close()


def buscar_leitura(id: int) -> sqlite3.Row | None:
    """Retorna uma leitura pelo id, ou None se não existir."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM leituras WHERE id = ?", (id,)
        ).fetchone()
        return row
    finally:
        conn.close()


def buscar_ultimas(n: int = 10) -> list[sqlite3.Row]:
    """Retorna as n leituras mais recentes (usado no painel principal)."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM leituras ORDER BY timestamp DESC LIMIT ?", (n,)
        ).fetchall()
        return rows
    finally:
        conn.close()


# ── UPDATE ─────────────────────────────────────────────────────────────────────

def atualizar_leitura(id: int, dados: dict) -> bool:
    """
    Atualiza campos de uma leitura existente.
    Aceita dicionário com qualquer combinação de: temperatura, umidade, pressao, localizacao.
    Retorna True se alguma linha foi afetada, False se o id não existir.
    """
    campos_permitidos = {'temperatura', 'umidade', 'pressao', 'localizacao'}
    campos = {k: v for k, v in dados.items() if k in campos_permitidos}

    if not campos:
        return False

    set_clause = ', '.join(f"{campo} = ?" for campo in campos)
    valores    = list(campos.values()) + [id]

    sql = f"UPDATE leituras SET {set_clause} WHERE id = ?"

    conn = get_db_connection()
    try:
        cursor = conn.execute(sql, valores)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── DELETE ─────────────────────────────────────────────────────────────────────

def deletar_leitura(id: int) -> bool:
    """
    Remove uma leitura pelo id.
    Retorna True se removida com sucesso, False se não encontrada.
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM leituras WHERE id = ?", (id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── ESTATÍSTICAS ───────────────────────────────────────────────────────────────

def estatisticas() -> dict:
    """
    Retorna média, mínimo e máximo de temperatura e umidade
    para todas as leituras do banco.
    """
    sql = """
        SELECT
            ROUND(AVG(temperatura), 2) AS temp_media,
            ROUND(MIN(temperatura), 2) AS temp_min,
            ROUND(MAX(temperatura), 2) AS temp_max,
            ROUND(AVG(umidade), 2)     AS umid_media,
            ROUND(MIN(umidade), 2)     AS umid_min,
            ROUND(MAX(umidade), 2)     AS umid_max,
            COUNT(*)                   AS total_leituras
        FROM leituras
    """
    conn = get_db_connection()
    try:
        row = conn.execute(sql).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()