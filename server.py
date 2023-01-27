from flask import Flask, request, jsonify
from puppy import pup
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins='*')

#hacky as hell but for now good enough
puppy_running = False


@socketio.on('connect')
def test_connect():
    emit('connected',  {'data':'🐶🐶🐶'})


@app.route('/fetch', methods=['POST'])
def fetch():
    global puppy_running
    data = request.json
    start = data["start"]
    target = data["target"]
    pupper = pup.Puppy(start, target)
    if puppy_running:
        return jsonify({"result": "[!] sorry, puppy is busy at the moment\n[!] retry in a few minutes..."})
    puppy_running = True
    result = pupper.run()
    puppy_running = False
    return jsonify(result)

socketio.run(app)
