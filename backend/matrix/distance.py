# backend/distance.py

import math
import asyncio
import aiohttp
import csv
import os
from utils import config  # Import project-specific configuration (API keys, speeds, etc.)

# OpenRouteService API endpoint for driving-car distance matrix
ORS_API_URL = "https://api.openrouteservice.org/v2/matrix/driving-car"
MAX_CHUNK_SIZE = 25  # ORS free-tier often limits max 25x25 matrices


def euclidean_distance_km(p1, p2, use_elevation=True):
    """
    Compute straight-line distance (in km) between two points, optionally using elevation.
    
    Parameters:
    - p1, p2: dict with keys 'lat', 'lon', optionally 'elevation'
    - use_elevation: whether to factor in elevation differences

    Returns:
    - distance in kilometers (float)
    """
    lat1, lon1 = p1["lat"], p1["lon"]
    lat2, lon2 = p2["lat"], p2["lon"]

    # Average latitude in radians for scaling longitude distance
    avg_lat_rad = math.radians((lat1 + lat2) / 2)

    # Convert lat/lon differences to km
    dx = (lon2 - lon1) * 111 * math.cos(avg_lat_rad)
    dy = (lat2 - lat1) * 111

    dz = 0
    if use_elevation and "elevation" in p1 and "elevation" in p2:
        dz = (p2["elevation"] - p1["elevation"]) / 1000  # meters → km

    return math.sqrt(dx**2 + dy**2 + dz**2)


def drone_travel_time_minutes(distance_km, speed_kmph=config.Drone.SPEED_KMPH):
    """
    Estimate drone travel time in minutes given distance (km) and drone speed.
    """
    return (distance_km / speed_kmph) * 60


async def ors_matrix(session, locations, retries=3):
    """
    Query OpenRouteService API for a distance matrix with retry logic.
    
    Parameters:
    - session: aiohttp.ClientSession
    - locations: list of [lon, lat] coordinates
    - retries: number of retry attempts for rate-limiting / network errors

    Returns:
    - distances matrix (nested list) or None on failure
    """
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
            # Retry if rate-limited (HTTP 429)
            if e.status == 429 and attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # exponential backoff
                continue
            raise e
        except asyncio.TimeoutError:
            print("⚠️ ORS API request timed out")
            return None
    return None


async def compute_truck_chunk(session, coords_chunk, all_coords, start_index):
    """
    Compute truck distances for a chunk of origin coordinates using ORS.
    
    Parameters:
    - session: aiohttp.ClientSession
    - coords_chunk: sublist of origins (chunk)
    - all_coords: full list of coordinates (origins + destinations)
    - start_index: index of first origin in chunk
    
    Returns:
    - truck_chunk: 2D list of distances (km), same order as coords_chunk vs all_coords
    """
    results = await ors_matrix(session, all_coords)  # Query ORS for full matrix
    n = len(all_coords)
    truck_chunk = [[None] * n for _ in range(len(coords_chunk))]

    if results:
        for i_local, i_global in enumerate(range(start_index, start_index + len(coords_chunk))):
            for j in range(n):
                if i_global == j:  # Skip self-distance
                    continue
                val = results[i_global][j]
                if val is not None:
                    truck_chunk[i_local][j] = round(val / 1000, 2)  # meters → km
    return truck_chunk


async def compute_distances(nodes):
    """
    Compute both drone (Euclidean) and truck (ORS) distances for all nodes.
    
    Parameters:
    - nodes: list of dicts, each with keys 'node_id', 'lat', 'lon', optionally 'elevation'

    Returns:
    - dist_rows: list of [origin_id, dest_id, truck_km, truck_duration, drone_km, drone_duration]
    """
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

    # --- Truck distances (ORS API) ---
    coords = [[node["lon"], node["lat"]] for node in nodes]
    truck_results = [[None] * n for _ in range(n)]

    async with aiohttp.ClientSession() as session:
        tasks = []
        # Split into chunks to respect ORS max 25x25 limit
        for start in range(0, n, MAX_CHUNK_SIZE):
            end = min(start + MAX_CHUNK_SIZE, n)
            chunk_coords = coords[start:end]
            tasks.append(compute_truck_chunk(session, chunk_coords, coords, start))

        chunks = await asyncio.gather(*tasks)  # Run all chunks concurrently
        for i, chunk in enumerate(chunks):
            start_index = i * MAX_CHUNK_SIZE
            for row_idx, row in enumerate(chunk):
                truck_results[start_index + row_idx] = row

    # --- Merge results into final matrix rows ---
    dist_rows = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            truck_km = truck_results[i][j]
            truck_dur = round((truck_km / config.TRUCK_SPEED) * 60, 2) if truck_km else None
            drone_km, drone_dur = drone_matrix[i][j]
            dist_rows.append([
                nodes[i]["node_id"],  # DB-compatible origin ID
                nodes[j]["node_id"],  # DB-compatible destination ID
                truck_km,             # Truck distance in km
                truck_dur,            # Truck duration in minutes
                drone_km,             # Drone distance in km
                drone_dur             # Drone duration in minutes
            ])

    print("Backend: all distances computed successfully.")

    # --- Optional debug: write distances to CSV ---

    return dist_rows