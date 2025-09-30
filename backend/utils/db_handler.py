# utils/db_handler.py
import asyncio
from libsql_client import create_client
from utils import config

# ----------------- Globals -----------------
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
    print("Initializing database...")

    # Drop tables if they exist
    for table in ["generated_nodes", "vehicle_matrix", "vehicles"]:
        try:
            res = await client.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
            if res and len(res) > 0:
                await client.execute(f"DROP TABLE {table};")
        except Exception as e:
            print(f"Warning dropping table {table}: {e}")

    # Create tables
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
        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY,
            vehicle_id TEXT UNIQUE,
            capacity_kg REAL,
            capacity_cm3 REAL,
            speed_kmph REAL,
            range_km REAL
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
    try:
        await client.execute("""
            CREATE UNIQUE INDEX vehicle_matrix_unique_idx
            ON vehicle_matrix(origin_id, dest_id, vehicle_type);
        """)
    except Exception:
        pass

    print("Database initialized successfully.")

# ----------------- Clear Tables -----------------
async def clear_generated_nodes():
    await get_client().execute("DELETE FROM generated_nodes;")

async def clear_vehicles():
    await get_client().execute("DELETE FROM vehicles;")

async def clear_vehicle_matrix():
    await get_client().execute("DELETE FROM vehicle_matrix;")

# ----------------- Inserts -----------------
async def insert_nodes_bulk(nodes):
    """Insert multiple nodes in batches."""
    client = get_client()
    query = """
        INSERT OR IGNORE INTO generated_nodes (node_id, weight, volume, lon, lat)
        VALUES (?, ?, ?, ?, ?)
    """
    for i in range(0, len(nodes), DB_BATCH_SIZE):
        batch = nodes[i:i + DB_BATCH_SIZE]
        for node in batch:
            try:
                await client.execute(query, [node["node_id"], node["weight"], node["volume"], node["lon"], node["lat"]])
            except Exception as e:
                print(f"Error inserting node {node['node_id']}: {e}")

async def insert_vehicles_bulk(vehicles):
    """Insert vehicles in batches."""
    client = get_client()
    query = """
        INSERT OR IGNORE INTO vehicles
        (vehicle_id, capacity_kg, capacity_cm3, speed_kmph, range_km)
        VALUES (?, ?, ?, ?, ?)
    """
    for v in vehicles:
        try:
            await client.execute(query, [
                v["vehicle_id"], v["capacity_kg"], v["capacity_cm3"], v["speed_kmph"], v["range_km"]
            ])
        except Exception as e:
            print(f"Error inserting vehicle {v['vehicle_id']}: {e}")

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
            VALUES {', '.join(values)}
            ON CONFLICT(origin_id, dest_id, vehicle_type) DO NOTHING;
        """
        try:
            await client.execute(query, params)
        except Exception as e:
            print(f"[Bulk Insert Error] Batch starting at {i} | {e}")

# ----------------- Queries -----------------
async def get_nodes():
    client = get_client()
    result = await client.execute("SELECT * FROM generated_nodes;")
    rows = result.get("rows", []) if isinstance(result, dict) else result
    return [{"id": r[0], "node_id": r[1], "weight": r[2], "volume": r[3], "lon": r[4], "lat": r[5]} for r in rows]

async def get_vehicles():
    client = get_client()
    result = await client.execute("SELECT * FROM vehicles;")
    rows = result.get("rows", []) if isinstance(result, dict) else result
    return [{"id": r[0], "vehicle_id": r[1], "capacity_kg": r[2], "capacity_cm3": r[3], "speed_kmph": r[4], "range_km": r[5]} for r in rows]

async def get_vehicle_matrix():
    client = get_client()
    result = await client.execute("SELECT * FROM vehicle_matrix;")
    rows = result.get("rows", []) if isinstance(result, dict) else result
    return [{"id": r[0], "origin_id": r[1], "dest_id": r[2], "vehicle_type": r[3], "distance": r[4], "duration": r[5], "total_cost": r[6]} for r in rows]

async def get_all_data():
    nodes = await get_nodes()
    vehicle_matrix = await get_vehicle_matrix()
    vehicles = await get_vehicles()
    return nodes, vehicle_matrix, vehicles
