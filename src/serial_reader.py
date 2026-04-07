"""
serial_reader.py — Leitura da porta serial do Arduino

Roda como processo INDEPENDENTE (em outro terminal) em paralelo com o Flask.
Lê o JSON enviado pelo Arduino via USB e faz POST para a API Flask.

Uso:
    python serial_reader.py

Configuração via variáveis de ambiente (opcional):
    PORTA_SERIAL=COM3          (Windows) ou /dev/ttyUSB0 (Linux/macOS)
    BAUD_RATE=9600
    API_URL=http://localhost:5000/leituras
"""

import serial
import json
import requests
import time
import os
import sys
from datetime import datetime

# ── Configuração (pode ser sobrescrita por variáveis de ambiente) ──────────────
PORTA   = os.getenv('PORTA_SERIAL', 'COM3')        # Windows: COM3 | Linux: /dev/ttyUSB0
BAUD    = int(os.getenv('BAUD_RATE', '9600'))
URL     = os.getenv('API_URL', 'http://localhost:5000/leituras')
TIMEOUT = 2   # segundos de timeout na leitura serial


def log(mensagem: str) -> None:
    """Imprime mensagem com timestamp para facilitar o debug."""
    agora = datetime.now().strftime('%H:%M:%S')
    print(f"[{agora}] {mensagem}")


def enviar_para_api(dados: dict) -> bool:
    """
    Faz POST dos dados para a API Flask.
    Retorna True em caso de sucesso, False em caso de erro.
    """
    try:
        resposta = requests.post(URL, json=dados, timeout=5)
        if resposta.status_code == 201:
            id_criado = resposta.json().get('id', '?')
            log(f"✓ Enviado → ID {id_criado} | temp={dados.get('temperatura')}°C | umid={dados.get('umidade')}%")
            return True
        else:
            log(f"✗ API retornou status {resposta.status_code}: {resposta.text}")
            return False
    except requests.exceptions.ConnectionError:
        log("✗ Não foi possível conectar à API. O Flask está rodando?")
        return False
    except requests.exceptions.Timeout:
        log("✗ Timeout ao conectar com a API.")
        return False


def ler_serial() -> None:
    """
    Loop principal: abre a porta serial e fica lendo linhas JSON.
    Trata erros de decodificação e reconexão automática.
    """
    log(f"Iniciando leitura serial em {PORTA} @ {BAUD} baud")
    log(f"Enviando para: {URL}")
    log("Pressione Ctrl+C para encerrar.\n")

    while True:
        try:
            with serial.Serial(PORTA, BAUD, timeout=TIMEOUT) as ser:
                log(f"Porta {PORTA} aberta com sucesso.")

                while True:
                    linha_raw = ser.readline()

                    # Ignora linhas vazias (timeout do readline)
                    if not linha_raw:
                        continue

                    try:
                        linha = linha_raw.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        log(f"✗ Erro de decodificação UTF-8: {linha_raw}")
                        continue

                    if not linha:
                        continue

                    # Tenta parsear como JSON
                    try:
                        dados = json.loads(linha)

                        # Ignora mensagens de erro vindas do Arduino
                        if 'erro' in dados:
                            log(f"⚠ Arduino reportou erro: {dados['erro']}")
                            continue

                        enviar_para_api(dados)

                    except json.JSONDecodeError:
                        log(f"✗ JSON inválido recebido: {linha!r}")

                    time.sleep(0.1)

        except serial.SerialException as e:
            log(f"✗ Erro na porta serial: {e}")
            log("Tentando reconectar em 5 segundos...")
            time.sleep(5)

        except KeyboardInterrupt:
            log("\nEncerrando leitura serial.")
            sys.exit(0)


if __name__ == '__main__':
    ler_serial()