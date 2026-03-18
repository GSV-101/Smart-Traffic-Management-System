import cv2, threading, time

class VideoThread(threading.Thread):
    def __init__(self, thread_name, phase):
        threading.Thread.__init__(self, name=thread_name)

        self.phase = phase
        self.video = phase.video # Assuming phase.video is a cv2.VideoCapture object
        self.is_running = True

        # Getting video FPS
        fps = self.video.get(cv2.CAP_PROP_FPS)

        # Time required for one frame
        self.frame_delay = 1 / fps if fps > 0 else 0.03
    
    def run(self):
        while(self.is_running):
            start = time.time()

            success, frame = self.video.read()

            if(not success):
                # Restart if there is no success / frame i.e. video is ended
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0) 
                success, frame = self.video.read()

                if(not success): # Unable to read video frame
                    break # Exit loop instead of just return to allow cleanup
            
            # ✅ INTEGRATION: Ensure the frame is resized for YOLO efficiency 
            # (YOLOv8 usually expects 640x640, resizing here saves CPU/GPU time later)
            # frame = cv2.resize(frame, (640, 480)) 

            self.phase.setFrame(frame) # Saving latest frame in phase

            # Maintaining FPS timing
            elapsed = time.time() - start
            sleep_time = self.frame_delay - elapsed

            if(sleep_time > 0):
                time.sleep(sleep_time)
        
        # ✅ INTEGRATION: Resource Cleanup
        # This is vital to prevent memory leaks and file locking
        if self.video.isOpened():
            self.video.release()

    def stop(self):
        self.is_running = False
    
    def begin(self):
        self.is_running = True