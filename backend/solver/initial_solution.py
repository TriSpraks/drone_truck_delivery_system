
from collections import deque
from utils import db_handler
from .preprocess import fetch_data, preprocess_matrix, calculate_route_distance, check_range_constraint


def create_smart_clusters(truck_nodes, depot_id, matrix, min_cluster_size=2, max_cluster_size=4):
    """Create clusters using nearest neighbor approach with size constraints"""
    clusters = []
    unvisited = {n["node_id"]: n for n in truck_nodes}
    
    while unvisited:
        cluster_nodes = []
        current = depot_id
        
        # Start cluster with nearest unvisited node
        if unvisited:
            candidates = []
            for node_id, node in unvisited.items():
                dist = matrix.get((current, node_id), {}).get("E", (1e9, 0, 1e9))[0]
                if dist == 1e9:  # Try fuel truck if electric not available
                    dist = matrix.get((current, node_id), {}).get("F", (1e9, 0, 1e9))[0]
                candidates.append((node_id, node, dist))
            
            # Sort by distance and start with nearest
            candidates.sort(key=lambda x: x[2])
            first_node_id, first_node, _ = candidates[0]
            cluster_nodes.append(first_node)
            current = first_node_id
            del unvisited[first_node_id]
        
        # Add more nodes to cluster using nearest neighbor
        while len(cluster_nodes) < max_cluster_size and unvisited:
            candidates = []
            for node_id, node in unvisited.items():
                dist = matrix.get((current, node_id), {}).get("E", (1e9, 0, 1e9))[0]
                if dist == 1e9:
                    dist = matrix.get((current, node_id), {}).get("F", (1e9, 0, 1e9))[0]
                candidates.append((node_id, node, dist))
            
            if not candidates:
                break
                
            # Sort by distance and take nearest
            candidates.sort(key=lambda x: x[2])
            next_node_id, next_node, _ = candidates[0]
            cluster_nodes.append(next_node)
            current = next_node_id
            del unvisited[next_node_id]
        
        if cluster_nodes:
            clusters.append(cluster_nodes)
    
    return clusters

def fit_clusters_to_truck_aggressive(clusters, truck, vtype, depot_id, matrix, nodes_map):
    """More aggressive version that tries to fit individual nodes if clusters don't work"""
    truck_capacity_kg = truck["capacity_kg"]
    truck_capacity_cm3 = truck["capacity_cm3"]
    truck_range = truck.get("range_km", float('inf'))
    
    assigned_nodes = []
    current_weight = 0
    current_volume = 0
    remaining_clusters = clusters[:]
    
    # First try to fit complete clusters
    while remaining_clusters:
        best_cluster = None
        best_cluster_idx = None
        best_fit_score = -1
        
        for idx, cluster in enumerate(remaining_clusters):
            cluster_weight = sum(nodes_map[n["node_id"]]["weight"] for n in cluster)
            cluster_volume = sum(nodes_map[n["node_id"]]["volume"] for n in cluster)
            
            if (current_weight + cluster_weight <= truck_capacity_kg and 
                current_volume + cluster_volume <= truck_capacity_cm3):
                
                test_route = [depot_id] + [n["node_id"] for n in assigned_nodes] + [n["node_id"] for n in cluster] + [depot_id]
                
                if check_range_constraint(test_route, matrix, vtype, truck_range):
                    weight_util = (current_weight + cluster_weight) / truck_capacity_kg
                    volume_util = (current_volume + cluster_volume) / truck_capacity_cm3
                    fit_score = (weight_util + volume_util) / 2
                    
                    if fit_score > best_fit_score:
                        best_fit_score = fit_score
                        best_cluster = cluster
                        best_cluster_idx = idx
        
        if best_cluster is not None:
            cluster_weight = sum(nodes_map[n["node_id"]]["weight"] for n in best_cluster)
            cluster_volume = sum(nodes_map[n["node_id"]]["volume"] for n in best_cluster)
            
            assigned_nodes.extend(best_cluster)
            current_weight += cluster_weight
            current_volume += cluster_volume
            remaining_clusters.pop(best_cluster_idx)
        else:
            break
    
    # If there's still capacity, try to fit individual nodes from remaining clusters
    if remaining_clusters and (current_weight < truck_capacity_kg * 0.9 or current_volume < truck_capacity_cm3 * 0.9):
        print(f"Truck still has capacity, trying individual nodes...")
        
        # Flatten remaining clusters to individual nodes
        available_nodes = []
        for cluster in remaining_clusters:
            available_nodes.extend(cluster)

        # Sort nodes by distance to last assigned node
        last_node_id = assigned_nodes[-1]["node_id"] if assigned_nodes else depot_id
        available_nodes.sort(
            key=lambda n: matrix.get((last_node_id, n["node_id"]), {}).get(vtype, (1e9,0,1e9))[0]
        )
        
        fitted_individual_nodes = []
        for node in available_nodes:
            node_weight = nodes_map[node["node_id"]]["weight"]
            node_volume = nodes_map[node["node_id"]]["volume"]
            
            if (current_weight + node_weight <= truck_capacity_kg and 
                current_volume + node_volume <= truck_capacity_cm3):
                
                test_route = [depot_id] + [n["node_id"] for n in assigned_nodes] + [node["node_id"]] + [depot_id]
                if check_range_constraint(test_route, matrix, vtype, truck_range):
                    assigned_nodes.append(node)
                    current_weight += node_weight
                    current_volume += node_volume
                    fitted_individual_nodes.append(node)
        
        # Update remaining_clusters by removing fitted individual nodes
        updated_remaining_clusters = []
        for cluster in remaining_clusters:
            updated_cluster = [n for n in cluster if n not in fitted_individual_nodes]
            if updated_cluster:
                updated_remaining_clusters.append(updated_cluster)
        
        remaining_clusters = updated_remaining_clusters
    
    return assigned_nodes, current_weight, current_volume, remaining_clusters

