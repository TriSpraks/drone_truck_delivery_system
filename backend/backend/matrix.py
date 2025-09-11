# backend/matrix.py
import pandas as pd
from utils import db_handler, config
from .vehicle import FuelTruck, ElectricTruck, Drone


async def generate_vehicle_matrix(nodes, dist_rows):
    """
    Optimized version:
    - Loops directly over dist_rows (no Pandas iteration).
    - Precomputes vehicle metrics for all possible distances.
    - Uses batch inserts instead of row-by-row.
    """
    print("Building vehicle matrix...")

    nodes_dict = {n["node_id"]: n for n in nodes}
    vehicles = [FuelTruck(id="F"), ElectricTruck(id="E"), Drone(id="D")]

    # Convert to DataFrame (fast column ops)
    df = pd.DataFrame(dist_rows, columns=[
        "origin_id", "dest_id",
        "truck_distance", "truck_duration",
        "drone_distance", "drone_duration"
    ])

    # --- Precompute normalization factors ---
    max_distance = df[["truck_distance", "drone_distance"]].max().max()
    metrics_cache = {}

    def get_metrics(v, d):
        key = (v.id, round(d, 2))
        if key not in metrics_cache:
            metrics_cache[key] = v.metrics(d)
        return metrics_cache[key]

    max_energy = max(
        get_metrics(v, max_distance)["energy_kwh"] or 0
        for v in vehicles
    )
    max_emission = max(
        get_metrics(v, max_distance)["co2_kg"] or 0
        for v in vehicles
    )

    # --- Build DB rows ---
    db_inserts = []
    for row in dist_rows:  # much faster than df.iterrows()
        origin_id, dest_id, truck_km, truck_dur, drone_km, drone_dur = row
        if origin_id == dest_id:
            continue

        feasible_vehicles, feasible_distances, feasible_costs = [], [], []

        for v in vehicles:
            distance = truck_km if isinstance(v, (FuelTruck, ElectricTruck)) else drone_km
            if distance is None:
                continue

            # --- Feasibility checks ---
            feasible = v.can_carry(
                nodes_dict[dest_id]["weight"],
                nodes_dict[dest_id]["volume"],
                distance
            )
            if isinstance(v, (ElectricTruck, Drone)):
                feasible = feasible and v.can_complete_route(distance / 2)

            if not feasible:
                continue

            # --- Compute normalized cost ---
            metrics = get_metrics(v, distance)
            energy_norm = (metrics["energy_kwh"] or 0) / max_energy if max_energy else 0
            co2_norm = (metrics["co2_kg"] or 0) / max_emission if max_emission else 0
            total = round(
                config.ALPHA * distance + config.BETA * energy_norm + config.GAMMA * co2_norm,
                2,
            )

            feasible_vehicles.append(v.id)
            feasible_distances.append(distance)
            feasible_costs.append(total)

        if feasible_vehicles:
            db_inserts.append([
                origin_id,
                dest_id,
                str(tuple(feasible_vehicles)),
                str(tuple(feasible_distances)),
                str(tuple(feasible_costs))
            ])

    # --- Bulk insert in chunks (⚡ avoids 2500+ single writes) ---
    BATCH_SIZE = 500
    for i in range(0, len(db_inserts), BATCH_SIZE):
        await db_handler.insert_vehicle_matrix_bulk(db_inserts[i:i + BATCH_SIZE])

    print(f"Vehicle matrix inserted into DB successfully ({len(db_inserts)} entries).")
