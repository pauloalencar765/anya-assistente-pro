from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import threading
import time
import requests
import json
import logging

app = Flask(__name__)

# === CONFIGURAÇÃO ===

CLIENT_TOKEN = "Faff5c7d30dbe4802bba8a32859847564S"
ZAPI_INSTANCE_ID = "3DEBB2A5B63D80B04CBFFA8592F99CB9"
ZAPI_TOKEN = "FC0BB2079B45ED702078B617"
SEU_NUMERO = "559888425166"

# === LOGGING ===

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === CONTATOS E GRUPOS ===

GRUPOS_MOTIVACAO = [
    "FAMÍLIA", "FAMÍLIA MOUTA", "Família Figueiredo",
    "Best Family", "Diretoria", "Sócios Mananciais", "Irmãos"
]

GRUPO_LOG_NOME = "Assistente Pessoal"
GRUPO_LOG_ID = None

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
    headers = {
        'Content-Type': 'application/json',
        'Client-Token': CLIENT_TOKEN
    }
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        logging.info(f"Mensagem enviada para {destinatario}: {mensagem}")
    except requests.exceptions.RequestException as e:
        logging.error(f"[ERRO] Falha ao enviar mensagem para {destinatario}: {e}")

def obter_id_grupo_por_nome(nome_grupo):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/chats"
    headers = {
        "Client-Token": CLIENT_TOKEN
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        logging.info(f"[DEBUG] Conteúdo retornado por /chats: {json.dumps(data, indent=2, ensure_ascii=False)}")

        chats = data.get("chats") if isinstance(data, dict) else data
        if isinstance(chats, str):
            chats = json.loads(chats)

        for chat in chats:
            if isinstance(chat, dict) and chat.get("name") == nome_grupo:
                logging.info(f"[INFO] ID do grupo '{nome_grupo}' encontrado: {chat.get('id')}")
                return chat.get("id")

        logging.warning(f"[AVISO] Grupo '{nome_grupo}' não encontrado.")
    except Exception as e:
        logging.error(f"[ERRO] Falha ao buscar grupo '{nome_grupo}': {e}")
    return None

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

        if GRUPO_LOG_ID:
            enviar_mensagem(GRUPO_LOG_ID, f"✅ Mensagens motivacionais enviadas para: {', '.join(GRUPOS_MOTIVACAO)}")

def monitorar_inatividade():
    while True:
        agora = datetime.now()
        contatos_inativos = []

        for contato, timestamp in list(ultimas_interacoes.items()):
            if agora - timestamp > timedelta(minutes=INATIVIDADE_TIMEOUT_MINUTOS):
                contatos_inativos.append(contato)

        for contato in contatos_inativos:
            enviar_mensagem(contato, "👋 Oi! Você mandou uma mensagem e ainda não tive tempo de responder. Em que posso te ajudar?")
            ultimas_interacoes.pop(contato)

        time.sleep(INTERVALO_MONITORAMENTO_INATIVIDADE_SEGUNDOS)

# === ENDPOINTS ===

@app.route("/zapi-webhook", methods=["POST"])
def receber_webhook():
    global GRUPO_LOG_ID
    dados = request.json
    logging.info(f"Dados recebidos no webhook: {dados}")

    mensagem_conteudo = (
        dados.get("message") or
        dados.get("body") or
        dados.get("text", {}).get("message", "") or
        "sem_conteudo"
    )

    remetente = dados.get("phone") or dados.get("chatId") or "desconhecido"
    chat_name = dados.get("chatName", "Desconhecido")
    participante = dados.get("participantPhone", "Desconhecido")

    try:
        conteudo = mensagem_conteudo.strip()
        ultimas_interacoes[remetente] = datetime.now()

        if not GRUPO_LOG_ID:
            GRUPO_LOG_ID = obter_id_grupo_por_nome(GRUPO_LOG_NOME)

        log = f"📥 Mensagem de {remetente}: {conteudo}"
        if GRUPO_LOG_ID:
            enviar_mensagem(GRUPO_LOG_ID, log)

        if f"@{SEU_NUMERO}" in conteudo or "Paulo" in conteudo:
            mensagem_mencao = (
                f"📣 Você foi mencionado no grupo '{chat_name}' por {participante}:\n\n{conteudo}"
            )
            if GRUPO_LOG_ID:
                enviar_mensagem(GRUPO_LOG_ID, mensagem_mencao)

        return jsonify({"status": "mensagem registrada"})

    except Exception as e:
        if GRUPO_LOG_ID:
            enviar_mensagem(GRUPO_LOG_ID, f"[ERRO] Falha no processamento do webhook: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/")
def index():
    return "Anya Assistente está no ar!"

# === EXECUÇÃO ===

if __name__ == "__main__":
    GRUPO_LOG_ID = obter_id_grupo_por_nome(GRUPO_LOG_NOME)
    threading.Thread(target=agendar_mensagens_diarias, daemon=True).start()
    threading.Thread(target=monitorar_inatividade, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
