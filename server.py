from flask import Flask, request, jsonify, send_from_directory
from puppy import pup
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__, static_url_path='', static_folder="webapp/dist")
socketio = SocketIO(app, cors_allowed_origins='*')

@app.route("/", methods=["GET"])
def home():
    return send_from_directory("webapp/dist", "index.html")


@socketio.on('connect')
def test_connect():
    print(f"[*] server: connection received from socket {request.sid}")
    socketio.emit('connected',  {'data':'🐶🐶🐶'})


@socketio.on('fetch')
def fetch_target(data):
    start = data["start"]
    target = data["target"]
    pupper = pup.Puppy(start, target, socketio, request.sid)
    pupper.run()

socketio.run(app)
