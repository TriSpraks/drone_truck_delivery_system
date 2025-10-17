# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import time
import json

from .utils import db_handler
from .matrix.distance import compute_distances
from .matrix.matrix import generate_vehicle_matrix
from .matrix.vehicle import create_fleet_vehicles, FuelTruck, ElectricTruck, Drone
from .solver.initial_solution import build_initial_solution
from .solution.solution import generate_solution

# ----------------- Lifespan -----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Backend initializing...")
    await db_handler.init_db()
    print("Backend ready - database initialized")
    try:
        yield
    finally:
        print("Backend shutting down...")
        await db_handler.close_client()

# ----------------- App Setup -----------------
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- API Endpoints -----------------
@app.get("/api/config")
async def get_config():
    """Return configuration for frontend"""
    config_data = {
        "DEFAULT_DEPOT_COORDS": [12.8500, 74.9200],
        "DEFAULT_CUSTOMER_COUNT": 5,
        "MAP_CENTER": [20.5937, 78.9629],
        "MAP_ZOOM": 5,
        "DEFAULT_FLEET_CONFIG": {"electric_trucks": 2, "fuel_trucks": 1, "drones": 3},
        "VEHICLE_SPEEDS": {"Drone": 60, "Electric Truck": 40, "Fuel Truck": 35},
        "VEHICLE_WEIGHTS": {"Drone": [1, 5], "Electric Truck": [200, 500], "Fuel Truck": [300, 700]},
    }
    nodes = await db_handler.get_nodes()
    config_data["nodes_count"] = len(nodes)
    return config_data

@app.post("/api/nodes/insert")
async def insert_nodes(request: dict):
    """
    Insert nodes and vehicle data, then trigger backend computations
    """
    start_time = time.time()
    nodes = request.get("nodes", [])
    vehicle_config = request.get("vehicle_config", {})

    if not nodes:
        raise HTTPException(status_code=400, detail="No nodes provided")

    print(f"Inserting {len(nodes)} nodes to database...")
    print(f"Vehicle config received: {vehicle_config}")

    # Clear existing tables
    clear_start = time.time()
    await db_handler.clear_generated_nodes()
    await db_handler.clear_vehicle_matrix()
    await db_handler.clear_vehicles()
    clear_time = time.time() - clear_start

    # Insert nodes
    node_insert_start = time.time()
    await db_handler.insert_nodes_bulk(nodes)
    current_nodes = await db_handler.get_nodes()
    if len(current_nodes) != len(nodes):
        raise HTTPException(status_code=500, detail="Node insertion verification failed")
    node_insert_time = time.time() - node_insert_start

    # Insert vehicles
    vehicle_insert_start = time.time()
    vehicles = create_fleet_vehicles(vehicle_config)
    vehicle_records = []
    for v in vehicles:
        if isinstance(v, FuelTruck):
            range_km = 10000.0
        elif isinstance(v, ElectricTruck):
            range_km = v.RANGE_KM
        elif isinstance(v, Drone):
            range_km = v.MAX_RANGE_KM
        else:
            range_km = 0.0
        vehicle_records.append({
            "vehicle_id": v.id,
            "capacity_kg": v.capacity_kg,
            "capacity_cm3": v.capacity_cm3 or 0.0,
            "speed_kmph": v.speed_kmph,
            "range_km": range_km,
        })
    await db_handler.insert_vehicles_bulk(vehicle_records)
    vehicle_insert_time = time.time() - vehicle_insert_start

    # Compute distances
    distance_compute_start = time.time()
    dist_rows = await compute_distances(current_nodes)
    matrix_entries = []
    for row in dist_rows:
        origin_id, dest_id, truck_km, truck_dur, drone_km, drone_dur = row
        if truck_km is not None and truck_dur is not None:
            matrix_entries.append([origin_id, dest_id, "truck", truck_km, truck_dur, 0.0])
        if drone_km is not None and drone_dur is not None:
            matrix_entries.append([origin_id, dest_id, "drone", drone_km, drone_dur, 0.0])
    await db_handler.insert_vehicle_matrix_bulk(matrix_entries)
    distance_compute_time = time.time() - distance_compute_start

    # Generate vehicle matrix
    vehicle_matrix_start = time.time()
    await generate_vehicle_matrix(current_nodes, dist_rows, vehicle_config)
    final_count = len(await db_handler.get_vehicle_matrix())
    vehicle_matrix_time = time.time() - vehicle_matrix_start
 
    # Build initial solution
    initial_solution = await build_initial_solution()

    with open("backend/initial_solution.json", "w") as f:
        json.dump(initial_solution, f, indent=2)

    print("Initial solution generated:")
    print(initial_solution)

    # Trigger the solution generator
    solution_data = await generate_solution()

    # Save to solution.json
    with open("backend/solution.json", "w") as f:
        json.dump(solution_data, f, indent=4)

    print("Optimized solution saved to solution.json")
    print(solution_data)


    total_time = time.time() - start_time
    print(f"✅ Total backend processing completed in {total_time:.2f}s")

    return {
        "status": "success",
        "message": "Nodes and vehicle data processed, computations completed",
        "nodes_inserted": len(nodes),
        "vehicle_config": vehicle_config,
        "vehicles_inserted": len(vehicle_records),
        "distance_entries": len(matrix_entries),
        "vehicle_matrix_entries": final_count,
        "timing": {
            "table_clearing": round(clear_time, 2),
            "node_insertion": round(node_insert_time, 2),
            "vehicle_insertion": round(vehicle_insert_time, 2),
            "distance_computation": round(distance_compute_time, 2),
            "vehicle_matrix_generation": round(vehicle_matrix_time, 2),
            "total_time": round(total_time, 2)
        }
    }

