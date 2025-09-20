import pandas as pd
import asyncio
from utils import db_handler
from .vehicle import FuelTruck, ElectricTruck, Drone

async def generate_vehicle_matrix(nodes, dist_rows, fleet_config=None):
    """
    Build vehicle matrix:
      - Trucks: always feasible if within capacity
      - Drones: only depot→customer and customer→depot if feasible
    """
    print("⚙️ Building vehicle matrix...")
    await db_handler.clear_vehicle_matrix()

    # Ensure all distances/durations are floats or None
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

    nodes_dict = {n["node_id"]: n for n in nodes}
    vehicles = [FuelTruck(id="F"), ElectricTruck(id="E"), Drone(id="D")]

    # Precompute max distance for normalization
    df = pd.DataFrame(dist_rows, columns=[
        "origin_id", "dest_id", "truck_distance", "truck_duration",
        "drone_distance", "drone_duration"
    ])
    max_distance = float(df[["truck_distance", "drone_distance"]].max().max())
    metrics_cache = {}

    def get_metrics(vehicle, distance):
        key = (vehicle.id, round(distance, 2))
        if key not in metrics_cache:
            metrics_cache[key] = vehicle.metrics(distance)
        return metrics_cache[key]

    max_energy = max([m.get("energy_kwh") or 0 for m in (get_metrics(v, max_distance) for v in vehicles)])
    max_emission = max([m.get("co2_kg") or 0 for m in (get_metrics(v, max_distance) for v in vehicles)])

    async def process_od_pair(od):
        origin_id, dest_id, truck_km, truck_dur, drone_km, drone_dur = od
        if origin_id == dest_id:
            return None

        feasible_vehicles, feasible_distances, feasible_durations, feasible_costs = [], [], [], []

        for v in vehicles:
            # Determine which distance/duration to use
            distance, duration = (drone_km, drone_dur) if isinstance(v, Drone) else (truck_km, truck_dur)
            if distance is None or duration is None:
                continue

            # Determine which node to check for payload
            node = nodes_dict[dest_id] if not isinstance(v, Drone) or origin_id == "depot" else nodes_dict[origin_id]

            # Check payload and route feasibility
            if not v.can_carry(node.get("weight", 0), node.get("volume", 0), distance):
                continue
            if isinstance(v, Drone) and not v.can_complete_route(distance):
                continue

            # Compute cost
            m = v.metrics(distance)
            total_cost = round(v.total_cost(distance, max_energy, max_emission), 2)

            feasible_vehicles.append(v.id)
            feasible_distances.append(distance)
            feasible_durations.append(duration)
            feasible_costs.append(total_cost)

        if feasible_vehicles:
            return [
                origin_id,
                dest_id,
                str(tuple(feasible_vehicles)),
                str(tuple(feasible_distances)),
                str(tuple(feasible_durations)),
                str(tuple(feasible_costs)),
            ]
        return None

    # Limit concurrency for large matrices
    semaphore = asyncio.Semaphore(50)

    async def sem_process(od):
        async with semaphore:
            return await process_od_pair(od)

    results = await asyncio.gather(*[sem_process(od) for od in dist_rows])
    db_inserts = [r for r in results if r is not None]

    # Insert in batches
    BATCH_SIZE = 1000
    for i in range(0, len(db_inserts), BATCH_SIZE):
        await db_handler.insert_vehicle_matrix_bulk(db_inserts[i:i + BATCH_SIZE])

    print(f"Vehicle matrix inserted ({len(db_inserts)} entries).")
