"""
app.py — Servidor Flask: API REST + Interface Web
"""

from flask import (
    Flask, request, jsonify, render_template,
    redirect, url_for
)
from database import (
    init_db, inserir_leitura, listar_leituras, contar_leituras,
    buscar_leitura, buscar_ultimas, atualizar_leitura,
    deletar_leitura, estatisticas
)

app = Flask(__name__)

# ── Inicialização do banco ────────────────────────────────────────────────
with app.app_context():
    init_db()


# ── Utilidade ─────────────────────────────────────────────────────────────
def row_para_dict(row):
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════════════════
# PAINEL PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    leituras = buscar_ultimas(10)
    stats = estatisticas()

    if request.args.get('formato') == 'json':
        return jsonify({
            'leituras': [row_para_dict(r) for r in leituras],
            'estatisticas': stats
        })

    return render_template('index.html', leituras=leituras, stats=stats)


# ══════════════════════════════════════════════════════════════════════════
# LISTAR / CRIAR
# ══════════════════════════════════════════════════════════════════════════

@app.route('/leituras', methods=['GET', 'POST'])
def leituras_endpoint():
    if request.method == 'POST':
        return criar()
    return listar()


def listar():
    pagina = max(1, request.args.get('pagina', 1, type=int))
    por_pagina = min(100, request.args.get('por_pagina', 20, type=int))
    offset = (pagina - 1) * por_pagina

    total = contar_leituras()
    total_paginas = max(1, -(-total // por_pagina))

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


def criar():
    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({'erro': 'Corpo inválido'}), 400

    if 'temperatura' not in dados or 'umidade' not in dados:
        return jsonify({'erro': 'temperatura e umidade obrigatórios'}), 422

    try:
        temp = float(dados['temperatura'])
        umid = float(dados['umidade'])
        press = float(dados['pressao']) if dados.get('pressao') else None
    except:
        return jsonify({'erro': 'valores inválidos'}), 422

    id_novo = inserir_leitura(temp, umid, press)
    return jsonify({'id': id_novo, 'status': 'criado'}), 201


# ══════════════════════════════════════════════════════════════════════════
# DETALHE / ATUALIZAR / DELETAR
# ══════════════════════════════════════════════════════════════════════════

@app.route('/leituras/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def leitura_detalhe(id):
    if request.method == 'GET':
        return detalhe(id)
    elif request.method == 'PUT':
        return atualizar(id)
    elif request.method == 'DELETE':
        return deletar(id)


def detalhe(id):
    leitura = buscar_leitura(id)

    if not leitura:
        return jsonify({'erro': f'Leitura {id} não encontrada'}), 404

    return jsonify(row_para_dict(leitura))


# ══════════════════════════════════════════════════════════════════════════
# FORMULÁRIO DE EDIÇÃO
# ══════════════════════════════════════════════════════════════════════════

@app.route('/leituras/<int:id>/editar')
def editar_form(id):
    leitura = buscar_leitura(id)

    if not leitura:
        return jsonify({'erro': f'Leitura {id} não encontrada'}), 404

    return render_template('editar.html', leitura=leitura)


# ══════════════════════════════════════════════════════════════════════════
# ATUALIZAR
# ══════════════════════════════════════════════════════════════════════════

def atualizar(id):
    dados = request.get_json(silent=True) or request.form.to_dict()

    if not dados:
        return jsonify({'erro': 'Nenhum dado enviado'}), 400

    for campo in ('temperatura', 'umidade', 'pressao'):
        if campo in dados and dados[campo] != '':
            try:
                dados[campo] = float(dados[campo])
            except:
                return jsonify({'erro': f'Valor inválido para {campo}'}), 422
        elif campo in dados:
            dados[campo] = None

    sucesso = atualizar_leitura(id, dados)

    if not sucesso:
        return jsonify({'erro': f'Leitura {id} não encontrada'}), 404

    if request.is_json:
        return jsonify({'status': 'atualizado'})

    return redirect(url_for('leituras_endpoint'))


# ══════════════════════════════════════════════════════════════════════════
# DELETAR
# ══════════════════════════════════════════════════════════════════════════

def deletar(id):
    sucesso = deletar_leitura(id)

    if not sucesso:
        return jsonify({'erro': f'Leitura {id} não encontrada'}), 404

    return jsonify({'status': 'deletado'})


# ══════════════════════════════════════════════════════════════════════════
# ESTATÍSTICAS
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/estatisticas')
def rota_estatisticas():
    stats = estatisticas()

    if not stats or stats.get('total_leituras') == 0:
        return jsonify({'aviso': 'Sem dados'}), 200

    return jsonify(stats)


# ══════════════════════════════════════════════════════════════════════════
# GRÁFICO
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/leituras/grafico')
def dados_grafico():
    n = min(200, request.args.get('n', 50, type=int))
    leituras = list(reversed(buscar_ultimas(n)))

    return jsonify({
        'labels': [r['timestamp'] for r in leituras],
        'temperatura': [r['temperatura'] for r in leituras],
        'umidade': [r['umidade'] for r in leituras],
    })


# ══════════════════════════════════════════════════════════════════════════
# ERRO 404 (JSON)
# ══════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def nao_encontrado(e):
    return jsonify({'erro': 'Rota não encontrada'}), 404


# ══════════════════════════════════════════════════════════════════════════
# EXECUÇÃO
# ══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True)