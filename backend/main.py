from utils import (
    init_db, close_client, clear_nodes,
    get_nodes, get_vehicle_matrix
)
from frontend import generate_and_store
from backend import compute_distances, generate_vehicle_matrix
import time
from fastapi import FastAPI
from contextlib import asynccontextmanager


# --- Lifespan for startup & shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        total_start = time.perf_counter()

        print("Initializing database...")
        t0 = time.perf_counter()
        await init_db()
        print(f"Database initialized in {time.perf_counter() - t0:.2f} sec")

        print("Generating nodes...")
        t0 = time.perf_counter()
        nodes = await generate_and_store()
        print(f"Nodes generated in {time.perf_counter() - t0:.2f} sec")

        print("Computing distances...")
        t0 = time.perf_counter()
        dist_rows = await compute_distances(nodes)
        print(f"Distances computed in {time.perf_counter() - t0:.2f} sec")

        print("Generating vehicle matrix...")
        t0 = time.perf_counter()
        await generate_vehicle_matrix(nodes, dist_rows)
        print(f"Vehicle matrix generated in {time.perf_counter() - t0:.2f} sec")

        total_time = time.perf_counter() - total_start
        print(f"Startup flow completed in {total_time:.2f} sec")

        yield
    finally:
        print("Closing DB client...")
        t0 = time.perf_counter()
        await close_client()
        print(f"DB client closed in {time.perf_counter() - t0:.2f} sec")
        print("Shutdown completed.")


# --- FastAPI app with lifespan ---
app = FastAPI(title="Vehicle Routing Project", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Vehicle Routing API is running"}


@app.get("/nodes")
async def nodes_endpoint():
    return {"nodes": await get_nodes()}


@app.get("/vehicle_matrix")
async def vehicle_matrix_endpoint():
    return {"vehicle_matrix": await get_vehicle_matrix()}


@app.post("/regenerate")
async def regenerate_data():
    total_start = time.perf_counter()

    # 🧹 Step 1: Clear old data
    print("Clearing old data...")
    t0 = time.perf_counter()
    await clear_nodes()
    print(f"Old data cleared in {time.perf_counter() - t0:.2f} sec")

    # 🔄 Step 2: Generate fresh nodes
    print("Regenerating nodes...")
    t0 = time.perf_counter()
    nodes = await generate_and_store()
    print(f"Nodes regenerated in {time.perf_counter() - t0:.2f} sec")

    # 🔄 Step 3: Recompute distances
    print("Recomputing distances...")
    t0 = time.perf_counter()
    dist_rows = await compute_distances(nodes)
    print(f"Distances recomputed in {time.perf_counter() - t0:.2f} sec")

    # 🔄 Step 4: Regenerate vehicle matrix
    print("Regenerating vehicle matrix...")
    t0 = time.perf_counter()
    await generate_vehicle_matrix(nodes, dist_rows)
    print(f"Vehicle matrix regenerated in {time.perf_counter() - t0:.2f} sec")

    total_time = time.perf_counter() - total_start
    print(f"🔄 Data regeneration completed in {total_time:.2f} sec")

    return {
        "status": "Data regenerated successfully",
        "execution_time_sec": round(total_time, 2),
    }
