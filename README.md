# Smart-Traffic-Management-System
** 1. Overview**

An AI-driven traffic management system designed to optimize signal control dynamically using real-time video analytics and distributed coordination across multiple intersections.

The system leverages computer vision models for traffic density estimation, emergency vehicle detection, and accident identification. It integrates a centralized coordination server to enable intelligent decision-making and inter-intersection communication, forming a scalable foundation for smart city traffic systems.

**2. Objectives**

-> Reduce traffic congestion through adaptive signal timing
-> Enable priority routing for emergency vehicles
-> Detect and report accidents in real-time
-> Coordinate nearby intersections for optimized traffic flow

**3. Key Features**

3.1 Adaptive Traffic Signal Control
-> Real-time vehicle detection using YOLOv8
-> Dynamic green time allocation based on traffic density (PCU model)
-> Multi-lane, multi-phase signal management

3.2 Emergency Vehicle Prioritization
-> Ambulance detection using a fine-tuned model
-> Immediate prioritization of detected lane within the intersection
-> Emergency signal propagation to nearby intersections (≤ 1 km radius)

3.3 Accident Detection & Alerting
-> Custom-trained model for accident detection
-> Automatic alert dispatch to central authority
-> Real-time notification via server

 3.4 Distributed Coordination System
-> Central server built using FastAPI
-> Intersections communicate via REST APIs
->Emergency mode broadcast to nearby intersections

3.5 Monitoring Dashboard
-> WebSocket-based real-time updates
-> Displays emergency states and alerts
-> Prototype implementation (requires further stabilization)

**4. System Workflow**

4.1. Video Acquisition

-> Each lane is processed via a dedicated thread
-> Frames are continuously extracted from video streams

4.2. Detection Pipeline

-> Vehicle detection → Traffic density estimation
-> Ambulance detection → Emergency trigger
-> Accident detection → Alert generation

4.3. Local Decision Engine

-> Computes optimal signal timing using PCU
-> Dynamically updates phase durations

4.4. Central Communication

-> Sends events (ACCIDENT / AMB_START / AMB_STOP) to server
-> Receives emergency mode instructions

4.5. Distributed Response

-> Nearby intersections enter emergency mode
-> Source intersection prioritizes emergency lane

**5. Core Components**

5.1 Phase Management
-> Maintains signal state (RED, YELLOW, GREEN)
-> Implements locking mechanism for stable transitions
-> Stores latest frame for processing

5.2 Phase Scheduler
-> Controls signal transitions
-> Handles Normal and Emergency modes
-> Ensures continuous and adaptive operation

5.3 Detection Modules
-> YOLOv8 (base model) → Vehicle detection
-> Custom-trained model → Accident detection
-> Custom-trained model → Ambulance detection

5.4 Central Server
-> Event processing and routing
-> Geospatial filtering using Haversine formula
-> Emergency propagation to nearby intersections
-> WebSocket-based real-time communication

**6. Project Structure**
Traffic_Management_Prayatna/
│
├── Models/
│   ├── yolov8n.pt
│   ├── best_accident.pt
│   ├── best_ambulance.pt
│   └── yolov11n.pt
│
├── Phase_Folder/
│   ├── phase.py
│   ├── phase_schedular.py
│   └── VideoThread.py
│
├── Traffic_Mode/
│   ├── Normal_Mode/
│   │   └── Optimization_And_Detection/
│   │       └── normal_logic.py
│   │
│   └── Emergency_Mode/
│       └── Optimization_And_Detection/
│           └── emergency_logic.py
│
├── video/
│   ├── north.mp4
│   ├── south.mp4
│   ├── east.mp4
│   ├── west.mp4
│   ├── accident.mp4
│   └── stimulation.mp4
│
├── server.py
├── main.py
├── index.html
└── README.md

**7. Model Details**
-> Base Model: YOLOv8n
-> Custom Models:
  Accident Detection → best_accident.pt
  Ambulance Detection → best_ambulance.pt
  
**8. Training Characteristics**
-> Lightweight architecture for real-time inference
-> Optimized for low latency and multi-threaded processing
-> Designed for urban traffic scenarios

**9. Tech Stack**
-> Language: Python
-> Computer Vision: YOLOv8 (Ultralytics)
-> Backend: FastAPI
-> Concurrency: Python threading
-> Communication: REST APIs + WebSockets
-> Frontend: HTML-based dashboard , TailWing

**10. Current Limitations**

-> Dashboard requires improved synchronization and stability
-> No persistent database (in-memory storage used)
-> Network failures are not fully handled
-> Model performance depends on dataset quality and environment

**11. Future Enhancements**

-> Integration with live GPS-based ambulance tracking
-> Edge deployment (Jetson Nano / Raspberry Pi)
-> Scalable backend with database (PostgreSQL / Redis)
-> Improved monitoring dashboard (React-based UI)
-> Distributed messaging system (Kafka / RabbitMQ)
-> Model optimization (ONNX / TensorRT)

**11. Conclusion**

This project demonstrates the integration of computer vision, distributed systems, and real-time processing to build an intelligent traffic control solution. By combining adaptive signal timing with centralized coordination, the system provides a scalable and efficient approach to modern traffic management challenges.
