# vehicle_matrix.py
import pandas as pd
from utils import db_handler, config
from .vehicle import FuelTruck, ElectricTruck, Drone


async def generate_vehicle_matrix(nodes, dist_rows, fleet_config=None):
    """
    Generate a vehicle matrix using actual vehicle metrics.
    Considers weight, volume, distance, energy, emissions, and fleet availability.
    """

    print("⚙️ Building vehicle matrix...")

    # Clear old records
    await db_handler.clear_vehicle_matrix()

    # --- Clean dist_rows ---
    dist_rows = [
        [
            origin_id,
            dest_id,
            float(truck_km) if truck_km is not None else None,
            float(truck_dur) if truck_dur is not None else None,
            float(drone_km) if drone_km is not None else None,
            float(drone_dur) if drone_dur is not None else None,
        ]
        for origin_id, dest_id, truck_km, truck_dur, drone_km, drone_dur in dist_rows
    ]

    # Convert nodes list to dict for quick lookup
    nodes_dict = {n["node_id"]: n for n in nodes}

    # Available vehicle types
    vehicles = [FuelTruck(id="F"), ElectricTruck(id="E"), Drone(id="D")]

    # Compute maximum distance for normalization
    df = pd.DataFrame(dist_rows, columns=[
        "origin_id", "dest_id",
        "truck_distance", "truck_duration",
        "drone_distance", "drone_duration"
    ])
    max_distance = float(df[["truck_distance", "drone_distance"]].max().max())

    metrics_cache = {}

    def get_metrics(v, d):
        """Cache metrics for efficiency"""
        key = (v.id, round(d, 2))
        if key not in metrics_cache:
            metrics_cache[key] = v.metrics(d)
        return metrics_cache[key]

    # Normalization factors
    max_energy = max((get_metrics(v, max_distance)["energy_kwh"] or 0) for v in vehicles)
    max_emission = max((get_metrics(v, max_distance)["co2_kg"] or 0) for v in vehicles)

    db_inserts = []

    for origin_id, dest_id, truck_km, truck_dur, drone_km, drone_dur in dist_rows:
        if origin_id == dest_id:
            continue

        feasible_vehicles, feasible_distances, feasible_durations, feasible_costs = [], [], [], []

        for v in vehicles:
            # Choose correct distance/duration for vehicle
            if isinstance(v, (FuelTruck, ElectricTruck)):
                distance, duration = truck_km, truck_dur
            else:  # Drone
                distance, duration = drone_km, drone_dur

            if distance is None or duration is None:
                continue

            # Destination node details
            node = nodes_dict[dest_id]

            # Check payload feasibility
            if not v.can_carry(node["weight"], node["volume"], distance):
                continue

            # Get full metrics
            m = v.metrics(distance)
            if not m.get("feasible", True):
                continue

            # Weighted cost function (α, β, γ from config)
            total_cost = v.total_cost(distance, max_energy, max_emission)

            # Append feasible result
            feasible_vehicles.append(v.id)
            feasible_distances.append(distance)
            feasible_durations.append(duration)
            feasible_costs.append(total_cost)

        if feasible_vehicles:
            db_inserts.append([
                origin_id,
                dest_id,
                str(tuple(feasible_vehicles)),
                str(tuple(feasible_distances)),
                str(tuple(feasible_durations)),
                str(tuple(feasible_costs))
            ])

    # Bulk insert into DB
    BATCH_SIZE = 500
    for i in range(0, len(db_inserts), BATCH_SIZE):
        await db_handler.insert_vehicle_matrix_bulk(db_inserts[i:i + BATCH_SIZE])

    print(f"Vehicle matrix inserted ({len(db_inserts)} entries).")
