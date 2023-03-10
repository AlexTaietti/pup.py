import time

from . import pup
from threading import Thread


MAX_PUPPERS = 5
POLITE_DELAY = 0.2 # stagger requests to respect our beloved wikipedia servers <3
PUPPY_ROSTER = dict()

ws_emitter = None
TASK_QUEUE = list() # will hold the tasks to be executed by the puppers


def init_ws_events(ws_emit):
    global ws_emitter
    print("[*] server: initialising ws emitter")
    ws_emitter = ws_emit


def get_puppy(socket_id):
    global PUPPY_ROSTER
    global MAX_PUPPERS
    global ws_emitter
    if not PUPPY_ROSTER:
        pupper = pup.Puppy(ws_emitter)
        return pupper
    puppy = get_socket_bound_puppy(socket_id)
    if puppy:
        stop_puppy(socket_id)
        return puppy
    for socket in PUPPY_ROSTER:
        puppy = PUPPY_ROSTER[socket]
        if not puppy.socket_id:
            del PUPPY_ROSTER[socket_id]
            return puppy
    if len(PUPPY_ROSTER.keys()) < MAX_PUPPERS:
        pupper = pup.Puppy(ws_emitter)
        return pupper
    return None


def get_socket_bound_puppy(socket_id):
    return PUPPY_ROSTER.get(socket_id)


def stop_puppy(socket_id):
    global TASK_QUEUE
    global PUPPY_ROSTER
    puppy = PUPPY_ROSTER[socket_id]
    if puppy:
        for task in TASK_QUEUE:
            if task[0] is puppy:
                task_index = TASK_QUEUE.index(task)
                TASK_QUEUE.pop(task_index)
        del PUPPY_ROSTER[socket_id]
        puppy.unbind()


def let_dog_out(start, target, socket_id):
    puppy = get_puppy(socket_id)
    if puppy:
        PUPPY_ROSTER[socket_id] = puppy
        return TASK_QUEUE.insert(0, (puppy, "init_run", (start, target, socket_id, TASK_QUEUE)))
    ws_emitter('all puppers busy',  'All puppies are currently busy, retry later', to=socket_id)


def process_tasks():
    global PUPPY_ROSTER
    global TASK_QUEUE
    while True:
        time.sleep(POLITE_DELAY)
        if TASK_QUEUE:
            pupper, action, args = TASK_QUEUE.pop()
            puppy_action = getattr(pupper, action)
            Thread(target=puppy_action, args=args).start()  # todo: switch to threadpool class
