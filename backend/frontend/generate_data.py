# frontend/generate_data.py
import random
from utils import config, db_handler

random.seed(config.SEED)
DB_BATCH_SIZE = 50  # For batch inserts

def generate_nodes():
    """
    Generate depot + customers with random demand and coordinates.
    Returns a list of node dicts.
    """
    nodes = []

    # Depot
    nodes.append({
        "node_id": "depot",
        "weight": 0,
        "volume": 0,
        "lon": config.DEPOT_COORDS[0],
        "lat": config.DEPOT_COORDS[1],
        "elevation": getattr(config, "DEPOT_ELEV", 20),
    })

    # Customers
    for i in range(1, config.NUM_CUSTOMERS + 1):
        nodes.append({
            "node_id": f"cust_{i}",
            "weight": round(max(0.1, random.gauss(config.WEIGHT_MEAN, config.WEIGHT_STDDEV)), 2),
            "volume": round(max(1, random.gauss(config.VOLUME_MEAN, config.VOLUME_STDDEV)), 0),
            "lon": round(random.uniform(*config.LON_RANGE), 6),
            "lat": round(random.uniform(*config.LAT_RANGE), 6),
            "elevation": round(random.uniform(*config.ELEV_RANGE), 2),
        })
    return nodes


async def generate_and_store():
    """
    Generate nodes and insert into DB in batches asynchronously.
    """
    nodes = generate_nodes()
    await db_handler.clear_nodes()

    # Batch insert
    for i in range(0, len(nodes), DB_BATCH_SIZE):
        batch = nodes[i:i + DB_BATCH_SIZE]
        await db_handler.insert_nodes_bulk(batch)

    print(f"Frontend: {len(nodes)} nodes inserted into DB.")
    return nodes
