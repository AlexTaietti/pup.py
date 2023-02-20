from flask import Flask, request, jsonify, send_from_directory
from puppy import pup
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__, static_url_path='', static_folder="webapp/dist")
socketio = SocketIO(app, cors_allowed_origins='*')

MAX_PUPPERS = 3
puppy_roster = dict()


@app.route("/", methods=["GET"])
def home():
    return send_from_directory("webapp/dist", "index.html")


@socketio.on('connect')
def test_connect():
    print(f"[*] server: socket {request.sid} connected")
    socketio.emit('connected',  {'data':'🐶🐶🐶'})


@socketio.on('fetch')
def fetch_target(data):
    global puppy_roster
    start = data["start"]
    target = data["target"]
    socket_bound_pupper = puppy_roster.get(request.sid)
    if socket_bound_pupper:
        socket_bound_pupper.goodbye()
        del puppy_roster[request.sid]
        new_pupper = pup.Puppy(socketio.emit)
        puppy_roster[request.sid] = new_pupper
        new_pupper.run(start, target, request.sid)
    else:
        connected_sockets = puppy_roster.keys()
        for socket in connected_sockets:
            puppy = puppy_roster[socket]
            if not puppy.running:
                puppy_roster[request.sid] = puppy
                puppy.run(start, target, request.sid)
                return
        if len(puppy_roster.keys()) < MAX_PUPPERS:
            new_pupper = pup.Puppy(socketio.emit)
            puppy_roster[request.sid] = new_pupper
            new_pupper.run(start, target, request.sid)
        else:
            socketio.emit('all puppers busy',  {'data':'💔'}, to=request.sid)


@socketio.on('disconnect')
def disconnect_client():
    print(f"[*] server: socket {request.sid} disconnected")
    socket_bound_pupper = puppy_roster.get(request.sid)
    if socket_bound_pupper:
        if socket_bound_pupper.running:
            socket_bound_pupper.running = False
        del puppy_roster[request.sid]

socketio.run(app, host='0.0.0.0', debug=True)
