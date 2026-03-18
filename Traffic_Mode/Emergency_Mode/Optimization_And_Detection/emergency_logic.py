from ultralytics import YOLO
import requests

SERVER_URL = "http://127.0.0.1:8000"

class EmergencyMode:
    def __init__(self, phase_list):
        self.phase_list = phase_list
        self.model = YOLO("Models/yolov8n.pt")

        self.MIN_GREEN_TIME = 10 
        self.MAX_GREEN_TIME = 25

        self.Emergency_Detected = set()

    def compute_time(self, phase_index):
        phase = self.phase_list[phase_index]
        if (not phase.ready_for_computation()):
            return

        car_count = 0
        truck_count = 0
        bus_count = 0
        motorcycle_count = 0

        FRAME_SAMPLE = 3
        valid_frames = 0

        for i in range(0, FRAME_SAMPLE):
            frame = phase.getFrame()

            if(frame is None):
                continue
            
            valid_frames += 1
        
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

        if valid_frames == 0:
            return

        car_count = car_count / valid_frames
        truck_count = truck_count / valid_frames
        bus_count = bus_count / valid_frames
        motorcycle_count = motorcycle_count / valid_frames

        vehicle_count = int(car_count + truck_count + bus_count + motorcycle_count)
        phase.setVehicleCount(vehicle_count)

        PCU = car_count + (truck_count*3) + (bus_count*3) + (motorcycle_count*0.75)
        l = 2
        hc = 2
        estimation = int(l + (PCU*hc))

        final_time = max(min(self.MAX_GREEN_TIME, estimation), self.MIN_GREEN_TIME)
        phase.setProposed_time(final_time)

        # ✅ INTEGRATION: Update Dashboard with Emergency status
        try:
            requests.post(f"{SERVER_URL}/update-status", json={
                "lane_id": phase_index,
                "timer": phase.getLock_time(),
                "density": int((final_time / self.MAX_GREEN_TIME) * 100),
                "state": phase.getState(),
                "is_emergency": True # Force true because we are in EmergencyMode
            }, timeout=0.1)
        except:
            pass

    def getEmergency_Detected(self):
        return len(self.Emergency_Detected) > 0

    def getEmergency_Lane(self):
        return list(self.Emergency_Detected)

    def setEmergency(self, detected, lane):
        if detected:
            self.Emergency_Detected.add(lane)
        else:
            self.Emergency_Detected.discard(lane)