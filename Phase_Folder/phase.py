import threading

class Phase:
    def __init__(self, name, video_src, signals):
        self.name = name
        self.video = video_src
        self.signal = signals  # Signals Assigned

        self.vehicle_count = 0
        self.proposed_time = 45
        self.lock_time = 45

        self.lock = False
        self.state = "RED"  # RED, YELLOW, GREEN

        self.frame = None
        self.mutex = threading.Lock()

    def getState(self):
        with self.mutex:
            return self.state

    def setState(self, state):
        with self.mutex:
            self.state = state

    def getLock(self):
        with self.mutex:
            return self.lock

    def freeze_time(self):
        with self.mutex:
            self.lock_time = self.proposed_time
            self.lock = True

    def unlock(self):
        with self.mutex:
            self.lock = False

    def getProposed_time(self):
        with self.mutex:
            return self.proposed_time

    def setProposed_time(self, proposed_time):
        with self.mutex:
            if not self.lock:
                self.proposed_time = proposed_time

    def getLock_time(self):
        with self.mutex:
            return self.lock_time

    def ready_for_computation(self):
        with self.mutex:
            ready = (self.state == "RED") and (not self.lock)
            return ready

    def setFrame(self, frame):
        with self.mutex:
            self.frame = frame

    def getFrame(self):
        with self.mutex:
            if self.frame is None:
                return None
            return self.frame.copy()

    def setVehicleCount(self, count):
        with self.mutex:
            self.vehicle_count = count

    def getVehicleCount(self):
        with self.mutex:
            return self.vehicle_count