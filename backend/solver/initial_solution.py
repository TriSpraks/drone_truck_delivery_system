import ast
from collections import deque
from utils import db_handler

async def fetch_data():
    nodes = await db_handler.get_nodes()
    vehicles = await db_handler.get_vehicles()
    vehicle_matrix_rows = await db_handler.get_vehicle_matrix()
    return nodes, vehicles, vehicle_matrix_rows

def preprocess_matrix(rows):
    """Convert DB matrix strings to proper float tuples per vehicle type."""
    matrix = {}
    for r in rows:
        origin, dest = r["origin_id"], r["dest_id"]
        vtypes = ast.literal_eval(r["vehicle_type"])
        dist_tuple = tuple(map(float, ast.literal_eval(r["distance"])))
        dur_tuple = tuple(map(float, ast.literal_eval(r["duration"])))
        cost_tuple = tuple(map(float, ast.literal_eval(r["total_cost"])))

        if (origin, dest) not in matrix:
            matrix[(origin, dest)] = {}

        for i, v in enumerate(vtypes):
            matrix[(origin, dest)][v.upper()] = (dist_tuple[i], dur_tuple[i], cost_tuple[i])
    return matrix

def greedy_cluster(truck_nodes, depot_id, matrix, max_cluster_size=3):
    clusters = []
    unvisited = set(n["node_id"] for n in truck_nodes)
    while unvisited:
        cluster = []
        current = depot_id
        while unvisited and len(cluster) < max_cluster_size:
            candidates = [(n, matrix.get((current, n), {}).get("F", (1e9, 0, 1e9))[0]) for n in unvisited]
            next_node, _ = min(candidates, key=lambda x: x[1])
            cluster.append(next_node)
            unvisited.remove(next_node)
            current = next_node
        clusters.append(cluster)
    return clusters

def select_truck_for_cluster(cluster, vtype, fleet_state, vehicles, nodes_map):
    """Check payload & volume constraints for trucks."""
    for truck_id in fleet_state[vtype]:
        truck = next(v for v in vehicles if v["vehicle_id"] == truck_id)
        total_weight = sum(nodes_map[n]["weight"] for n in cluster)
        total_volume = sum(nodes_map[n]["volume"] for n in cluster)
        if total_weight <= truck["capacity_kg"] and total_volume <= truck["capacity_cm3"]:
            return truck_id
    return None

async def build_initial_solution():
    nodes, vehicles, vehicle_matrix_rows = await fetch_data()
    matrix = preprocess_matrix(vehicle_matrix_rows)

    depot = next((n for n in nodes if n["node_id"].lower() == "depot"), None)
    if not depot:
        raise ValueError("Depot node not found in DB")
    depot_id = depot["node_id"]

    fleet_config = {"D": [], "E": [], "F": []}
    for v in vehicles:
        if "Drone" in v["vehicle_id"]:
            fleet_config["D"].append(v["vehicle_id"])
        elif "Fuel" in v["vehicle_id"]:
            fleet_config["F"].append(v["vehicle_id"])
        else:
            fleet_config["E"].append(v["vehicle_id"])

    demand_nodes = [n for n in nodes if n["node_id"].lower() != "depot"]
    nodes_map = {n["node_id"]: n for n in demand_nodes}

    drone_nodes, truck_nodes = [], []
    available_drones = fleet_config["D"][:]

    # Assign nodes to drones or trucks (payload ignored for drones)
    for node in demand_nodes:
        if "D" in matrix.get((depot_id, node["node_id"]), {}) and available_drones:
            drone_nodes.append(node)
            available_drones.pop(0)
        else:
            truck_nodes.append(node)

    # --- Drone routes ---
    drone_routes = []
    for i, node in enumerate(drone_nodes):
        route = [depot_id, node["node_id"], depot_id]
        dist, cost = 0, 0
        for j in range(len(route)-1):
            d, _, c = matrix[(route[j], route[j+1])]["D"]
            dist += d
            cost += c
        drone_routes.append({
            "vehicle_id": fleet_config["D"][i] if i < len(fleet_config["D"]) else f"D_{i+1}",
            "node_ids": [node["node_id"]],
            "route": route,
            "distance": round(dist, 4),
            "cost": round(cost, 4)
        })

    # --- Truck clusters ---
    clusters = greedy_cluster(truck_nodes, depot_id, matrix)
    truck_routes = []
    cluster_queue = deque(clusters)
    fleet_state = {"E": fleet_config["E"][:], "F": fleet_config["F"][:]}  # available trucks

    wave = 1
    max_waves = 10
    solution = {}

    while cluster_queue and wave <= max_waves:
        remaining_clusters = deque()
        wave_routes = {"drones": [], "trucks": [], "total_distance": 0, "total_cost": 0}

        # Add drone routes only in first wave
        if wave == 1:
            wave_routes["drones"] = drone_routes
            wave_routes["total_distance"] = round(sum(r["distance"] for r in drone_routes), 4)
            wave_routes["total_cost"] = round(sum(r["cost"] for r in drone_routes), 4)

        while cluster_queue:
            cluster = cluster_queue.popleft()
            chosen_vehicle = None
            for vtype in ["E", "F"]:
                chosen_vehicle = select_truck_for_cluster(cluster, vtype, fleet_state, vehicles, nodes_map)
                if chosen_vehicle:
                    fleet_state[vtype].remove(chosen_vehicle)
                    break

            if chosen_vehicle:
                route_nodes = [depot_id] + cluster + [depot_id]
                dist, cost = 0, 0
                for j in range(len(route_nodes)-1):
                    d, _, c = matrix[(route_nodes[j], route_nodes[j+1])][vtype]
                    dist += d
                    cost += c
                dist = round(dist, 4)
                cost = round(cost, 4)
                truck_routes.append({
                    "vehicle_id": chosen_vehicle,
                    "node_ids": cluster,
                    "route": route_nodes,
                    "distance": dist,
                    "cost": cost
                })
                wave_routes["trucks"].append(truck_routes[-1])
                wave_routes["total_distance"] = round(wave_routes["total_distance"] + dist, 4)
                wave_routes["total_cost"] = round(wave_routes["total_cost"] + cost, 4)
            else:
                remaining_clusters.append(cluster)

        solution[f"wave_{wave}"] = wave_routes

        if not remaining_clusters:
            break

        if wave == max_waves:
            print(f"Safety break reached. Clusters not assigned: {list(remaining_clusters)}")
            break

        cluster_queue = remaining_clusters
        wave += 1
        fleet_state = {"E": fleet_config["E"][:], "F": fleet_config["F"][:]}

    return solution
