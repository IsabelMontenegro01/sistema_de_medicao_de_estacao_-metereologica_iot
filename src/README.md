# Estação Meteorológica IoT

Sistema de medição meteorológica com Arduino (simulado no Tinkercad), API REST com Flask, banco SQLite e interface web.

---

## Decisões de Arquitetura

### Hardware
| Componente original | Substituição no Tinkercad | Motivo |
|---|---|---|
| DHT11 (temp + umidade) | TMP36 (temperatura) | DHT11 não está disponível no Tinkercad |
| DHT11 (umidade) | Potenciômetro (umidade simulada) | Simula leitura analógica contínua girando o knob |
| BMP180 (pressão) | Omitido | Não disponível; campo `pressao` salvo como NULL |

O potenciômetro no pino **A1** é mapeado linearmente de 0–1023 para **20–95%** de umidade.  
O TMP36 no pino **A0** usa a fórmula: `temp = (tensão_mV - 500) / 10`.

### Software
- Arquitetura **em três camadas**: Arduino → Flask API → Interface Web
- **Dois processos paralelos**: `app.py` (servidor web) + `serial_reader.py` (leitor serial)
- **WAL mode** no SQLite para suportar escrita simultânea dos dois processos sem deadlock
- Interface web em Jinja2 com atualização automática via JavaScript (sem frameworks)
- Gráfico temporal com **Chart.js** consumindo endpoint `/api/leituras/grafico`
- Exclusão via `fetch + DELETE` (sem recarregar página); edição via `fetch + PUT`

---

## Estrutura do Projeto

```
estacao_meteorologica/
├── arduino/
│   └── estacao.ino          # Sketch: TMP36 + Potenciômetro → JSON Serial
└── src/
    ├── app.py               # Servidor Flask (API REST + renderização HTML)
    ├── database.py          # Todas as funções SQLite (CRUD + estatísticas)
    ├── serial_reader.py     # Lê porta serial → POST para API
    ├── schema.sql           # DDL do banco de dados
    ├── gerar_dados.py       # Popula banco com 30 leituras de exemplo
    ├── dados.db             # Banco SQLite (gerado automaticamente)
    ├── static/
    │   └── (arquivos estáticos adicionais, se necessário)
    └── templates/
        ├── base.html        # Layout base (nav, fontes, CSS global)
        ├── index.html       # Painel principal + gráfico + cards
        ├── historico.html   # Tabela paginada + exclusão
        ├── editar.html      # Formulário de edição (PUT via fetch)
        ├── detalhe.html     # Detalhe de uma leitura
        └── 404.html         # Página de erro
```

---

## Instalação e Execução

### 1. Pré-requisitos
- Python 3.10 ou superior
- Arduino IDE 2.x (para carregar o sketch no Tinkercad)

### 2. Instalar dependências Python

```bash
# Criar e ativar ambiente virtual
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Instalar pacotes
pip install flask pyserial requests
```

### 3. Configurar variáveis de ambiente (opcional)

Crie um arquivo `.env` ou exporte antes de rodar:

```bash
# Linux/macOS
export PORTA_SERIAL=/dev/ttyUSB0   # ou /dev/ttyACM0
export BAUD_RATE=9600
export API_URL=http://localhost:5000/leituras

# Windows
set PORTA_SERIAL=COM3
set BAUD_RATE=9600
set API_URL=http://localhost:5000/leituras
```

### 4. Popular o banco com leituras de exemplo

```bash
cd src
python gerar_dados.py
# ✓ 30 leituras inseridas em dados.db
```

### 5. Iniciar o servidor Flask

```bash
cd src
python app.py
# * Running on http://0.0.0.0:5000
```

Acesse: **http://localhost:5000**

### 6. Iniciar a leitura serial (em outro terminal)

```bash
cd src
# Ative o venv novamente se necessário
python serial_reader.py
```

> **Nota:** O Tinkercad precisa estar rodando a simulação com o sketch carregado. No Tinkercad, a porta serial virtual é exposta como Serial Monitor — para uso real com o script Python, conecte o Arduino físico pela USB.

---

## 🔌 Rotas da API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Painel principal (HTML) |
| GET | `/?formato=json` | Painel em JSON |
| GET | `/leituras` | Histórico paginado (HTML) |
| GET | `/leituras?formato=json` | Histórico em JSON |
| POST | `/leituras` | Cria nova leitura (JSON body) |
| GET | `/leituras/<id>` | Detalhe de uma leitura |
| GET | `/leituras/<id>/editar` | Formulário de edição |
| PUT | `/leituras/<id>` | Atualiza uma leitura |
| DELETE | `/leituras/<id>` | Remove uma leitura |
| GET | `/api/estatisticas` | Média, mín e máx (JSON) |
| GET | `/api/leituras/grafico` | Dados formatados para Chart.js |

### Exemplo de POST (curl)

```bash
curl -X POST http://localhost:5000/leituras \
  -H "Content-Type: application/json" \
  -d '{"temperatura": 24.5, "umidade": 62.0}'
```

### Exemplo de PUT (curl)

```bash
curl -X PUT http://localhost:5000/leituras/1 \
  -H "Content-Type: application/json" \
  -d '{"temperatura": 25.0, "localizacao": "Sala de Aula"}'
```

### Exemplo de DELETE (curl)

```bash
curl -X DELETE http://localhost:5000/leituras/1
```

---

## Testando sem Arduino

Para testar a API sem hardware, envie requisições manuais:

```bash
# Enviar 5 leituras simuladas
for i in 1 2 3 4 5; do
  curl -s -X POST http://localhost:5000/leituras \
    -H "Content-Type: application/json" \
    -d "{\"temperatura\": $((20 + RANDOM % 10)).0, \"umidade\": $((50 + RANDOM % 30)).0}"
  sleep 1
done
```

---

## Circuito no Tinkercad

```
TMP36
  VCC  → 5V
  GND  → GND
  OUT  → A0

Potenciômetro (umidade simulada)
  VCC   → 5V
  GND   → GND
  WIPER → A1
```

Gire o potenciômetro durante a simulação para variar a "umidade" de 20% a 95%.  
Clique no TMP36 durante a simulação para arrastar o slider de temperatura.

---

## Referências

- [Flask Documentation](https://flask.palletsprojects.com)
- [PySerial Documentation](https://pyserial.readthedocs.io)
- [SQLite com Python](https://docs.python.org/3/library/sqlite3.html)
- [Chart.js](https://www.chartjs.org)
- [TMP36 Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/TMP35_36_37.pdf)