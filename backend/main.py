# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from utils import db_handler
from matrix.distance import compute_distances
from matrix.matrix import generate_vehicle_matrix

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
    config = {
        "DEFAULT_DEPOT_COORDS": [12.8500, 74.9200],
        "DEFAULT_CUSTOMER_COUNT": 5,
        "MAP_CENTER": [20.5937, 78.9629],
        "MAP_ZOOM": 5,
        "DEFAULT_FLEET_CONFIG": {"electric_trucks": 2, "fuel_trucks": 1, "drones": 3},
        "VEHICLE_SPEEDS": {"Drone": 60, "Electric Truck": 40, "Fuel Truck": 35},
        "VEHICLE_WEIGHTS": {"Drone": [1, 5], "Electric Truck": [200, 500], "Fuel Truck": [300, 700]},
    }
    nodes = await db_handler.get_nodes()
    config["nodes_count"] = len(nodes)
    return config

@app.post("/api/nodes/insert")
async def insert_nodes(nodes: list[dict]):
    """
    MAIN ENTRY POINT: Insert nodes and trigger automatic backend computations
    """
    if not nodes:
        raise HTTPException(status_code=400, detail="No nodes provided")

    print(f"Inserting {len(nodes)} nodes to database...")

    # Step 1: Insert nodes to generated_nodes table
    await db_handler.insert_nodes_bulk(nodes)

    # Step 2: Verify insertion
    current_nodes = await db_handler.get_nodes()
    if len(current_nodes) != len(nodes):
        raise HTTPException(status_code=500, detail="Node insertion verification failed")

    print(f"{len(nodes)} nodes inserted to generated_nodes table")

    # Step 3: Backend main triggers automatic computations
    print("Backend main triggering computations...")

    # Distance computation
    print("Computing distances...")
    dist_rows = await compute_distances(current_nodes)

    # Clear and insert distance matrix
    await db_handler.clear_vehicle_matrix()
    matrix_entries = []
    for row in dist_rows:
        origin_id, dest_id, truck_km, truck_dur, drone_km, drone_dur = row
        if truck_km is not None and truck_dur is not None:
            matrix_entries.append([origin_id, dest_id, "truck", truck_km, truck_dur, 0.0])
        if drone_km is not None and drone_dur is not None:
            matrix_entries.append([origin_id, dest_id, "drone", drone_km, drone_dur, 0.0])

    await db_handler.insert_vehicle_matrix_bulk(matrix_entries)
    print(f"Distance matrix: {len(matrix_entries)} entries")

    # Vehicle matrix generation
    print("Generating vehicle matrix...")
    await generate_vehicle_matrix(current_nodes, dist_rows)

    final_count = len(await db_handler.get_vehicle_matrix())
    print(f"Vehicle matrix: {final_count} entries")

    return {
        "status": "success",
        "message": "Nodes inserted and computations completed",
        "nodes_inserted": len(nodes),
        "distance_entries": len(matrix_entries),
        "vehicle_matrix_entries": final_count
    }

# ----------------- Run -----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
