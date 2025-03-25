from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Anya Assistente está no ar!"

@app.route("/zapi-webhook", methods=["POST"])
def receber_webhook():
    data = request.json
    print("📩 Webhook recebido:", data)
    
    # Resposta padrão
    return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
