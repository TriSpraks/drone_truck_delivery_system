import copy
import json
import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ALNS.alns import ALNS
from ALNS.alns.accept import SimulatedAnnealing
from ALNS.alns.select import RouletteWheel
from ALNS.alns.stop import MaxRuntime
import backend.solution.preprocess as preprocess
from backend.solution.preprocess import TspState

class SolutionState:
    """
    Represents a complete solution. It now holds all required data.
    """
    def __init__(self, routes: dict, nodes_map: dict, vehicles_map: dict, matrix: dict, unassigned: list = None):
        self.routes = routes
        self.unassigned = unassigned if unassigned is not None else []
        
        # Store data maps directly in the state
        self.nodes_map = nodes_map
        self.vehicles_map = vehicles_map
        self.matrix = matrix

    def copy(self):
        # The copy must also carry over the data maps
        return SolutionState(copy.deepcopy(self.routes), self.nodes_map, self.vehicles_map, self.matrix, self.unassigned[:])
    
    def objective(self):
        """
        Calculates the total cost of all routes in the current solution.
        """
        total_cost = 0
        
        for vehicle_id, route_state in self.routes.items():
            if 'Drone' in vehicle_id: v_type = 'D'
            elif 'Fuel' in vehicle_id: v_type = 'F'
            else: v_type = 'E'
            
            full_route = ['depot'] + route_state.nodes + ['depot']
            
            for i in range(len(full_route) - 1):
                origin, dest = full_route[i], full_route[i+1]
                # Accesses the matrix stored in 'self'
                total_cost += self.matrix.get((origin, dest), {}).get(v_type, (0, 0, float('inf')))[2]
                
        return total_cost

    def __repr__(self):
        routes_str = "\n".join([f"  - {v_id}: {r.nodes}" for v_id, r in self.routes.items()])
        return f"SolutionState:\n{routes_str}\n  Unassigned: {self.unassigned}"

def run_alns(initial_solution, seed=45):
    random_state = np.random.RandomState(seed)
    alns = ALNS(random_state)
    import backend.solution.destroy as destroy
    import backend.solution.repair as repair
    alns.add_destroy_operator(destroy.random_removal)
    alns.add_destroy_operator(destroy.cluster_removal)
    alns.add_destroy_operator(destroy.worst_removal)
    alns.add_destroy_operator(destroy.shaw_removal)
    alns.add_destroy_operator(destroy.worst_drone_removal)
    alns.add_repair_operator(repair.greedy_truck_first_repair)
    alns.add_repair_operator(repair.best_insertion_repair)
    alns.add_repair_operator(repair.regret_insertion_repair)
    accept = SimulatedAnnealing.autofit(initial_solution.objective(), 0.05, 0.8, 1000)
    select = RouletteWheel([3, 2, 1, 0.5], decay=0.8, num_destroy=5, num_repair=3)
    stop = MaxRuntime(20)
    result = alns.iterate(initial_solution, select, accept, stop)
    return result

def optimize_all_waves(data, nodes_map, vehicles_map, matrix, seed=45):
    """
    Optimizes all waves in the data using ALNS.
    """
    all_best_solutions = {}
    total_optimized_cost = 0
    initial_total_cost = 0

    wave_keys = sorted([key for key in data if key.startswith('wave_')])

    for wave_key in wave_keys:
        print(f"\n==================== Optimizing {wave_key.upper()} ====================")
        wave_value = data[wave_key]

        initial_routes_for_wave = {}
        all_vehicles_in_wave = wave_value.get('drones', []) + wave_value.get('trucks', [])

        for vehicle_route in all_vehicles_in_wave:
            vehicle_id = vehicle_route['vehicle_id']
            route_nodes = vehicle_route['node_ids']
            full_route_list = ['depot'] + route_nodes + ['depot']
            edges = {start: end for start, end in zip(full_route_list, full_route_list[1:])}
            initial_routes_for_wave[vehicle_id] = TspState(route_nodes, edges)

        initial_solution_for_wave = SolutionState(routes=initial_routes_for_wave,
                                                  nodes_map=nodes_map,
                                                  vehicles_map=vehicles_map,
                                                  matrix=matrix)

        initial_objective = initial_solution_for_wave.objective()
        initial_total_cost += initial_objective
        print(f"Initial objective for {wave_key}: {initial_objective:.2f}")

        result = run_alns(initial_solution_for_wave, seed)
        best_solution_for_wave = result.best_state
        best_objective_for_wave = best_solution_for_wave.objective()

        all_best_solutions[wave_key] = best_solution_for_wave
        total_optimized_cost += best_objective_for_wave

        print(f"Optimized objective for {wave_key}: {best_objective_for_wave:.2f}")
        print(f"Improvement: {initial_objective - best_objective_for_wave:.2f}")

    print("\n\n==================== FINAL OPTIMIZED RESULTS ====================")
    print(f"Initial Combined Cost (All Waves): {initial_total_cost:.2f}")
    print(f"Optimized Combined Cost (All Waves): {total_optimized_cost:.2f}")
    print(f"Total Improvement: {initial_total_cost - total_optimized_cost:.2f}")

    for wave_key, solution in all_best_solutions.items():
        print(f"\n--- Best Solution for {wave_key.upper()} ---")
        print(solution)

    return all_best_solutions

