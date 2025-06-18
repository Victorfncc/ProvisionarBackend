from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import paramiko
import threading
import time
import os

app = Flask(__name__)
CORS(app)  # Libera CORS para todas origens - para produção configure melhor

ssh_client = None
ssh_shell = None
lock = threading.Lock()

host = "10.11.104.2"
port = 22
user = "root"
password = "berg88453649"

def send_command(cmd, sleep=1.5):
    global ssh_shell
    if ssh_shell is None:
        return "❌ Não conectado."
    with lock:
        ssh_shell.send(cmd + "\n")
        time.sleep(sleep)
        output = ""
        while ssh_shell.recv_ready():
            output += ssh_shell.recv(65535).decode("utf-8")
        return output

@app.route("/")
def index():
    connected = ssh_client is not None and ssh_shell is not None
    return render_template("index.html", connected=connected)

@app.route("/connect", methods=["POST"])
def connect():
    global ssh_client, ssh_shell
    if ssh_client is not None:
        return jsonify({"status": "already_connected"})
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=host, port=port, username=user, password=password, timeout=10)
        ssh_shell = ssh_client.invoke_shell()
        time.sleep(1)
        while ssh_shell.recv_ready():
            ssh_shell.recv(65535)
        return jsonify({"status": "connected"})
    except Exception as e:
        ssh_client = None
        ssh_shell = None
        return jsonify({"status": "error", "message": str(e)})

@app.route("/disconnect", methods=["POST"])
def disconnect():
    global ssh_client, ssh_shell
    try:
        if ssh_shell:
            ssh_shell.close()
        if ssh_client:
            ssh_client.close()
    finally:
        ssh_shell = None
        ssh_client = None
    return jsonify({"status": "disconnected"})

@app.route("/send_command", methods=["POST"])
def command():
    cmd = request.json.get("command", "")
    if not cmd:
        return jsonify({"output": "⚠️ Nenhum comando enviado."})
    output = send_command(cmd)
    return jsonify({"output": output})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
