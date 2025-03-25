from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import threading
import time
import requests
import json

app = Flask(__name__)

# Lista de contatos e grupos
GRUPOS_MOTIVACAO = [
    "FAMÍLIA", "FAMÍLIA MOUTA", "Família Figueiredo",
    "Best Family", "Diretoria", "Sócios Mananciais", "Irmãos"
]
GRUPO_LOG = "Assistente Pessoal"

# Mensagem motivacional fixa (pode ser personalizada depois)
MENSAGEM_DIARIA = "Bom dia! Que hoje seja um dia produtivo e cheio de realizações. 💪"

# Armazena última interação para controle de inatividade
ultimas_interacoes = {}

# Envia mensagem via Z-API
def enviar_mensagem(destinatario, mensagem):
    url = "https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": destinatario,
        "message": mensagem
    }
    headers = {'Content-Type': 'application/json'}
    requests.post(url, data=json.dumps(payload), headers=headers)

# Envia mensagens motivacionais às 6h da manhã
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

# Responde mensagens após 5 minutos se não houver resposta
def monitorar_inatividade():
    while True:
        agora = datetime.now()
        for contato, timestamp in list(ultimas_interacoes.items()):
            if agora - timestamp > timedelta(minutes=5):
                enviar_mensagem(contato, "👋 Oi! Você mandou uma mensagem e ainda não tive tempo de responder. Em que posso te ajudar?")
                ultimas_interacoes.pop(contato)
        time.sleep(60)

# Webhook Z-API
@app.route("/zapi-webhook", methods=["POST"])
def receber_webhook():
    dados = request.json
    if not dados or 'message' not in dados:
        return jsonify({"status": "sem mensagem"}), 400

    mensagem = dados['message']
    remetente = dados.get('phone') or dados.get('chatId')
    conteudo = mensagem.strip()

    # Atualiza horário da última mensagem recebida
    ultimas_interacoes[remetente] = datetime.now()

    # Registra a mensagem recebida no grupo de log
    log = f"📥 Mensagem de {remetente}: {conteudo}"
    enviar_mensagem(GRUPO_LOG, log)

    return jsonify({"status": "mensagem registrada"})

# Rota básica para teste
@app.route("/")
def index():
    return "Anya Assistente está no ar!"

if __name__ == "__main__":
    # Inicia agendamentos em background
    threading.Thread(target=agendar_mensagens_diarias, daemon=True).start()
    threading.Thread(target=monitorar_inatividade, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)