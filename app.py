from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import threading
import time
import requests
import json

app = Flask(__name__)

# === CONFIGURAÇÃO ===

ZAPI_INSTANCE_ID = "FC0B82079B45ED7020B78617"  # Seu ID da Z-API
ZAPI_TOKEN = "7uw0lx81pjzrs0r1"               # Seu token da Z-API

# === CONTATOS E GRUPOS ===

GRUPOS_MOTIVACAO = [
    "FAMÍLIA", "FAMÍLIA MOUTA", "Família Figueiredo",
    "Best Family", "Diretoria", "Sócios Mananciais", "Irmãos"
]
GRUPO_LOG = "Assistente Pessoal"
MENSAGEM_DIARIA = "Bom dia! Que hoje seja um dia produtivo e cheio de realizações. 💪"

# === CONTROLE DE INTERAÇÕES ===

ultimas_interacoes = {}

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
        print(f"[ERRO] Falha ao enviar mensagem para {destinatario}: {e}")

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
                enviar_mensagem(contato, "👋 Oi! Você mandou uma mensagem e ainda não tive tempo de responder. Em que posso te ajudar?")
                ultimas_interacoes.pop(contato)
        time.sleep(60)

# === ENDPOINTS ===

@app.route("/zapi-webhook", methods=["POST"])
def receber_webhook():
    dados = request.json

    # Log bruto para debug
    enviar_mensagem(GRUPO_LOG, f"[DEBUG] Webhook bruto recebido:\n{json.dumps(dados, indent=2)}")

    try:
        # Tenta extrair conteúdo da mensagem
        mensagem = dados.get('message') or dados.get('body') or 'sem_conteudo'
        remetente = dados.get('phone') or dados.get('chatId') or 'desconhecido'

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
    threading.Thread(target=agendar_mensagens_diarias, daemon=True).start()
    threading.Thread(target=monitorar_inatividade, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
