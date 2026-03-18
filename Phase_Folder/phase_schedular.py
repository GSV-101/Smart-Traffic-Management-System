import threading
import time
import requests
from Traffic_Mode.Normal_Mode.Optimization_And_Detection.normal_logic import NormalMode
from Traffic_Mode.Emergency_Mode.Optimization_And_Detection.emergency_logic import EmergencyMode

SERVER_URL = "http://127.0.0.1:8000"

class Phase_Schedular(threading.Thread):

    def __init__(self, thread_name, phase_list):
        threading.Thread.__init__(self, name=thread_name)

        self.phase_list = phase_list
        self.phase_index = 0
        self.is_running = True
        self.cycle_count = 0
        self.mode = "NORMAL"

        self.normal = NormalMode(phase_list) 
        self.emergency = EmergencyMode(phase_list)
        self.control_mutex = threading.Lock()

    def run(self):
        while(self.is_running):
            curr_phase = self.phase_list[self.phase_index]

            # ================= NORMAL MODE =================
            if(self.getMode() == "NORMAL"):
                curr_phase.freeze_time()
                duration = curr_phase.getLock_time()
                curr_phase.setState("GREEN")

                temp1 = time.time()
                next_phase_index = (self.phase_index + 1) % len(self.phase_list)

                while((time.time() - temp1) < duration):
                    self.normal.compute_time(next_phase_index)
                    next_phase_index = (next_phase_index + 1) % len(self.phase_list)
                    time.sleep(1)

                # 🚨 LOCAL PRIORITY (NO MODE CHANGE)
                jump_to_lane = None
                if(self.normal.getEmergency_Detected()):
                    lane_list = self.normal.getEmergency_Lane()
                    if(len(lane_list) > 0):
                        jump_to_lane = lane_list[0]
                        # clear local detection
                        for lane in lane_list:
                            self.normal.setEmergency(False, lane)

                # YELLOW phase
                curr_phase.setState("YELLOW")
                self.sync_dashboard_state(self.phase_index, "YELLOW") # Added sync
                time.sleep(5)

                curr_phase.unlock()
                curr_phase.setState("RED")
                self.sync_dashboard_state(self.phase_index, "RED") # Added sync

                # 🚀 PRIORITY JUMP
                if(jump_to_lane is not None):
                    self.phase_index = jump_to_lane
                else:
                    self.phase_index = (self.phase_index + 1) % len(self.phase_list)

            # ================= EMERGENCY MODE =================
            else:
                if(self.emergency.getEmergency_Detected()):
                    lane_list = self.emergency.getEmergency_Lane()
                    if(len(lane_list) > 0):
                        self.phase_index = lane_list[0]

                curr_phase = self.phase_list[self.phase_index]
                curr_phase.freeze_time()
                duration = curr_phase.getLock_time()
                curr_phase.setState("GREEN")

                temp1 = time.time()
                next_phase_index = (self.phase_index + 1) % len(self.phase_list)

                while((time.time() - temp1) < duration):
                    self.emergency.compute_time(next_phase_index)
                    next_phase_index = (next_phase_index + 1) % len(self.phase_list)
                    time.sleep(1)

                if(self.emergency.getEmergency_Detected()):
                    curr_phase.unlock()
                    curr_phase.setState("RED")
                    continue

                curr_phase.setState("YELLOW")
                self.sync_dashboard_state(self.phase_index, "YELLOW")
                time.sleep(5)

                curr_phase.unlock()
                curr_phase.setState("RED")
                self.sync_dashboard_state(self.phase_index, "RED")

                self.phase_index = (self.phase_index + 1) % len(self.phase_list)

                if(self.cycle_count < 1):
                    self.cycle_count += 1
                else:
                    self.cycle_count = 0
                    self.setMode("NORMAL")

    # ================= HELPERS & TRIGGERS =================
    
    def sync_dashboard_state(self, lane_id, state):
        """Helper to ensure Yellow/Red transitions appear on UI instantly"""
        try:
            requests.post(f"{SERVER_URL}/update-status", json={
                "lane_id": lane_id,
                "state": state,
                "timer": 0 if state == "RED" else 5
            }, timeout=0.05)
        except:
            pass

    def handle_incoming_emergency(self, lane_id):
        self.emergency.setEmergency(True, int(lane_id))
        self.setMode("EMERGENCY")

    def getMode(self):
        with self.control_mutex:
            return self.mode

    def setMode(self, mode):
        with self.control_mutex:
            self.mode = mode