from flask import Flask, request, jsonify, send_from_directory
from puppy import pup
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__, static_url_path='', static_folder="webapp/dist")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins='*')

#hacky as hell but for now good enough
puppy_running = False


@app.route("/", methods=["GET"])
def home():
    return send_from_directory("webapp/dist", "index.html")


@socketio.on('connect')
def test_connect():
    socketio.emit('connected',  {'data':'🐶🐶🐶'})


@socketio.on('fetch')
def fetch_target(data):
    global puppy_running
    start = data["start"]
    target = data["target"]
    pupper = pup.Puppy(start, target)
    if puppy_running:
        return socketio.emit("busy", "[!] sorry, puppy is busy at the moment\n[!] retry in a few minutes...")
    puppy_running = True
    result = pupper.run(socketio)
    puppy_running = False
    return socketio.emit("found", {"result": result})

socketio.run(app)
