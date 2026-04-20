import asyncio
import random
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ==========================================
# Global State
# ==========================================
global_state: Dict[str, Any] = {
    "stadium_info": {
        "total_people": 42500,
        "capacity": 55000,
    },
    "live_score": {
        "home_team": "Eagles",
        "home_score": 2,
        "away_team": "Falcons",
        "away_score": 1,
        "period": "3rd Qtr",
        "time_remaining": "04:12"
    },
    "gates": {
        "Gate 1": {"density_percent": 0, "headcount": 0, "staff": 0, "throughput": 0},
        "Gate 2": {"density_percent": 0, "headcount": 0, "staff": 0, "throughput": 0},
        "Gate 3": {"density_percent": 0, "headcount": 0, "staff": 0, "throughput": 0},
        "Gate 4": {"density_percent": 0, "headcount": 0, "staff": 0, "throughput": 0}
    },
    "wait_times": {
        "Washrooms (North Wing)": {"minutes": 0, "in_line": 0, "status": "Clear"},
        "Washrooms (South Wing)": {"minutes": 0, "in_line": 0, "status": "Clear"},
        "Snacks & Beverage": {"minutes": 0, "in_line": 0, "status": "Clear"},
        "Seating Area A Entry": {"minutes": 0, "in_line": 0, "status": "Clear"},
        "Seating Area B Entry": {"minutes": 0, "in_line": 0, "status": "Clear"}
    },
    "recommended_exit": "Gate 1"
}

def determine_best_exit(gates_data: Dict[str, dict]) -> str:
    # Find the gate key with the lowest density percent
    best_gate = min(gates_data, key=lambda k: gates_data[k]["density_percent"])
    return best_gate

async def simulation_engine():
    """
    Background task that simulates live fluctuating crowd data.
    """
    while True:
        # Fluctuate total people slightly
        fluctuation = random.randint(-150, 150)
        global_state["stadium_info"]["total_people"] += fluctuation
        
        # Keep total people within realistic bounds
        if global_state["stadium_info"]["total_people"] > 55000:
            global_state["stadium_info"]["total_people"] = 55000
        elif global_state["stadium_info"]["total_people"] < 10000:
            global_state["stadium_info"]["total_people"] = 10000

        # Simulate Score occasionally (10% chance to change time/score roughly)
        if random.random() < 0.2:
            seconds = random.randint(10, 59)
            global_state["live_score"]["time_remaining"] = f"0{random.randint(0,4)}:{seconds}"

        # Gates Simulation
        for gate in global_state["gates"]:
            density = random.randint(15, 95)
            global_state["gates"][gate] = {
                "density_percent": density,
                "headcount": int(density * 18.5) + random.randint(0, 50),
                "staff": random.randint(3, 8),
                "throughput": random.randint(20, 150)  # people per minute
            }
        
        # Wait Times Simulation
        for area in global_state["wait_times"]:
            wait = random.randint(0, 30)
            status = "Busy" if wait > 20 else ("Moderate" if wait > 10 else "Clear")
            global_state["wait_times"][area] = {
                "minutes": wait,
                "in_line": wait * random.randint(2, 6),
                "status": status
            }
            
        # Update recommended exit based on density
        global_state["recommended_exit"] = determine_best_exit(global_state["gates"])
        
        await asyncio.sleep(3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    sim_task = asyncio.create_task(simulation_engine())
    yield
    sim_task.cancel()

app = FastAPI(title="Smart Stadium Crowd Management", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static directory for images
app.mount("/static", StaticFiles(directory="backimg"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

@app.get("/api/status")
async def get_status():
    return global_state
