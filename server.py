from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import math
import json
from datetime import datetime

app = FastAPI()

# ✅ FIX: Allow your browser to talk to the server (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows local HTML files to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ WEBSOCKET MANAGER ------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # ✅ FIX: Explicitly accept the connection
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass 

manager = ConnectionManager()

# ------------------ DATABASE ------------------
squares_db = {}             
emergency_registry = {}     

# ------------------ MODELS ------------------
class SquareSetup(BaseModel):
    city: str
    hq_contact_number: str
    square_name: str
    square_code: str
    lat: float
    lon: float
    lane_ids: List[str]

class EventPayload(BaseModel):
    square_code: str
    lane_id: str
    city: str
    event_type: str 

class TrafficUpdate(BaseModel):
    lane_id: int
    timer: int
    state: str       
    density: int     
    is_emergency: Optional[bool] = False

# ------------------ UTILITY ------------------
def get_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# ------------------ WEBSOCKET ------------------
@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ------------------ ENDPOINTS ------------------

@app.post("/register-square")
async def register(config: SquareSetup):
    # Use model_dump for Pydantic V2 compatibility
    squares_db[config.square_code] = config.model_dump()
    return {"status": "Square Configured", "hq": config.hq_contact_number}

@app.post("/update-status")
async def update_status(data: TrafficUpdate):
    await manager.broadcast({
        "event": "TRAFFIC_UPDATE",
        "lane_id": data.lane_id,
        "timer": data.timer,
        "state": data.state,
        "density": data.density,
        "is_emergency": data.is_emergency
    })
    return {"status": "Broadcasted"}

@app.post("/process-event")
async def process_event(data: EventPayload):
    current_sq = squares_db.get(data.square_code)
    if not current_sq:
        raise HTTPException(status_code=404, detail="Square not found")

    if data.event_type == "ACCIDENT":
        await manager.broadcast({
            "event": "ACCIDENT_DETECTED",
            "message": "Alert sent to HQ",
            "details": f"Lane: {data.lane_id}",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        return {"status": "Alert Dispatched"}

    if data.event_type == "AMB_START":
        affected = [code for code, info in squares_db.items() if code != data.square_code]
        await manager.broadcast({"event": "EMERGENCY_MODE_ON", "squares": affected})
        return {"status": "Green Corridor Active"}

    return {"status": "Processed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)