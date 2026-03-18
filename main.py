import cv2
import time
import requests
import threading
import os
from Phase_Folder.phase import Phase
from Phase_Folder.VideoThread import VideoThread
from Phase_Folder.phase_schedular import Phase_Schedular

# ================= CONFIGURATION =================
SERVER_URL = "http://127.0.0.1:8000"
SQUARE_CODE = "A1"
CITY = "Indore"

# Ensure these files exist in your project folder
VIDEO_SOURCES = [
    "video/north.mp4",
    "video/east.mp4",
    "video/south.mp4",
    "video/west.mp4"
]

def main():
    print(f"--- TRAFFIX COMMAND CENTER: {CITY} [{SQUARE_CODE}] ---")

    # 1. Initialize Phase Objects
    phases = []
    for i, src in enumerate(VIDEO_SOURCES):
        # Check if file exists to prevent OpenCV hanging
        if not os.path.exists(src):
            print(f"Error: Video file not found at {src}")
            continue

        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print(f"Error: Could not open video stream for Lane {i}")
            continue
        
        # Create Phase (Name, VideoCapture, LaneID)
        new_phase = Phase(f"Lane_{i}", cap, i)
        phases.append(new_phase)

    if len(phases) < 4:
        print("CRITICAL: Not all 4 lanes were initialized. Check your 'video' folder.")
        return

    # 2. Register with the Dashboard API (FIXED for 422 Errors)
    try:
        # This dictionary must match the 'SquareSetup' Pydantic model in server.py
        registration_payload = {
            "city": CITY,
            "hq_contact_number": "911-TRAFFIX",
            "square_name": "Rajwada Junction",
            "square_code": SQUARE_CODE,
            "lat": 22.7196,
            "lon": 75.8577,
            "lane_ids": [str(i) for i in range(len(phases))] # Must be strings
        }

        response = requests.post(
            f"{SERVER_URL}/register-square", 
            json=registration_payload, 
            timeout=5
        )

        if response.status_code == 200:
            print("✅ Successfully registered square with Server.")
        else:
            print(f"❌ Registration failed ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"⚠️ Server Offline: Dashboard updates will be skipped. (Error: {e})")

    # 3. Start Video Threads
    video_threads = []
    for i, phase in enumerate(phases):
        v_thread = VideoThread(f"VideoThread_{i}", phase)
        v_thread.daemon = True  # Cleanup on exit
        v_thread.start()
        video_threads.append(v_thread)
    
    print(f"✅ Started {len(video_threads)} Video Capture Threads.")

    # 4. Start the Phase Scheduler (The Master Controller)
    scheduler = Phase_Schedular("Main_Scheduler", phases)
    scheduler.daemon = True
    scheduler.start()
    
    print("🚀 AI Traffic Scheduler is now ONLINE.")
    print("System running... Press Ctrl+C to shutdown.")

    # 5. Keep the Main Thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Shutting down Traffic System ---")
        scheduler.is_running = False
        for vt in video_threads:
            vt.stop()
        print("Cleanup complete. All threads terminated.")

if __name__ == "__main__":
    main()