def optimize_cluster_for_truck(cluster_nodes, truck, vtype, depot_id, matrix, nodes_map):
    """Reduce cluster size to fit truck constraints if needed"""
    truck_capacity_kg = truck["capacity_kg"]
    truck_capacity_cm3 = truck["capacity_cm3"]
    truck_range = truck.get("range_km", float('inf'))
    
    # Sort nodes by priority (you can adjust this logic)
    # Here we prioritize by weight efficiency (value per weight ratio)
    sorted_nodes = sorted(cluster_nodes, key=lambda n: nodes_map[n["node_id"]]["weight"])
    
    optimized_cluster = []
    current_weight = 0
    current_volume = 0
    
    for node in sorted_nodes:
        node_weight = nodes_map[node["node_id"]]["weight"]
        node_volume = nodes_map[node["node_id"]]["volume"]
        
        # Check if adding this node violates constraints
        if (current_weight + node_weight <= truck_capacity_kg and 
            current_volume + node_volume <= truck_capacity_cm3):
            
            # Check range constraint
            test_route = [depot_id] + [n["node_id"] for n in optimized_cluster] + [node["node_id"]] + [depot_id]
            if check_range_constraint(test_route, matrix, vtype, truck_range):
                optimized_cluster.append(node)
                current_weight += node_weight
                current_volume += node_volume
            else:
                break  # Range exceeded, stop adding nodes
        else:
            break  # Capacity exceeded, stop adding nodes
    
    removed_nodes = [n for n in cluster_nodes if n not in optimized_cluster]
    return optimized_cluster, current_weight, current_volume, removed_nodes

