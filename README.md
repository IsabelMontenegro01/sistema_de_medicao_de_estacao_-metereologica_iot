# Estação Meteorológica IoT

Sistema de medição meteorológica com Arduino simulado no Tinkercad, API REST com Flask, banco SQLite e interface web.

🔗 **Simulação no Tinkercad:** [Abrir circuito](https://www.tinkercad.com/things/4htn0NkUu95/editel?returnTo=%2Fdashboard%2Fdesigns%2Fcircuits&sharecode=a-BWQxG1HjJNjC7_MZxRp0oIEzT2DdBmqLwlMPzmfqA)

> O circuito usa **TMP36** para temperatura e **potenciômetro** para simular umidade (DHT11 não disponível no Tinkercad). Os dados da aplicação são **mockados** via `gerar_dados.py`.

---

## Como rodar

```bash
# 1. Instalar dependências
pip install flask pyserial requests

# 2. Popular o banco com dados de exemplo
cd src
python gerar_dados.py

# 3. Subir o servidor
python app.py
# Acesse: http://localhost:5000
```

Para leitura serial com Arduino físico, veja a [documentação completa](docs/DOCUMENTACAO.md).

---

## Estrutura

```
├── docs/
│   ├── images/
│   └── documentacao.md     # detalhes técnicos do projeto
├── src/
│   ├── app.py              # servidor Flask
│   ├── database.py         # camada de dados
│   ├── serial_reader.py    # leitura serial do Arduino
│   ├── gerar_dados.py      # gerador de dados mockados
│   ├── schema.sql
│   ├── static/
│   ├── templates/
│   └── arduino/
│       └── estacao.ino
└── README.md
```