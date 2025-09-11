from utils import (
    init_db, close_client, clear_nodes,
    get_nodes, get_vehicle_matrix
)
from frontend import generate_and_store
from matrix import compute_distances, generate_vehicle_matrix
import time
from fastapi import FastAPI
from contextlib import asynccontextmanager


# --- Lifespan for startup & shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function manages the startup and shutdown lifecycle of the FastAPI app.
    It runs initialization tasks when the app starts and cleanup tasks when it shuts down.
    """
    try:
        total_start = time.perf_counter()  # Measure total startup time

        # Step 1: Initialize the database connection
        print("Initializing database...")
        t0 = time.perf_counter()
        await init_db()
        print(f"Database initialized in {time.perf_counter() - t0:.2f} sec")

        # Step 2: Generate nodes (data points, e.g., delivery locations)
        print("Generating nodes...")
        t0 = time.perf_counter()
        nodes = await generate_and_store()
        print(f"Nodes generated in {time.perf_counter() - t0:.2f} sec")

        # Step 3: Compute distances between nodes (distance matrix)
        print("Computing distances...")
        t0 = time.perf_counter()
        dist_rows = await compute_distances(nodes)
        print(f"Distances computed in {time.perf_counter() - t0:.2f} sec")

        # Step 4: Generate the vehicle matrix (vehicles assigned to nodes/distances)
        print("Generating vehicle matrix...")
        t0 = time.perf_counter()
        await generate_vehicle_matrix(nodes, dist_rows)
        print(f"Vehicle matrix generated in {time.perf_counter() - t0:.2f} sec")

        total_time = time.perf_counter() - total_start
        print(f"Startup flow completed in {total_time:.2f} sec")

        # Yield control back to FastAPI after startup is done
        yield

    finally:
        # Cleanup tasks when app shuts down
        print("Closing DB client...")
        t0 = time.perf_counter()
        await close_client()  # Close database connection
        print(f"DB client closed in {time.perf_counter() - t0:.2f} sec")
        print("Shutdown completed.")


# --- FastAPI app with custom startup/shutdown (lifespan) ---
app = FastAPI(title="Vehicle Routing Project", lifespan=lifespan)


# --- Root endpoint ---
@app.get("/")
async def root():
    """Simple health check endpoint to verify API is running."""
    return {"message": "Vehicle Routing API is running"}


# --- Endpoint to fetch stored nodes ---
@app.get("/nodes")
async def nodes_endpoint():
    """Returns all generated nodes from the database."""
    return {"nodes": await get_nodes()}


# --- Endpoint to fetch vehicle distance matrix ---
@app.get("/vehicle_matrix")
async def vehicle_matrix_endpoint():
    """Returns the vehicle matrix (distances/assignments)."""
    return {"vehicle_matrix": await get_vehicle_matrix()}


# --- Endpoint to regenerate all data (clear + rebuild) ---
@app.post("/regenerate")
async def regenerate_data():
    """
    Clears old nodes, generates fresh nodes, recomputes distances,
    and regenerates the vehicle matrix.
    Useful for refreshing data without restarting the app.
    """
    total_start = time.perf_counter()

    # Step 1: Clear existing data
    print("Clearing old data...")
    t0 = time.perf_counter()
    await clear_nodes()
    print(f"Old data cleared in {time.perf_counter() - t0:.2f} sec")

    # Step 2: Generate fresh nodes
    print("Regenerating nodes...")
    t0 = time.perf_counter()
    nodes = await generate_and_store()
    print(f"Nodes regenerated in {time.perf_counter() - t0:.2f} sec")

    # Step 3: Recompute distances for the new nodes
    print("Recomputing distances...")
    t0 = time.perf_counter()
    dist_rows = await compute_distances(nodes)
    print(f"Distances recomputed in {time.perf_counter() - t0:.2f} sec")

    # Step 4: Regenerate vehicle matrix
    print("Regenerating vehicle matrix...")
    t0 = time.perf_counter()
    await generate_vehicle_matrix(nodes, dist_rows)
    print(f"Vehicle matrix regenerated in {time.perf_counter() - t0:.2f} sec")

    total_time = time.perf_counter() - total_start
    print(f"Data regeneration completed in {total_time:.2f} sec")

    return {
        "status": "Data regenerated successfully",
        "execution_time_sec": round(total_time, 2),
    }
