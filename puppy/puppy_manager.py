import time

from puppy.pup import Puppy
from multiprocessing.pool import ThreadPool


class PuppyManager:

    max_puppies = 5
    polite_delay = 0.15  # in seconds

    def __init__(self, websockets_emitter):
        self.puppy_queue = list()
        self.puppy_roster = dict()
        self.available_puppies = list()
        self.websocket_events_emitter = websockets_emitter
        self.pool_of_threads = ThreadPool(self.max_puppies)
        self.running = False

    def stop(self):
        self.running = False
        self.pool_of_threads.close()
        self.pool_of_threads.join()
        print("[*] all puppy threads closed")

    def get_available_puppy(self, socket_id):
        if self.puppy_roster:
            puppy = self.get_socket_bound_puppy(socket_id)
            if puppy:
                self.stop_puppy(socket_id)
                return puppy
            if self.available_puppies:
                pupper = self.available_puppies.pop()
                return pupper
            if len(self.puppy_roster) < self.max_puppies:
                pupper = Puppy(socket_id)
                return pupper
            return None
        pupper = Puppy(socket_id)
        return pupper

    def stop_puppy(self, socket_id):
        puppy = self.puppy_roster[socket_id]
        if puppy:
            puppy.reset()
            del self.puppy_roster[socket_id]
            for pupper in self.puppy_queue:
                if pupper is puppy:
                    self.puppy_queue.remove(pupper)
            self.available_puppies.insert(0, puppy)

    def get_socket_bound_puppy(self, socket_id):
        return self.puppy_roster.get(socket_id)

    def let_dog_out(self, start, target, socket_id):
        puppy = self.get_available_puppy(socket_id)
        if puppy:
            puppy.init_run_parameters(start, target, socket_id)
            self.puppy_roster[socket_id] = puppy
            print(f"[*] new puppy added to roster for socket {socket_id}")
            return self.puppy_queue.insert(0, puppy)
        self.websocket_events_emitter('all puppers busy', 'All puppies are currently busy, retry later', to=socket_id)

    def handle_threaded_puppy(self, threaded_puppy):
        if threaded_puppy.update_data:
            self.websocket_events_emitter("puppy live update", {"update": threaded_puppy.update_data}, to=threaded_puppy.socket_id)
        if threaded_puppy.next_article:
            self.puppy_queue.append(threaded_puppy)
            return
        self.stop_puppy(threaded_puppy.socket_id)

    def process_tasks(self):
        self.running = True
        while self.running:
            time.sleep(self.polite_delay)
            if self.puppy_queue:
                pupper = self.puppy_queue.pop()
                if not pupper.next_article:
                    self.pool_of_threads.apply_async(pupper.tokenize_target, callback=self.handle_threaded_puppy)
                self.pool_of_threads.apply_async(pupper.go, callback=self.handle_threaded_puppy)

