
import asyncio
from libsql_client import create_client
from utils import config

# Global async database client (singleton)
_client = None
DB_BATCH_SIZE = 50  # Batch size for inserts

# ----------------- Client Management -----------------
def get_client():
    """Get or create a global LibSQL async client."""
    global _client
    if _client is None:
        _client = create_client(
            url=config.DB_URL,
            auth_token=getattr(config, "DB_AUTH_TOKEN", None),
        )
    return _client

async def close_client():
    """Close the global client session."""
    global _client
    if _client:
        await _client.close()
        _client = None

# ----------------- Initialization -----------------
async def init_db():
    """Create tables if they do not exist."""
    client = get_client()
    try:
        # Clear and recreate tables on initialization
        await client.execute("DROP TABLE IF EXISTS generated_nodes;")
        await client.execute("DROP TABLE IF EXISTS vehicle_matrix;")

        await client.execute("""
            CREATE TABLE generated_nodes (
                id INTEGER PRIMARY KEY,
                node_id TEXT UNIQUE,
                weight REAL,
                volume REAL,
                lon REAL,
                lat REAL
            );
        """)

        await client.execute("""
            CREATE TABLE vehicle_matrix (
                id INTEGER PRIMARY KEY,
                origin_id TEXT,
                dest_id TEXT,
                vehicle_type TEXT,
                distance REAL,
                duration REAL,
                total_cost REAL
            );
        """)

        # Unique index to prevent duplicates
        try:
            await client.execute("""
                CREATE UNIQUE INDEX vehicle_matrix_unique_idx
                ON vehicle_matrix(origin_id, dest_id, vehicle_type);
            """)
        except Exception:
            pass  # index already exists

        print("Database initialized successfully (async).")
    except Exception as e:
        print("Error initializing DB:", e)
        raise

# ----------------- Clearing -----------------
async def clear_nodes():
    """Clear all data from tables."""
    client = get_client()
    try:
        await client.execute("DELETE FROM vehicle_matrix;")
        await client.execute("DELETE FROM generated_nodes;")
    except Exception as e:
        print("Error clearing tables:", e)
        raise

async def clear_vehicle_matrix():
    """Clear only vehicle matrix data."""
    client = get_client()
    try:
        await client.execute("DELETE FROM vehicle_matrix;")
    except Exception as e:
        print("Error clearing vehicle matrix:", e)
        raise

async def clear_generated_nodes():
    """Clear only generated nodes data."""
    client = get_client()
    try:
        await client.execute("DELETE FROM generated_nodes;")
    except Exception as e:
        print("Error clearing generated nodes:", e)
        raise

# ----------------- Inserts -----------------
async def insert_nodes_bulk(nodes):
    """Insert multiple nodes in batches."""
    client = get_client()
    query = """
        INSERT OR IGNORE INTO generated_nodes (node_id, weight, volume, lon, lat)
        VALUES (?, ?, ?, ?, ?)
    """

    inserted_count = 0
    for i in range(0, len(nodes), DB_BATCH_SIZE):
        batch = nodes[i:i + DB_BATCH_SIZE]
        for node in batch:
            try:
                await client.execute(query, [node["node_id"], node["weight"], node["volume"], node["lon"], node["lat"]])
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting node {node['node_id']}: {e}")
                # Continue with other nodes

    print(f"Inserted {inserted_count} nodes out of {len(nodes)}")

async def insert_vehicle_matrix_bulk(matrix_list, batch_size=500):
    """Insert vehicle_matrix entries in bulk."""
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
            ON CONFLICT(origin_id, dest_id, vehicle_type) DO NOTHING;
        """
        try:
            await client.execute(query, params)
        except Exception as e:
            print(f"[Bulk Insert Error] Batch starting at {i} | Error: {e}")

# ----------------- Queries -----------------
async def get_nodes():
    """Fetch all generated nodes."""
    client = get_client()
    result = await client.execute("SELECT * FROM generated_nodes;")
    # Handle different response formats
    if isinstance(result, dict):
        rows = result.get("rows", [])
    else:
        rows = result
    return [
        {
            "id": r[0],
            "node_id": r[1],
            "weight": r[2],
            "volume": r[3],
            "lon": r[4],
            "lat": r[5],
        }
        for r in rows
    ]

async def get_vehicle_matrix():
    """Fetch all vehicle matrix entries."""
    client = get_client()
    result = await client.execute("SELECT * FROM vehicle_matrix;")
    # Handle different response formats
    if isinstance(result, dict):
        rows = result.get("rows", [])
    else:
        rows = result
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
