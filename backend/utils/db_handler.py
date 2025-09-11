import asyncio
from libsql_client import create_client
from . import config

# Global database client (singleton)
_client = None

# Default batch size for inserting nodes
DB_BATCH_SIZE = 50  

# ----------------- Client Management -----------------
def get_client():
    """
    Get or create a global LibSQL client.
    Lazy initialization: client is created only when first needed.
    """
    global _client
    if _client is None:
        _client = create_client(
            url=config.DB_URL,
            auth_token=getattr(config, "DB_AUTH_TOKEN", None),
        )
    return _client

async def close_client():
    """Close the global client connection and reset it to None."""
    global _client
    if _client:
        await _client.close()
        _client = None

# ----------------- Initialization -----------------
async def init_db():
    """
    Initialize database tables:
    - generated_nodes: stores delivery nodes
    - vehicle_matrix: stores distance, duration, total_cost per vehicle
    """
    client = get_client()
    try:
        await client.execute("""
            CREATE TABLE IF NOT EXISTS generated_nodes (
                id INTEGER PRIMARY KEY,
                node_id TEXT UNIQUE,
                weight REAL,
                volume REAL,
                lon REAL,
                lat REAL,
                elevation REAL
            )
        """)

        await client.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_matrix (
                id INTEGER PRIMARY KEY,
                origin_id TEXT,
                dest_id TEXT,
                vehicle_type TEXT,
                distance REAL,
                duration REAL,
                total_cost REAL
            )
        """)

        # Create unique index to prevent duplicate vehicle_matrix entries
        try:
            await client.execute("""
                CREATE UNIQUE INDEX vehicle_matrix_unique_idx
                ON vehicle_matrix(origin_id, dest_id, vehicle_type)
            """)
        except Exception:
            pass  # index already exists

        print("Database initialized successfully.")
    except Exception as e:
        print("Error initializing DB:", e)
        raise

# ----------------- Clearing -----------------
async def clear_nodes():
    """Clear all data from generated_nodes and vehicle_matrix."""
    client = get_client()
    try:
        await client.execute("DELETE FROM vehicle_matrix;")
        await client.execute("DELETE FROM generated_nodes;")
    except Exception as e:
        print("Error clearing tables:", e)
        raise

# ----------------- Inserts -----------------
async def insert_nodes_bulk(nodes):
    """
    Insert multiple nodes in batches.
    Each node must include: node_id, weight, volume, lon, lat, elevation.
    """
    client = get_client()
    query = """
        INSERT INTO generated_nodes (node_id, weight, volume, lon, lat, elevation)
        VALUES ($1, $2, $3, $4, $5, $6)
    """
    for i in range(0, len(nodes), DB_BATCH_SIZE):
        batch = nodes[i:i + DB_BATCH_SIZE]
        await asyncio.gather(*[
            client.execute(query, [
                n["node_id"], n["weight"], n["volume"],
                n["lon"], n["lat"], n["elevation"]
            ]) for n in batch
        ])

async def insert_vehicle_matrix_bulk(matrix_list, batch_size=500):
    """
    Insert vehicle_matrix entries in bulk.
    Each row should be: [origin_id, dest_id, vehicle_type, distance, duration, total_cost]
    """
    client = get_client()
    if not matrix_list:
        return

    for i in range(0, len(matrix_list), batch_size):
        batch = matrix_list[i:i + batch_size]
        values = []
        params = []
        for j, row in enumerate(batch):
            offset = j * 6
            values.append(f"($${offset+1}, $${offset+2}, $${offset+3}, $${offset+4}, $${offset+5}, $${offset+6})")
            params.extend(row)

        query = f"""
            INSERT INTO vehicle_matrix
            (origin_id, dest_id, vehicle_type, distance, duration, total_cost)
            VALUES {", ".join(values)}
            ON CONFLICT(origin_id, dest_id, vehicle_type) DO NOTHING
        """
        try:
            await client.execute(query, params)
        except Exception as e:
            print(f"[Bulk Insert Error] Batch starting at {i} | Error: {e}")

# ----------------- Queries -----------------
async def get_nodes():
    """
    Fetch all generated nodes from the database.
    Returns a list of dictionaries with node details.
    """
    client = get_client()
    rows = await client.execute("SELECT * FROM generated_nodes;")
    return [
        {
            "id": r[0],
            "node_id": r[1],
            "weight": r[2],
            "volume": r[3],
            "lon": r[4],
            "lat": r[5],
            "elevation": r[6],
        }
        for r in rows
    ]

async def get_vehicle_matrix():
    """
    Fetch all vehicle_matrix entries from the database.
    Returns a list of dictionaries with distance, duration, and total_cost.
    """
    client = get_client()
    rows = await client.execute("SELECT * FROM vehicle_matrix;")
    return [
        {
            "id": r[0],
            "origin_id": r[1],
            "dest_id": r[2],
            "vehicle_type": r[3],
            "distance": r[4],
            "duration": r[5],
            "total_cost": r[6],
        }
        for r in rows
    ]
