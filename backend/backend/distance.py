import math
import asyncio
import aiohttp
from utils import config

ORS_API_URL = "https://api.openrouteservice.org/v2/matrix/driving-car"
MAX_CHUNK_SIZE = 25  # ORS free-tier often limits max 25x25 matrix


def euclidean_distance_km(p1, p2, use_elevation=True):
    lat1, lon1 = p1["lat"], p1["lon"]
    lat2, lon2 = p2["lat"], p2["lon"]
    avg_lat_rad = math.radians((lat1 + lat2) / 2)
    dx = (lon2 - lon1) * 111 * math.cos(avg_lat_rad)
    dy = (lat2 - lat1) * 111
    dz = 0
    if use_elevation and "elevation" in p1 and "elevation" in p2:
        dz = (p2["elevation"] - p1["elevation"]) / 1000
    return math.sqrt(dx**2 + dy**2 + dz**2)


def drone_travel_time_minutes(distance_km, speed_kmph=config.Drone.SPEED_KMPH):
    return (distance_km / speed_kmph) * 60


async def ors_matrix(session, locations, retries=3):
    """Call ORS API with retries and timeout."""
    payload = {"locations": locations, "metrics": ["distance"]}
    headers = {"Authorization": config.ORS_API_KEY, "Content-Type": "application/json"}

    for attempt in range(retries):
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with session.post(ORS_API_URL, json=payload, headers=headers, timeout=timeout) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("distances")
        except aiohttp.ClientResponseError as e:
            if e.status == 429 and attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise e
        except asyncio.TimeoutError:
            print("⚠️ ORS API request timed out")
            return None
    return None


async def compute_truck_chunk(session, coords_chunk, all_coords, start_index):
    """Compute truck distances for a chunk of origins."""
    results = await ors_matrix(session, all_coords)
    n = len(all_coords)
    truck_chunk = [[None] * n for _ in range(len(coords_chunk))]
    if results:
        for i_local, i_global in enumerate(range(start_index, start_index + len(coords_chunk))):
            for j in range(n):
                if i_global == j:
                    continue
                truck_chunk[i_local][j] = round(results[i_global][j] / 1000, 2)
    return truck_chunk


async def compute_distances(nodes):
    n = len(nodes)
    print(f"Calculating distances for {n} nodes...")

    # --- Drone distances (Euclidean) ---
    drone_matrix = [[(0, 0)] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            dist_km = euclidean_distance_km(nodes[i], nodes[j])
            drone_matrix[i][j] = (round(dist_km, 2), round(drone_travel_time_minutes(dist_km), 2))

    # --- Truck distances (parallel ORS calls) ---
    coords = [[node["lon"], node["lat"]] for node in nodes]
    truck_results = [[None]*n for _ in range(n)]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for start in range(0, n, MAX_CHUNK_SIZE):
            end = min(start + MAX_CHUNK_SIZE, n)
            chunk_coords = coords[start:end]
            tasks.append(compute_truck_chunk(session, chunk_coords, coords, start))

        # Gather all chunk results concurrently
        chunks = await asyncio.gather(*tasks)
        for i, chunk in enumerate(chunks):
            start_index = i * MAX_CHUNK_SIZE
            for row_idx, row in enumerate(chunk):
                truck_results[start_index + row_idx] = row

    # --- Prepare vehicle matrix rows ---
    dist_rows = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            truck_km = truck_results[i][j]
            truck_dur = round((truck_km / config.TRUCK_SPEED) * 60, 2) if truck_km else None
            drone_km, drone_dur = drone_matrix[i][j]
            dist_rows.append([
                nodes[i]["node_id"],
                nodes[j]["node_id"],
                truck_km,
                truck_dur,
                drone_km,
                drone_dur
            ])

    print("Backend: all distances computed successfully.")
    return dist_rows
