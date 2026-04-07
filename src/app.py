"""
app.py — Servidor Flask: API REST + Interface Web

Endpoints:
  GET  /                    → Painel principal (últimas 10 leituras)
  GET  /leituras            → Histórico com paginação
  POST /leituras            → Recebe JSON do Arduino/simulador
  GET  /leituras/<id>       → Detalhe de uma leitura
  GET  /leituras/<id>/editar → Formulário de edição
  PUT  /leituras/<id>       → Atualiza uma leitura
  DELETE /leituras/<id>     → Remove uma leitura
  GET  /api/estatisticas    → Estatísticas agregadas (JSON)
"""

from flask import (
    Flask, request, jsonify, render_template,
    redirect, url_for, abort
)
from database import (
    init_db, inserir_leitura, listar_leituras, contar_leituras,
    buscar_leitura, buscar_ultimas, atualizar_leitura,
    deletar_leitura, estatisticas
)

app = Flask(__name__)

# ── Inicialização do banco na primeira execução ────────────────────────────────
with app.app_context():
    init_db()


# ── Utilidade: converter sqlite3.Row → dict (para jsonify) ────────────────────
def row_para_dict(row):
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════════════════════
# PAINEL PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """
    Exibe as últimas 10 leituras e estatísticas gerais.
    Suporta ?formato=json para retorno em JSON.
    """
    leituras = buscar_ultimas(10)
    stats    = estatisticas()

    if request.args.get('formato') == 'json':
        return jsonify({
            'leituras': [row_para_dict(r) for r in leituras],
            'estatisticas': stats
        })

    return render_template('index.html', leituras=leituras, stats=stats)


# ══════════════════════════════════════════════════════════════════════════════
# HISTÓRICO — LISTAR
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/leituras', methods=['GET', 'POST'])
def leituras_endpoint():
    if request.method == 'POST':
        return criar()
    return listar()


def listar():
    """
    GET /leituras — Histórico completo com paginação.
    Query params:
      ?pagina=1   → página atual (default 1)
      ?por_pagina=20 → itens por página (default 20)
      ?formato=json  → retorna JSON em vez de HTML
    """
    pagina      = max(1, request.args.get('pagina', 1, type=int))
    por_pagina  = min(100, request.args.get('por_pagina', 20, type=int))
    offset      = (pagina - 1) * por_pagina
    total       = contar_leituras()
    total_paginas = max(1, -(-total // por_pagina))  # ceil division

    leituras = listar_leituras(limite=por_pagina, offset=offset)

    if request.args.get('formato') == 'json':
        return jsonify({
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total': total,
            'total_paginas': total_paginas,
            'leituras': [row_para_dict(r) for r in leituras]
        })

    return render_template(
        'historico.html',
        leituras=leituras,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total
    )


# ══════════════════════════════════════════════════════════════════════════════
# CRIAR LEITURA (POST)
# ══════════════════════════════════════════════════════════════════════════════

def criar():
    """
    POST /leituras — Recebe JSON do serial_reader.py (ou Postman/curl).

    Body esperado:
      { "temperatura": 24.5, "umidade": 60.0 }
      { "temperatura": 24.5, "umidade": 60.0, "pressao": 1013.2 }  ← opcional
    """
    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({'erro': 'Corpo da requisição inválido ou não é JSON'}), 400

    # Campos obrigatórios
    if 'temperatura' not in dados or 'umidade' not in dados:
        return jsonify({'erro': 'Campos "temperatura" e "umidade" são obrigatórios'}), 422

    # Validação de faixas realistas
    try:
        temp  = float(dados['temperatura'])
        umid  = float(dados['umidade'])
        press = float(dados['pressao']) if dados.get('pressao') is not None else None
    except (TypeError, ValueError):
        return jsonify({'erro': 'Valores numéricos inválidos'}), 422

    if not (-40 <= temp <= 85):
        return jsonify({'erro': f'Temperatura fora do range permitido: {temp}°C'}), 422
    if not (0 <= umid <= 100):
        return jsonify({'erro': f'Umidade fora do range permitido: {umid}%'}), 422

    id_novo = inserir_leitura(temp, umid, press)
    return jsonify({'id': id_novo, 'status': 'criado'}), 201


# ══════════════════════════════════════════════════════════════════════════════
# DETALHE DE UMA LEITURA
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/leituras/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def leitura_detalhe(id):
    if request.method == 'GET':
        return detalhe(id)
    elif request.method == 'PUT':
        return atualizar(id)
    elif request.method == 'DELETE':
        return deletar(id)


def detalhe(id):
    """GET /leituras/<id> — Exibe uma leitura específica."""
    leitura = buscar_leitura(id)
    if not leitura:
        if request.args.get('formato') == 'json':
            return jsonify({'erro': f'Leitura {id} não encontrada'}), 404
        abort(404)

    if request.args.get('formato') == 'json':
        return jsonify(row_para_dict(leitura))

    return render_template('detalhe.html', leitura=leitura)


# ══════════════════════════════════════════════════════════════════════════════
# FORMULÁRIO DE EDIÇÃO
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/leituras/<int:id>/editar', methods=['GET'])
def editar_form(id):
    """GET /leituras/<id>/editar — Renderiza o formulário de edição."""
    leitura = buscar_leitura(id)
    if not leitura:
        abort(404)
    return render_template('editar.html', leitura=leitura)


# ══════════════════════════════════════════════════════════════════════════════
# ATUALIZAR
# ══════════════════════════════════════════════════════════════════════════════

def atualizar(id):
    """
    PUT /leituras/<id> — Atualiza campos de uma leitura.

    Aceita JSON:  { "temperatura": 25.0 }
    Aceita form:  campo _method=PUT via formulário HTML
    """
    # Suporte a form HTML (não há PUT nativo em forms HTML)
    dados = request.get_json(silent=True) or request.form.to_dict()

    if not dados:
        return jsonify({'erro': 'Nenhum dado enviado'}), 400

    # Converte campos numéricos que chegam como string (via form)
    for campo in ('temperatura', 'umidade', 'pressao'):
        if campo in dados and dados[campo] != '':
            try:
                dados[campo] = float(dados[campo])
            except ValueError:
                return jsonify({'erro': f'Valor inválido para {campo}'}), 422
        elif campo in dados and dados[campo] == '':
            dados[campo] = None

    sucesso = atualizar_leitura(id, dados)

    if not sucesso:
        if request.is_json:
            return jsonify({'erro': f'Leitura {id} não encontrada'}), 404
        abort(404)

    if request.is_json:
        return jsonify({'status': 'atualizado', 'id': id})

    # Redireciona de volta ao histórico após edição via formulário
    return redirect(url_for('leituras_endpoint'))


# ══════════════════════════════════════════════════════════════════════════════
# DELETAR
# ══════════════════════════════════════════════════════════════════════════════

def deletar(id):
    """DELETE /leituras/<id> — Remove uma leitura."""
    sucesso = deletar_leitura(id)

    if not sucesso:
        return jsonify({'erro': f'Leitura {id} não encontrada'}), 404

    return jsonify({'status': 'deletado', 'id': id})


# ══════════════════════════════════════════════════════════════════════════════
# ESTATÍSTICAS (JSON apenas)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/estatisticas')
def rota_estatisticas():
    """GET /api/estatisticas — Retorna estatísticas agregadas em JSON."""
    stats = estatisticas()
    if not stats or stats.get('total_leituras') == 0:
        return jsonify({'aviso': 'Nenhuma leitura no banco ainda'}), 200
    return jsonify(stats)


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT DE DADOS PARA O GRÁFICO
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/leituras/grafico')
def dados_grafico():
    """
    GET /api/leituras/grafico — Retorna as últimas N leituras em JSON
    formatadas para consumo direto pelo Chart.js no frontend.
    Query param: ?n=50 (default 50)
    """
    n = min(200, request.args.get('n', 50, type=int))
    leituras = buscar_ultimas(n)

    # Inverte para ordem cronológica (mais antigo → mais recente)
    leituras = list(reversed(leituras))

    return jsonify({
        'labels':       [r['timestamp'] for r in leituras],
        'temperatura':  [r['temperatura'] for r in leituras],
        'umidade':      [r['umidade'] for r in leituras],
    })


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 404 CUSTOMIZADA
# ══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def nao_encontrado(e):
    return render_template('404.html'), 404


# ══════════════════════════════════════════════════════════════════════════════
# EXECUÇÃO
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # debug=True APENAS em desenvolvimento
    app.run(debug=True, host='0.0.0.0', port=5000)