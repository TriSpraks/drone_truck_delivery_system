import asyncio
from libsql_client import create_client
from . import config

_client = None
DB_BATCH_SIZE = 50  # Default batch size for inserts


# ----------------- Client Management -----------------
def get_client():
    """Get or create a LibSQL client."""
    global _client
    if _client is None:
        _client = create_client(
            url=config.DB_URL,
            auth_token=getattr(config, "DB_AUTH_TOKEN", None),
        )
    return _client


async def close_client():
    """Close the client connection."""
    global _client
    if _client:
        await _client.close()
        _client = None


# ----------------- Initialization -----------------
async def init_db():
    """Create required tables if they do not exist."""
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
                total_cost REAL
            )
        """)

        try:
            await client.execute("""
                CREATE UNIQUE INDEX vehicle_matrix_unique_idx
                ON vehicle_matrix(origin_id, dest_id, vehicle_type)
            """)
        except Exception:
            # ignore if already exists
            pass

        print("Database initialized successfully.")
    except Exception as e:
        print("Error initializing DB:", e)
        raise


# ----------------- Clearing -----------------
async def clear_nodes():
    """Clear both nodes and vehicle matrix."""
    client = get_client()
    try:
        await client.execute("DELETE FROM vehicle_matrix;")
        await client.execute("DELETE FROM generated_nodes;")
    except Exception as e:
        print("Error clearing tables:", e)
        raise


# ----------------- Inserts -----------------
async def insert_nodes_bulk(nodes):
    """Insert nodes in async batches."""
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
    Bulk insert vehicle matrix entries efficiently.
    Each entry: [origin_id, dest_id, vehicle_type, distance, total_cost]
    """
    client = get_client()
    if not matrix_list:
        return

    for i in range(0, len(matrix_list), batch_size):
        batch = matrix_list[i:i + batch_size]

        values = []
        params = []
        for j, row in enumerate(batch):
            offset = j * 5
            values.append(
                f"($${offset+1}, $${offset+2}, $${offset+3}, $${offset+4}, $${offset+5})"
            )
            params.extend(row)

        query = f"""
            INSERT INTO vehicle_matrix
            (origin_id, dest_id, vehicle_type, distance, total_cost)
            VALUES {", ".join(values)}
            ON CONFLICT(origin_id, dest_id, vehicle_type) DO NOTHING
        """

        try:
            await client.execute(query, params)
        except Exception as e:
            print(f"[Bulk Insert Error] Batch starting at {i} | Error: {e}")


# ----------------- Queries -----------------
async def get_nodes():
    """Fetch all nodes."""
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
    """Fetch all vehicle matrix entries."""
    client = get_client()
    rows = await client.execute("SELECT * FROM vehicle_matrix;")
    return [
        {
            "id": r[0],
            "origin_id": r[1],
            "dest_id": r[2],
            "vehicle_type": r[3],
            "distance": r[4],
            "total_cost": r[5],
        }
        for r in rows
    ]
