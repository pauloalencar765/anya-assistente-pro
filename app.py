from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import threading
import time
import requests
import json
import logging

app = Flask(__name__)

# === CONFIGURAÇÃO ===

ZAPI_INSTANCE_ID = "FC0B82079B45ED7020B78617"
ZAPI_TOKEN = "7uw0lx81pjzrs0r1"

# === CONTATOS E GRUPOS ===

GRUPOS_MOTIVACAO = [
    "FAMÍLIA", "FAMÍLIA MOUTA", "Família Figueiredo",
    "Best Family", "Diretoria", "Sócios Mananciais", "Irmãos"
]
GRUPO_LOG = "Assistente Pessoal"
MENSAGEM_DIARIA = "Bom dia! Que hoje seja um dia produtivo e cheio de realizações. 💪"

# === CONTROLE DE INTERAÇÕES ===

ultimas_interacoes = {}
contatos_inativos = {}

# === FUNÇÕES ===

def enviar_mensagem(destinatario, mensagem):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": destinatario,
        "message": mensagem
    }
    headers = {'Content-Type': 'application/json'}
    try:
        requests.post(url, data=json.dumps(payload), headers=headers)
    except Exception as e:
        logging.error(f"[ERRO] Falha ao enviar mensagem para {destinatario}: {e}")

def agendar_mensagens_diarias():
    while True:
        agora = datetime.now()
        proxima_execucao = agora.replace(hour=6, minute=0, second=0, microsecond=0)
        if agora >= proxima_execucao:
            proxima_execucao += timedelta(days=1)
        tempo_espera = (proxima_execucao - agora).total_seconds()
        time.sleep(tempo_espera)

        for grupo in GRUPOS_MOTIVACAO:
            enviar_mensagem(grupo, MENSAGEM_DIARIA)
        enviar_mensagem(GRUPO_LOG, f"✅ Mensagens motivacionais enviadas para: {', '.join(GRUPOS_MOTIVACAO)}")

def monitorar_inatividade():
    while True:
        agora = datetime.now()
        for contato, timestamp in list(ultimas_interacoes.items()):
            if agora - timestamp > timedelta(minutes=5):
                if contato not in contatos_inativos:
                    enviar_mensagem(contato, "👋 Oi! Você mandou uma mensagem e ainda não tive tempo de responder. Em que posso te ajudar?")
                    contatos_inativos[contato] = True
        time.sleep(60)

# === ENDPOINTS ===

@app.route("/zapi-webhook", methods=["POST"])
def receber_webhook():
    try:
        dados = request.json
        logging.info(f"Dados recebidos no webhook: {dados}")

        if not dados or 'message' not in dados:
            return jsonify({"status": "sem mensagem"}), 400

        mensagem = dados.get('message') or dados.get('body') or 'sem_conteudo'
        remetente = dados.get('phone') or dados.get('chatId') or 'desconhecido'
        conteudo = mensagem.strip()

        ultimas_interacoes[remetente] = datetime.now()
        log = f"📥 Mensagem de {remetente}: {mensagem}"
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
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=agendar_mensagens_diarias, daemon=True).start()
    threading.Thread(target=monitorar_inatividade, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
