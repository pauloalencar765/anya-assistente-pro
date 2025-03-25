from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Endpoint inicial
@app.route("/", methods=["GET"])
def home():
    return "Anya Assistente está no ar!"

# Endpoint do webhook da Z-API
@app.route("/zapi-webhook", methods=["POST"])
def receber_webhook():
    data = request.json
    print("Webhook recebido:", data)
    return jsonify({"status": "recebido"}), 200


    # Extrair número e mensagem
    try:
        numero = dados["message"]["from"]
        mensagem = dados["message"]["content"].strip().lower()
    except (KeyError, TypeError):
        return jsonify({"status": "erro", "detalhe": "dados inválidos"}), 400

    # Verifica se a mensagem pede motivação
    if any(palavra in mensagem for palavra in ["motiva", "motivacional", "ânimo", "força"]):
        resposta = "Você é capaz de conquistar tudo o que deseja. Acredite em você! 💪"
        enviar_resposta(numero, resposta)

    return jsonify({"status": "mensagem recebida com sucesso"}), 200

# Função para enviar mensagem via Z-API
def enviar_resposta(numero, texto):
    ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCFC0BB2079B45ED702078B617E_ID")
    ZAPI_TOKEN = os.getenv("ZAP3DEBB2A5B63D80B04CBFFA8592F99CB9")

    if not ZAPI_INSTANCE_ID or not ZAPI_TOKEN:
        print("Variáveis de ambiente não definidas.")
        return

    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text"
    payload = {"phone": numero, "message": texto}

    try:
        r = requests.post(url, json=payload)
        print("Resposta enviada:", r.status_code)
    except Exception as e:
        print("Erro ao enviar resposta:", str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
