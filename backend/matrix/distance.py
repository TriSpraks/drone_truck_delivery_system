import math
import asyncio
import aiohttp
from utils import config
from .vehicle import Drone

ORS_API_URL = "https://api.openrouteservice.org/v2/matrix/driving-car"

def euclidean_distance_km(p1: dict, p2: dict) -> float:
    lat1, lon1 = p1["lat"], p1["lon"]
    lat2, lon2 = p2["lat"], p2["lon"]
    avg_lat_rad = math.radians((lat1 + lat2) / 2)
    dx = (lon2 - lon1) * 111 * math.cos(avg_lat_rad)
    dy = (lat2 - lat1) * 111
    dz = 0
    if "elevation" in p1 and "elevation" in p2:
        dz = (p2["elevation"] - p1["elevation"]) / 1000
    return math.sqrt(dx**2 + dy**2 + dz**2)

def drone_travel_time_minutes(distance_km: float, speed_kmph: float = config.DRONE_SPEED) -> float:
    return round((distance_km / speed_kmph) * 60, 2)

async def ors_matrix(session: aiohttp.ClientSession, locations: list, retries: int = 3):
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
            print("⚠️ ORS API timeout")
            return None
    return None

async def compute_distances(nodes: list):
    n = len(nodes)
    depot_index = 0  # assuming first node is depot

    # Drone matrix: (distance_km, duration_min)
    drone_matrix = [[(None, None)] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # Drone distance only if depot is involved
            if i == depot_index or j == depot_index:
                dist_km = round(euclidean_distance_km(nodes[i], nodes[j]), 2)
                dur_min = drone_travel_time_minutes(dist_km)
                drone_matrix[i][j] = (dist_km, dur_min)

    # Truck distances via ORS
    coords = [[node["lon"], node["lat"]] for node in nodes]
    truck_results = [[None] * n for _ in range(n)]
    async with aiohttp.ClientSession() as session:
        results = await ors_matrix(session, coords)
        if results:
            for i in range(n):
                for j in range(n):
                    if i != j and results[i][j] is not None:
                        truck_results[i][j] = round(results[i][j] / 1000, 2)

    # Merge distances and durations
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

    return dist_rows
