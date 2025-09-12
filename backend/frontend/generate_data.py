# frontend/generate_data.py
import random
from utils import config, db_handler

# Batch size for DB inserts (to avoid inserting all rows at once)
DB_BATCH_SIZE = 50  


# ----------------- Node Generation -----------------
def generate_nodes():
    """
    Generate a list of nodes for the VRP (Vehicle Routing Problem).
    
    Nodes include:
    - 1 depot (starting/ending point for vehicles).
    - Multiple customers with random demand (weight & volume) 
      and random geographic coordinates.

    Returns:
        List[dict]: Each node is a dictionary with attributes.
    """
    nodes = []

    # --- Depot (central hub, demand = 0) ---
    nodes.append({
        "node_id": "depot",             # Unique ID
        "type": "depot",                # Node type (used in routing logic)
        "weight": 0,                    # Depot has no demand
        "volume": 0,                    # Depot has no demand
        "lon": config.DEPOT_COORDS[0],  # Longitude from config
        "lat": config.DEPOT_COORDS[1],  # Latitude from config
        "elevation": getattr(config, "DEPOT_ELEV", 20),  # Elevation (default=20)
    })

    # --- Customers (delivery points) ---
    for i in range(1, config.NUM_CUSTOMERS + 1):
        # Random demand with Gaussian distribution (ensures realism)
        weight = max(0.1, random.gauss(config.WEIGHT_MEAN, config.WEIGHT_STDDEV))
        volume = max(1, random.gauss(config.VOLUME_MEAN, config.VOLUME_STDDEV))

        # Random geographic coordinates within bounding box
        lon = round(random.uniform(*config.LON_RANGE), 6)
        lat = round(random.uniform(*config.LAT_RANGE), 6)

        # Random elevation (e.g., terrain data)
        elevation = random.randint(*config.ELEV_RANGE)

        nodes.append({
            "node_id": f"cust_{i}",      # Unique ID (cust_1, cust_2, ...)
            "type": "customer",          # Node type
            "weight": round(weight, 2),  # Rounded demand weight
            "volume": round(volume, 0),  # Rounded demand volume
            "lon": lon,                  # Longitude
            "lat": lat,                  # Latitude
            "elevation": elevation,      # Elevation (integer)
        })

    return nodes


# ----------------- Node Generation + Storage -----------------
async def generate_and_store():
    """
    Generate nodes (depot + customers), clear old DB data, 
    and insert new nodes into the database asynchronously.

    Workflow:
    1. Generate fresh nodes.
    2. Clear old nodes and vehicle_matrix from DB.
    3. Insert new nodes in batches (for efficiency).
    4. Return the generated nodes for further processing.
    """
    # Step 1: Generate new node data
    nodes = generate_nodes()

    # Step 2: Clear old DB data
    await db_handler.clear_nodes()

    # Step 3: Insert nodes in batches
    for i in range(0, len(nodes), DB_BATCH_SIZE):
        batch = nodes[i:i + DB_BATCH_SIZE]
        await db_handler.insert_nodes_bulk(batch)

    # Log and return
    print(f"Frontend: {len(nodes)} nodes inserted into DB.")
    return nodes