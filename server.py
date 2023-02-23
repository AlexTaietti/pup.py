from flask import Flask, request, jsonify, send_from_directory
from puppy import pup
from flask_cors import CORS
from flask_socketio import SocketIO
from puppy import puppy_manager
from threading import Thread

app = Flask(__name__, static_url_path='', static_folder="webapp/dist")
socketio = SocketIO(app, cors_allowed_origins='*')


@app.before_first_request
def initialise_ws():
    puppy_manager.init_ws_events(socketio.emit)


@app.route("/", methods=["GET"])
def home():
    return send_from_directory("webapp/dist", "index.html")


@socketio.on('connect')
def test_connect():
    print(f"[*] server: socket {request.sid} connected")
    socketio.emit('connected',  {'data':'🐶🐶🐶'})


@socketio.on('fetch')
def fetch_target(data):
    start = data["start"]
    target = data["target"]
    puppy_manager.let_dog_out(start, target, request.sid)


@socketio.on('disconnect')
def disconnect_client():
    print(f"[*] server: socket {request.sid} disconnected")
    puppy_manager.get_socket_bound_puppy(request.sid)
    if socket_bound_pupper:
        puppy_manager.stop_puppy(request.sid)


puppy_manager.init_ws_events(socketio.emit)
Thread(target=puppy_manager.process_tasks).start()
socketio.run(app, host='0.0.0.0', debug=True)

