from ultralytics import YOLO
import time, cv2
import requests

SERVER_URL = "http://127.0.0.1:8000"
SQUARE_CODE = "A1"
CITY = "Indore"

class NormalMode:
    def __init__(self, phase_list):
        self.phase_list = phase_list
        self.model = YOLO("Models/yolov8n.pt")
        self.accident_model = YOLO("Models/best_accident.pt")
        self.ambulance_model = YOLO("Models/best_ambulance.pt")

        self.MIN_GREEN_TIME = 10 
        self.MAX_GREEN_TIME = 50

        self.Emergency_Detected = set()
        self.Accident_Detected = set()

        # ✅ NEW: prevent repeated API calls
        self.sent_accident = set()
        self.sent_emergency = set()

    def compute_time(self, phase_index):
        phase = self.phase_list[phase_index]
        if (not phase.ready_for_computation()):
            return

        car_count = 0
        truck_count = 0
        bus_count = 0
        motorcycle_count = 0

        FRAME_SAMPLE = 3

        for i in range(0, FRAME_SAMPLE):
            frame = phase.getFrame()

            if(frame is None):
                continue
        
            self.detect_accident(phase_index, frame)

            if phase_index in self.Accident_Detected:
                self.Accident_Detected.discard(phase_index)
            
            self.detect_emergency(phase_index, frame)

            output = self.model(frame)

            for result in output:
                boxes = result.boxes
                if (boxes is not None): 
                    for box in boxes:
                        class_id = int(box.cls[0])
                        label = self.model.names[class_id]
                        if(label == "car"):
                            car_count += 1 
                        elif(label == "truck"):
                            truck_count += 1
                        elif(label == "bus"):
                            bus_count += 1
                        elif(label == "motorcycle"):
                            motorcycle_count += 1

        car_count = car_count / FRAME_SAMPLE
        truck_count = truck_count / FRAME_SAMPLE
        bus_count = bus_count / FRAME_SAMPLE
        motorcycle_count = motorcycle_count / FRAME_SAMPLE

        vehicle_count = int(car_count + truck_count + bus_count + motorcycle_count)
        phase.setVehicleCount(vehicle_count)

        PCU = car_count + (truck_count*3) + (bus_count*3) + (motorcycle_count*0.75)
        l = 2
        hc = 2
        estimation = int(l + (PCU*hc))

        final_time = max(min(self.MAX_GREEN_TIME, estimation), self.MIN_GREEN_TIME)
        phase.setProposed_time(final_time)

        # ✅ INTEGRATION: Send real-time data to Dashboard via FastAPI
        try:
            requests.post(f"{SERVER_URL}/update-status", json={
                "lane_id": phase_index,
                "timer": phase.getLock_time(), # Current countdown
                "density": int((final_time / self.MAX_GREEN_TIME) * 100), # Visual density %
                "state": phase.getState(), # "GREEN" or "RED"
                "is_emergency": phase_index in self.Emergency_Detected
            }, timeout=0.1)
        except:
            pass # Server might be offline
        
    def detect_accident(self, phase_index, frame):
        result = self.accident_model(frame)
        # Check if classification or detection results exist
        if not result or result[0].probs is None:
            return

        probs = result[0].probs
        confidence = probs.top1conf

        if(confidence > 0.8):
            self.Accident_Detected.add(phase_index)

            if phase_index not in self.sent_accident:
                self.sent_accident.add(phase_index)
                try:
                    requests.post(f"{SERVER_URL}/process-event", json={
                        "square_code": SQUARE_CODE,
                        "lane_id": str(phase_index),
                        "city": CITY,
                        "event_type": "ACCIDENT",
                        "timestamp": time.strftime("%H:%M:%S")
                    })
                except:
                    pass
        else:
            if phase_index in self.sent_accident:
                self.sent_accident.discard(phase_index)

    def detect_emergency(self, phase_index, frame):
        result = self.ambulance_model(frame)
        if not result or result[0].probs is None:
            return

        probs = result[0].probs
        confidence = probs.top1conf

        if(confidence > 0.8):
            self.Emergency_Detected.add(phase_index)

            if phase_index not in self.sent_emergency:
                self.sent_emergency.add(phase_index)
                try:
                    requests.post(f"{SERVER_URL}/process-event", json={
                        "square_code": SQUARE_CODE,
                        "lane_id": str(phase_index),
                        "city": CITY,
                        "event_type": "AMB_START"
                    })
                except:
                    pass
        else:
            if phase_index in self.sent_emergency:
                self.sent_emergency.discard(phase_index)

    def getEmergency_Detected(self):
        return len(self.Emergency_Detected) > 0

    def getEmergency_Lane(self):
        return list(self.Emergency_Detected)

    def setEmergency(self, detected, phase_index):
        if detected:
            self.Emergency_Detected.add(phase_index)
        else:
            self.Emergency_Detected.discard(phase_index)
    
    def getAccident_Detected(self):
        return len(self.Accident_Detected) > 0
    
    def getAccident_Lane(self):
        return list(self.Accident_Detected)
    
    def setAccident(self, detected, phase_index):
        if detected:
            self.Accident_Detected.add(phase_index)
        else:
            self.Accident_Detected.discard(phase_index)