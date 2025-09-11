import pandas as pd
from utils import db_handler, config
from .vehicle import FuelTruck, ElectricTruck, Drone


async def generate_vehicle_matrix(nodes, dist_rows):
    """
    Generate a vehicle matrix for all node-to-node distances and durations.
    Each row contains tuples of feasible vehicles, their distances, durations, and costs.
    """
    print("Building vehicle matrix...")

    # --- Clean dist_rows ---
    cleaned_rows = []
    for r in dist_rows:
        origin_id, dest_id, truck_km, truck_dur, drone_km, drone_dur = r
        cleaned_rows.append([
            origin_id,
            dest_id,
            float(truck_km) if truck_km is not None else None,
            float(truck_dur) if truck_dur is not None else None,
            float(drone_km) if drone_km is not None else None,
            float(drone_dur) if drone_dur is not None else None,
        ])
    dist_rows = cleaned_rows

    nodes_dict = {n["node_id"]: n for n in nodes}
    vehicles = [FuelTruck(id="F"), ElectricTruck(id="E"), Drone(id="D")]

    df = pd.DataFrame(dist_rows, columns=[
        "origin_id", "dest_id",
        "truck_distance", "truck_duration",
        "drone_distance", "drone_duration"
    ])

    max_distance = float(df[["truck_distance", "drone_distance"]].max().max())
    metrics_cache = {}

    def get_metrics(v, d):
        key = (v.id, round(d, 2))
        if key not in metrics_cache:
            metrics_cache[key] = v.metrics(d)
        return metrics_cache[key]

    max_energy = max(float(get_metrics(v, max_distance)["energy_kwh"] or 0) for v in vehicles)
    max_emission = max(float(get_metrics(v, max_distance)["co2_kg"] or 0) for v in vehicles)

    db_inserts = []

    for origin_id, dest_id, truck_km, truck_dur, drone_km, drone_dur in dist_rows:
        if origin_id == dest_id:
            continue

        feasible_vehicles, feasible_distances, feasible_durations, feasible_costs = [], [], [], []

        for v in vehicles:
            distance = truck_km if isinstance(v, (FuelTruck, ElectricTruck)) else drone_km
            duration = truck_dur if isinstance(v, (FuelTruck, ElectricTruck)) else drone_dur
            if distance is None or duration is None:
                continue

            feasible = v.can_carry(
                nodes_dict[dest_id]["weight"],
                nodes_dict[dest_id]["volume"],
                distance
            )
            if isinstance(v, (ElectricTruck, Drone)):
                feasible = feasible and v.can_complete_route(distance / 2)
            if not feasible:
                continue

            metrics = get_metrics(v, distance)
            energy_norm = (metrics["energy_kwh"] or 0) / max_energy if max_energy else 0
            co2_norm = (metrics["co2_kg"] or 0) / max_emission if max_emission else 0

            total_cost = round(
                config.ALPHA * float(distance) +
                config.BETA * float(energy_norm) +
                config.GAMMA * float(co2_norm),
                2
            )

            feasible_vehicles.append(str(v.id))
            feasible_distances.append(float(distance))
            feasible_durations.append(float(duration))
            feasible_costs.append(float(total_cost))

        if feasible_vehicles:
            # Store tuples in single row
            db_inserts.append([
                origin_id,
                dest_id,
                str(tuple(feasible_vehicles)),
                str(tuple(feasible_distances)),
                str(tuple(feasible_durations)),
                str(tuple(feasible_costs))
            ])

    # Bulk insert in batches
    BATCH_SIZE = 500
    for i in range(0, len(db_inserts), BATCH_SIZE):
        await db_handler.insert_vehicle_matrix_bulk(db_inserts[i:i + BATCH_SIZE])

    print(f"Vehicle matrix inserted into DB successfully ({len(db_inserts)} entries).")
