from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO
from puppy.puppy_manager import PuppyManager
from threading import Thread
import signal

app = Flask(__name__, static_url_path='', static_folder="webapp/dist")
socketio = SocketIO(app, cors_allowed_origins='*')
puppy_manager = PuppyManager(socketio.emit)


@app.route("/", methods=["GET"])
def home():
    return send_from_directory("webapp/dist", "index.html")


@socketio.on('connect')
def test_connect():
    print(f"[*] server: socket {request.sid} connected")
    socketio.emit('connected',  {'data': '🐶🐶🐶'})


@socketio.on('fetch')
def fetch_target(data):
    start = data["start"]
    target = data["target"]
    puppy_manager.let_dog_out(start, target, request.sid)
    socketio.emit('running', '🚀', to=request.sid)


@socketio.on('stop')
def stop_puppy():
    puppy_manager.stop_puppy(request.sid)
    socketio.emit('stopped', "💔", to=request.sid)


@socketio.on('disconnect')
def disconnect_client():
    print(f"[*] server: socket {request.sid} disconnected")
    socket_bound_pupper = puppy_manager.get_socket_bound_puppy(request.sid)
    if socket_bound_pupper:
        puppy_manager.stop_puppy(request.sid)


def stop_server(*args):
    puppy_manager.stop()
    print("[*] shutting down")
    exit()


if __name__ == "__main__":

    # handle signals
    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGTERM, stop_server)

    # let's go!
    print("[*] let the dogs out!")

    # start processing puppy actions in a new thread
    Thread(name="puppy_queue", target=puppy_manager.process_tasks).start()

    # start socket server
    socketio.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True)