async def generate_solution():
    """
    Main function to generate optimized solutions.
    Fetches data, loads initial solution, and optimizes all waves.
    Returns solution in the same format as initial_solution.json
    """
    # Fetch data from database
    nodes, vehicles, vehicle_matrix_rows, DIST, matrix, nodes_map, vehicles_map = await preprocess.get_data()

    # Load initial solution data
    wave_data, summary_info, data = preprocess.load_initial_data()

    # Optimize all waves using ALNS
    optimized_solutions = optimize_all_waves(data, nodes_map, vehicles_map, matrix)

    # Convert optimized solutions to the same format as initial_solution.json
    formatted_solution = {}

    for wave_key, solution_state in optimized_solutions.items():
        wave_routes = {"drones": [], "trucks": [], "total_distance": 0, "total_cost": 0, "total_weight": 0, "total_volume": 0}

        for vehicle_id, route_state in solution_state.routes.items():
            node_ids = route_state.nodes
            route = ['depot'] + node_ids + ['depot']

            # Determine vehicle type
            if 'Drone' in vehicle_id:
                v_type = 'D'
                vehicle_list = wave_routes["drones"]
            elif 'Fuel' in vehicle_id:
                v_type = 'F'
                vehicle_list = wave_routes["trucks"]
            else:
                v_type = 'E'
                vehicle_list = wave_routes["trucks"]

            # Calculate distance, cost, weight, volume
            dist = 0
            cost = 0
            total_weight = 0
            total_volume = 0

            for i in range(len(route) - 1):
                origin, dest = route[i], route[i+1]
                d, dur, c = matrix.get((origin, dest), {}).get(v_type, (0, 0, 0))
                dist += d
                cost += c

            for node_id in node_ids:
                total_weight += nodes_map[node_id]['weight']
                total_volume += nodes_map[node_id]['volume']

            vehicle_route = {
                "vehicle_id": vehicle_id,
                "node_ids": [str(n).strip("'") if str(n).startswith("np.str_") else str(n) for n in node_ids],
                "route": ['depot'] + [str(n).strip("'") if str(n).startswith("np.str_") else str(n) for n in node_ids] + ['depot'],
                "distance": round(dist, 4),
                "cost": round(cost, 4),
                "total_weight": round(total_weight, 2),
                "total_volume": round(total_volume, 2)
            }

            if v_type != 'D':  # Add capacity utilization for trucks
                vehicle = vehicles_map[vehicle_id]
                vehicle_route["capacity_utilization"] = {
                    "weight_percent": round((total_weight / vehicle["capacity_kg"]) * 100, 2),
                    "volume_percent": round((total_volume / vehicle["capacity_cm3"]) * 100, 2)
                }

            vehicle_list.append(vehicle_route)
            wave_routes["total_distance"] += vehicle_route["distance"]
            wave_routes["total_cost"] += vehicle_route["cost"]
            wave_routes["total_weight"] += vehicle_route["total_weight"]
            wave_routes["total_volume"] += vehicle_route["total_volume"]

        formatted_solution[wave_key] = wave_routes

    # Add unassigned nodes if any
    all_unassigned = []
    for solution_state in optimized_solutions.values():
        all_unassigned.extend(solution_state.unassigned)
    if all_unassigned:
        formatted_solution["unassigned_nodes"] = all_unassigned

    # Add summary (similar to initial solution)
    summary = {
        "total_waves": len([k for k in formatted_solution.keys() if k.startswith("wave_")]),
        "total_nodes_assigned": 0,
        "total_drone_assignments": 0,
        "total_truck_assignments": 0,
        "total_distance": 0,
        "total_cost": 0,
        "total_weight": 0,
        "total_volume": 0,
        "wave_breakdown": {}
    }

    for wave_key, wave_data in formatted_solution.items():
        if wave_key.startswith("wave_"):
            drone_count = len(wave_data["drones"])
            truck_count = len(wave_data["trucks"])
            nodes_in_wave = 0

            for drone_route in wave_data["drones"]:
                nodes_in_wave += len(drone_route["node_ids"])

            for truck_route in wave_data["trucks"]:
                nodes_in_wave += len(truck_route["node_ids"])

            summary["wave_breakdown"][wave_key] = {
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

    if all_unassigned:
        summary["unassigned_nodes_count"] = len(all_unassigned)
        summary["assignment_success_rate"] = round((summary["total_nodes_assigned"] /
                                                  (summary["total_nodes_assigned"] + len(all_unassigned))) * 100, 2)
    else:
        summary["unassigned_nodes_count"] = 0
        summary["assignment_success_rate"] = 100.0

    formatted_solution["summary"] = summary

    return formatted_solution
