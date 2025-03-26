from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import threading
import time
import requests
import json
import logging

app = Flask(__name__)

# === CONFIGURAÇÃO ===

ZAPI_INSTANCE_ID = "FC0BB2079B45ED702078B617"
ZAPI_TOKEN = "3DEBB2A5B63D80B04CBFFA8592F99CB9"

# === LOGGING ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === CONTATOS E GRUPOS ===

GRUPOS_MOTIVACAO = [
    "FAMÍLIA", "FAMÍLIA MOUTA", "Família Figueiredo",
    "Best Family", "Diretoria", "Sócios Mananciais", "Irmãos"
]
GRUPO_LOG = "Assistente Pessoal"
MENSAGEM_DIARIA = "Bom dia! Que hoje seja um dia produtivo e cheio de realizações. 💪"

# === CONTROLE DE INTERAÇÕES ===

ultimas_interacoes = {}
INATIVIDADE_TIMEOUT_MINUTOS = 5
INTERVALO_MONITORAMENTO_INATIVIDADE_SEGUNDOS = 60

# === FUNÇÕES ===

def enviar_mensagem(destinatario, mensagem):
    if not ZAPI_INSTANCE_ID or not ZAPI_TOKEN:
        logging.error(f"Não é possível enviar mensagem para {destinatario}. Configurações da Z-API não definidas.")
        return

    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": destinatario,
        "message": mensagem
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        logging.info(f"Mensagem enviada para {destinatario}: {mensagem}")
    except requests.exceptions.RequestException as e:
        logging.error(f"[ERRO] Falha ao enviar mensagem para {destinatario}: {e}")

def agendar_mensagens_diarias():
    while True:
        agora = datetime.now()
        proxima_execucao = agora.replace(hour=6, minute=0, second=0, microsecond=0)
        if agora >= proxima_execucao:
            proxima_execucao += timedelta(days=1)
        tempo_espera = (proxima_execucao - agora).total_seconds()
        logging.info(f"Próxima execução de mensagens diárias em {tempo_espera:.0f} segundos.")
        time.sleep(tempo_espera)

        for grupo in GRUPOS_MOTIVACAO:
            enviar_mensagem(grupo, MENSAGEM_DIARIA)
        enviar_mensagem(GRUPO_LOG, f"✅ Mensagens motivacionais enviadas para: {', '.join(GRUPOS_MOTIVACAO)}")

def monitorar_inatividade():
    while True:
        agora = datetime.now()
        contatos_inativos = []
        for contato, timestamp in list(ultimas_interacoes.items()):
            if agora - timestamp > timedelta(minutes=INATIVIDADE_TIMEOUT_MINUTOS):
                contatos_inativos.append(contato)

        for contato in list(contatos_inativos):
            enviar_mensagem(contato, f"👋 Oi! Você mandou uma mensagem e ainda não tive tempo de responder. Em que posso te ajudar?")
            ultimas_interacoes.pop(contato)

        time.sleep(INTERVALO_MONITORAMENTO_INATIVIDADE_SEGUNDOS)

# === ENDPOINTS ===

@app.route("/zapi-webhook", methods=["POST"])
def receber_webhook():
    dados = request.json
    logging.info(f"Dados recebidos no webhook: {dados}")

    mensagem_conteudo = dados.get('message') or dados.get('body') or 'sem_conteudo'
    remetente = dados.get('phone') or dados.get('chatId') or "desconhecido"

    try:
        conteudo = mensagem_conteudo.strip()
        ultimas_interacoes[remetente] = datetime.now()
        log = f"📥 Mensagem de {remetente}: {conteudo}"
        enviar_mensagem(GRUPO_LOG, log)
        return jsonify({"status": "mensagem registrada"})

    except Exception as e:
        enviar_mensagem(GRUPO_LOG, f"[ERRO] Falha no processamento do webhook: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/")
def index():
    return "Anya Assistente está no ar!"

# === EXECUÇÃO ===

if __name__ == "__main__":
    threading.Thread(target=agendar_mensagens_diarias, daemon=True).start()
    threading.Thread(target=monitorar_inatividade, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