@app.post("/api/compute/distances")
async def compute_distances_endpoint():
    """Compute distances for existing nodes"""
    try:
        current_nodes = await db_handler.get_nodes()
        if not current_nodes:
            raise HTTPException(status_code=400, detail="No nodes found")
        dist_rows = await compute_distances(current_nodes)

        await db_handler.clear_vehicle_matrix()
        matrix_entries = []
        for row in dist_rows:
            origin_id, dest_id, truck_km, truck_dur, drone_km, drone_dur = row
            if truck_km is not None and truck_dur is not None:
                matrix_entries.append([origin_id, dest_id, "truck", truck_km, truck_dur, 0.0])
            if drone_km is not None and drone_dur is not None:
                matrix_entries.append([origin_id, dest_id, "drone", drone_km, drone_dur, 0.0])
        await db_handler.insert_vehicle_matrix_bulk(matrix_entries)
        return {"status": "success", "entries": len(matrix_entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compute/vehicle_matrix")
async def compute_vehicle_matrix_endpoint():
    """Generate vehicle matrix for existing nodes and distances"""
    try:
        current_nodes = await db_handler.get_nodes()
        if not current_nodes:
            raise HTTPException(status_code=400, detail="No nodes found")

        vehicle_matrix_data = await db_handler.get_vehicle_matrix()
        if not vehicle_matrix_data:
            raise HTTPException(status_code=400, detail="No distance data found")

        # Reconstruct dist_rows for vehicle matrix
        dist_rows = []
        for row in vehicle_matrix_data:
            dist_rows.append([
                row["origin_id"], row["dest_id"],
                row["distance"] if row["vehicle_type"] == "truck" else None,
                row["duration"] if row["vehicle_type"] == "truck" else None,
                row["distance"] if row["vehicle_type"] == "drone" else None,
                row["duration"] if row["vehicle_type"] == "drone" else None
            ])

        await generate_vehicle_matrix(current_nodes, dist_rows)
        final_count = len(await db_handler.get_vehicle_matrix())
        return {"status": "success", "entries": final_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/initial_solution")
async def api_initial_solution():
    p = Path(__file__).parent / "initial_solution.json"
    if not p.exists():
        return JSONResponse({"error": "initial_solution.json not found"}, status_code=404)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        return JSONResponse({"error": "failed to read initial_solution.json", "detail": str(e)}, status_code=500)

@app.get("/api/nodes")
async def api_nodes():
    # uses your existing async db handler
    try:
        nodes = await db_handler.get_nodes()
        return nodes
    except Exception as e:
        return JSONResponse({"error": "failed to fetch nodes", "detail": str(e)}, status_code=500)

@app.post("/api/generate_initial_solution")
async def generate_initial_solution_endpoint():
    """Generate the initial solution"""
    try:
        initial_solution_data = await build_initial_solution()

        # Save to initial_solution.json
        with open("initial_solution.json", "w") as f:
            json.dump(initial_solution_data, f, indent=2)

        print("Initial solution generated:")
        print(initial_solution_data)

        return initial_solution_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_solution")
async def generate_solution_endpoint():
    """Generate the optimized solution using ALNS"""
    try:
        solution_data = await generate_solution()

        # Save to solution.json
        with open("solution.json", "w") as f:
            json.dump(solution_data, f, indent=4)

        print("Optimized solution saved to solution.json")
        print(solution_data)

        return solution_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/solution")
async def api_solution():
    p = Path(__file__).parent / "solution.json"
    if not p.exists():
        return JSONResponse({"error": "solution.json not found"}, status_code=404)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        return JSONResponse({"error": "failed to read solution.json", "detail": str(e)}, status_code=500)
# ----------------- Run -----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