async def build_initial_solution():
    nodes, vehicles, vehicle_matrix_rows = await fetch_data()
    matrix = preprocess_matrix(vehicle_matrix_rows)

    depot = next((n for n in nodes if n["node_id"].lower() == "depot"), None)
    if not depot:
        raise ValueError("Depot node not found in DB")
    depot_id = depot["node_id"]

    # Create vehicle mappings
    fleet_config = {"D": [], "E": [], "F": []}
    vehicles_map = {}
    
    for v in vehicles:
        vehicles_map[v["vehicle_id"]] = v
        if "Drone" in v["vehicle_id"]:
            fleet_config["D"].append(v["vehicle_id"])
        elif "Fuel" in v["vehicle_id"]:
            fleet_config["F"].append(v["vehicle_id"])
        else:
            fleet_config["E"].append(v["vehicle_id"])

    demand_nodes = [n for n in nodes if n["node_id"].lower() != "depot"]
    nodes_map = {n["node_id"]: n for n in demand_nodes}

    # Separate drone-eligible and truck-only nodes
    drone_eligible_nodes = []
    truck_only_nodes = []
    
    for node in demand_nodes:
        # Check if drone route exists for this node
        if "D" in matrix.get((depot_id, node["node_id"]), {}):
            drone_eligible_nodes.append(node)
        else:
            truck_only_nodes.append(node)
    
    print(f"Drone eligible nodes: {len(drone_eligible_nodes)}")
    print(f"Truck only nodes: {len(truck_only_nodes)}")
    
    # Create clusters only from truck-only nodes initially
    truck_clusters = create_smart_clusters(truck_only_nodes, depot_id, matrix)
    
    # Track remaining drone eligible nodes separately
    remaining_drone_nodes = drone_eligible_nodes[:]
    remaining_truck_clusters = truck_clusters[:]
    
    # Process waves
    wave = 1
    max_waves = 10
    solution = {}
    total_drones_available = len(fleet_config["D"])
    
    while (remaining_drone_nodes or remaining_truck_clusters) and wave <= max_waves:
        wave_routes = {"drones": [], "trucks": [], "total_distance": 0, "total_cost": 0, "total_weight": 0, "total_volume": 0}
        wave_has_assignments = False
        
        # Available fleet for this wave
        available_drones = fleet_config["D"][:]
        available_e_trucks = fleet_config["E"][:]
        available_f_trucks = fleet_config["F"][:]
        
        # Priority 1: Assign drone-eligible nodes to drones (drone-only policy)
        if remaining_drone_nodes and available_drones:
            nodes_to_assign = min(len(remaining_drone_nodes), len(available_drones))
            
            for i in range(nodes_to_assign):
                node = remaining_drone_nodes.pop(0)
                drone_id = available_drones.pop(0)
                
                route = [depot_id, node["node_id"], depot_id]
                dist, cost = 0, 0
                for j in range(len(route)-1):
                    d, _, c = matrix[(route[j], route[j+1])]["D"]
                    dist += d
                    cost += c
                
                drone_route = {
                    "vehicle_id": drone_id,
                    "node_ids": [node["node_id"]],
                    "route": route,
                    "distance": round(dist, 4),
                    "cost": round(cost, 4),
                    "total_weight": round(node["weight"], 2),
                    "total_volume": round(node["volume"], 2)
                }
                
                wave_routes["drones"].append(drone_route)
                wave_routes["total_distance"] += drone_route["distance"]
                wave_routes["total_cost"] += drone_route["cost"]
                wave_routes["total_weight"] += drone_route["total_weight"]
                wave_routes["total_volume"] += drone_route["total_volume"]
                wave_has_assignments = True
        
        # Priority 2: Assign truck clusters to electric trucks
        for truck_id in available_e_trucks:
            if not remaining_truck_clusters:
                break
                
            truck = vehicles_map[truck_id]
            assigned_nodes, total_weight, total_volume, leftover_clusters = fit_clusters_to_truck_aggressive(
                remaining_truck_clusters, truck, "E", depot_id, matrix, nodes_map
            )
            
            if assigned_nodes:
                route_nodes = [depot_id] + [n["node_id"] for n in assigned_nodes] + [depot_id]
                dist, cost = 0, 0
                
                for j in range(len(route_nodes)-1):
                    d, _, c = matrix[(route_nodes[j], route_nodes[j+1])]["E"]
                    dist += d
                    cost += c
                
                truck_route = {
                    "vehicle_id": truck_id,
                    "node_ids": [n["node_id"] for n in assigned_nodes],
                    "route": route_nodes,
                    "distance": round(dist, 4),
                    "cost": round(cost, 4),
                    "total_weight": round(total_weight, 2),
                    "total_volume": round(total_volume, 2),
                    "capacity_utilization": {
                        "weight_percent": round((total_weight / truck["capacity_kg"]) * 100, 2),
                        "volume_percent": round((total_volume / truck["capacity_cm3"]) * 100, 2)
                    }
                }
                
                wave_routes["trucks"].append(truck_route)
                wave_routes["total_distance"] = round(wave_routes["total_distance"] + dist, 4)
                wave_routes["total_cost"] = round(wave_routes["total_cost"] + cost, 4)
                wave_routes["total_weight"] = round(wave_routes["total_weight"] + total_weight, 2)
                wave_routes["total_volume"] = round(wave_routes["total_volume"] + total_volume, 2)
                
                remaining_truck_clusters = leftover_clusters
                wave_has_assignments = True
        
        # Priority 3: Use fuel trucks for remaining truck clusters
        for truck_id in available_f_trucks:
            if not remaining_truck_clusters:
                break
                
            truck = vehicles_map[truck_id]
            assigned_nodes, total_weight, total_volume, leftover_clusters = fit_clusters_to_truck_aggressive(
                remaining_truck_clusters, truck, "F", depot_id, matrix, nodes_map
            )
            
            if assigned_nodes:
                route_nodes = [depot_id] + [n["node_id"] for n in assigned_nodes] + [depot_id]
                dist, cost = 0, 0
                
                for j in range(len(route_nodes)-1):
                    d, _, c = matrix[(route_nodes[j], route_nodes[j+1])]["F"]
                    dist += d
                    cost += c
                
                truck_route = {
                    "vehicle_id": truck_id,
                    "node_ids": [n["node_id"] for n in assigned_nodes],
                    "route": route_nodes,
                    "distance": round(dist, 4),
                    "cost": round(cost, 4),
                    "total_weight": round(total_weight, 2),
                    "total_volume": round(total_volume, 2),
                    "capacity_utilization": {
                        "weight_percent": round((total_weight / truck["capacity_kg"]) * 100, 2),
                        "volume_percent": round((total_volume / truck["capacity_cm3"]) * 100, 2)
                    }
                }
                
                wave_routes["trucks"].append(truck_route)
                wave_routes["total_distance"] = round(wave_routes["total_distance"] + dist, 4)
                wave_routes["total_cost"] = round(wave_routes["total_cost"] + cost, 4)
                wave_routes["total_weight"] = round(wave_routes["total_weight"] + total_weight, 2)
                wave_routes["total_volume"] = round(wave_routes["total_volume"] + total_volume, 2)
                
                remaining_truck_clusters = leftover_clusters
                wave_has_assignments = True

        # Only add wave to solution if it has assignments
        if wave_has_assignments:
            solution[f"wave_{wave}"] = wave_routes
        
        # Check if this could be the final wave (no more truck clusters and we can assign all remaining drone nodes)
        if not remaining_truck_clusters and remaining_drone_nodes:
            print(f"All truck clusters assigned. Attempting to assign remaining {len(remaining_drone_nodes)} drone-eligible nodes to trucks in current wave.")
            
            # Convert remaining drone nodes to single-node clusters
            drone_node_clusters = [[node] for node in remaining_drone_nodes]
            
            # Try to assign to available trucks in current wave
            available_trucks = available_e_trucks + available_f_trucks
            for truck_id in available_trucks:
                if not drone_node_clusters:
                    break
                
                truck = vehicles_map[truck_id]
                vtype = "E" if truck_id in available_e_trucks else "F"
                
                assigned_nodes, total_weight, total_volume, leftover_clusters = fit_clusters_to_truck_aggressive(
                    drone_node_clusters, truck, vtype, depot_id, matrix, nodes_map
                )
                
                if assigned_nodes:
                    route_nodes = [depot_id] + [n["node_id"] for n in assigned_nodes] + [depot_id]
                    dist, cost = 0, 0
                    
                    for j in range(len(route_nodes)-1):
                        d, _, c = matrix[(route_nodes[j], route_nodes[j+1])][vtype]
                        dist += d
                        cost += c
                    
                    truck_route = {
                        "vehicle_id": truck_id,
                        "node_ids": [n["node_id"] for n in assigned_nodes],
                        "route": route_nodes,
                        "distance": round(dist, 4),
                        "cost": round(cost, 4),
                        "total_weight": round(total_weight, 2),
                        "total_volume": round(total_volume, 2),
                        "capacity_utilization": {
                            "weight_percent": round((total_weight / truck["capacity_kg"]) * 100, 2),
                            "volume_percent": round((total_volume / truck["capacity_cm3"]) * 100, 2)
                        }
                    }
                    
                    # Add to current wave
                    wave_key = f"wave_{wave}"
                    if wave_key not in solution:
                        solution[wave_key] = {"drones": [], "trucks": [], "total_distance": 0, "total_cost": 0, "total_weight": 0, "total_volume": 0}
                        wave_has_assignments = True
                    
                    solution[wave_key]["trucks"].append(truck_route)
                    solution[wave_key]["total_distance"] = round(solution[wave_key]["total_distance"] + dist, 4)
                    solution[wave_key]["total_cost"] = round(solution[wave_key]["total_cost"] + cost, 4)
                    solution[wave_key]["total_weight"] = round(solution[wave_key]["total_weight"] + total_weight, 2)
                    solution[wave_key]["total_volume"] = round(solution[wave_key]["total_volume"] + total_volume, 2)
                    
                    drone_node_clusters = leftover_clusters
                    wave_has_assignments = True
            
            remaining_drone_nodes = []
            for cluster in drone_node_clusters:
                remaining_drone_nodes.extend(cluster)
        
        # Break if no more nodes to assign
        if not remaining_drone_nodes and not remaining_truck_clusters:
            break
            
        # Break if reached max waves
        if wave == max_waves:
            print(f"Safety break reached. Remaining drone nodes: {len(remaining_drone_nodes)}, Remaining truck clusters: {len(remaining_truck_clusters)}")
            break
            
        wave += 1

    # Add unassigned nodes info if any remain
    unassigned_nodes = []
    if remaining_drone_nodes:
        unassigned_nodes.extend([n["node_id"] for n in remaining_drone_nodes])
    if remaining_truck_clusters:
        for cluster in remaining_truck_clusters:
            unassigned_nodes.extend([n["node_id"] for n in cluster])
    
    if unassigned_nodes:
        solution["unassigned_nodes"] = unassigned_nodes

    # Add comprehensive summary
    summary = {
        "total_waves": len([k for k in solution.keys() if k.startswith("wave_")]),
        "total_nodes_assigned": 0,
        "total_drone_assignments": 0,
        "total_truck_assignments": 0,
        "total_distance": 0,
        "total_cost": 0,
        "total_weight": 0,
        "total_volume": 0,
        "wave_breakdown": {}
    }
    
    for wave_key, wave_data in solution.items():
        if wave_key.startswith("wave_"):
            wave_num = wave_key
            drone_count = len(wave_data["drones"])
            truck_count = len(wave_data["trucks"])
            nodes_in_wave = 0
            
            for drone_route in wave_data["drones"]:
                nodes_in_wave += len(drone_route["node_ids"])
            
            for truck_route in wave_data["trucks"]:
                nodes_in_wave += len(truck_route["node_ids"])
            
            summary["wave_breakdown"][wave_num] = {
                "nodes_assigned": nodes_in_wave,
                "drone_routes": drone_count,
                "truck_routes": truck_count,
                "total_distance": wave_data["total_distance"],
                "total_cost": wave_data["total_cost"],
                "total_weight": wave_data["total_weight"],
                "total_volume": wave_data["total_volume"]
            }
            
            summary["total_nodes_assigned"] += nodes_in_wave
            summary["total_drone_assignments"] += drone_count
            summary["total_truck_assignments"] += truck_count
            summary["total_distance"] += wave_data["total_distance"]
            summary["total_cost"] += wave_data["total_cost"]
            summary["total_weight"] += wave_data["total_weight"]
            summary["total_volume"] += wave_data["total_volume"]
    
    # Add efficiency metrics
    summary["efficiency_metrics"] = {
        "average_cost_per_node": round(summary["total_cost"] / max(1, summary["total_nodes_assigned"]), 4),
        "average_distance_per_node": round(summary["total_distance"] / max(1, summary["total_nodes_assigned"]), 4)
    }
    
    if unassigned_nodes:
        summary["unassigned_nodes_count"] = len(unassigned_nodes)
        summary["assignment_success_rate"] = round((summary["total_nodes_assigned"] / 
                                                  (summary["total_nodes_assigned"] + len(unassigned_nodes))) * 100, 2)
    else:
        summary["unassigned_nodes_count"] = 0
        summary["assignment_success_rate"] = 100.0
    
    solution["summary"] = summary
    
    return solution