import copy
import json
import numpy as np
import os
import sys

# Add project directories to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ALNS library imports
from ALNS.alns import ALNS
from ALNS.alns.accept import SimulatedAnnealing
from ALNS.alns.select import RouletteWheel
from ALNS.alns.stop import MaxRuntime

# Local module imports
from . import preprocess
from .preprocess import TspState
from . import destroy
from . import repair


class SolutionState:
    """
    Represents a complete solution, holding routes, unassigned nodes,
    and all necessary data maps for the ALNS operators.
    """
    def __init__(self, routes: dict, nodes_map: dict, vehicles_map: dict, matrix: dict, unassigned: list = None):
        self.routes = routes
        self.unassigned = unassigned if unassigned is not None else []
        
        # Store data maps directly in the state for easy access by operators
        self.nodes_map = nodes_map
        self.vehicles_map = vehicles_map
        self.matrix = matrix

    def copy(self):
        """
        Creates a deep copy of the solution state, ensuring that
        modifications to a new state do not affect the original.
        """
        return SolutionState(copy.deepcopy(self.routes), 
                             self.nodes_map, 
                             self.vehicles_map, 
                             self.matrix, 
                             self.unassigned[:])
    
    def objective(self):
        """
        Calculates the total cost of all routes in the current solution,
        PLUS a large penalty for any customers that are not assigned to a route.
        """
        total_cost = 0
        
        for vehicle_id, route_state in self.routes.items():
            if 'Drone' in vehicle_id: v_type = 'D'
            elif 'Fuel' in vehicle_id: v_type = 'F'
            else: v_type = 'E'
            
            full_route = ['depot'] + route_state.nodes + ['depot']
            
            for i in range(len(full_route) - 1):
                origin, dest = full_route[i], full_route[i+1]
                total_cost += self.matrix.get((origin, dest), {}).get(v_type, (0, 0, float('inf')))[2]
        
        # Add a large penalty for each unassigned customer to ensure all are served.
        UNASSIGNED_PENALTY = 10000
        total_cost += len(self.unassigned) * UNASSIGNED_PENALTY
                
        return total_cost

    def __repr__(self):
        """
        Provides a clean string representation of the solution for logging,
        ensuring all node IDs are displayed as standard strings.
        """
        routes_str = "\n".join([f"  - {v_id}: {[str(n) for n in r.nodes]}" 
                                for v_id, r in self.routes.items()])
        unassigned_str = [str(n) for n in self.unassigned]
        return f"SolutionState:\n{routes_str}\n  Unassigned: {unassigned_str}"


def run_alns(initial_solution, seed=45):
    """
    Configures and runs the ALNS algorithm for a given initial solution.
    """
    random_state = np.random.RandomState(seed)
    alns = ALNS(random_state)
    
    alns.add_destroy_operator(destroy.random_removal)
    alns.add_destroy_operator(destroy.cluster_removal)
    alns.add_destroy_operator(destroy.worst_removal)
    alns.add_destroy_operator(destroy.shaw_removal)
    alns.add_destroy_operator(destroy.worst_drone_removal)
    
    alns.add_repair_operator(repair.greedy_truck_first_repair)
    alns.add_repair_operator(repair.best_insertion_repair)
    alns.add_repair_operator(repair.regret_insertion_repair)
    
    accept = SimulatedAnnealing.autofit(initial_solution.objective(), 
                                         0.05, 
                                         0.001,
                                         1000)
    
    select = RouletteWheel([3, 2, 1, 0.5], decay=0.8, num_destroy=5, num_repair=3)
    stop = MaxRuntime(60)
    
    result = alns.iterate(initial_solution, select, accept, stop)
    
    return result


def optimize_all_waves(data, nodes_map, vehicles_map, matrix, seed=45):
    """
    Iterates through all waves from the initial solution data and optimizes each one.
    Skips optimization for trivial waves and sanitizes the final result for type consistency.
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
        
        total_customers_in_wave = 0
        for vehicle_route in all_vehicles_in_wave:
            total_customers_in_wave += len(vehicle_route.get('node_ids', []))
            
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

        MIN_CUSTOMERS_FOR_ALNS = 3
        if total_customers_in_wave < MIN_CUSTOMERS_FOR_ALNS:
            print(f"Skipping ALNS for {wave_key} (only {total_customers_in_wave} customers). Using initial solution.")
            best_solution_for_wave = initial_solution_for_wave
        else:
            result = run_alns(initial_solution_for_wave, seed)
            best_solution_for_wave = result.best_state

        # --- THIS IS THE CRITICAL FIX ---
        # Sanitize numpy string types from ALNS result back to native Python strings
        # to ensure type consistency throughout the rest of the program.
        for route_state in best_solution_for_wave.routes.values():
            route_state.nodes = [str(node) for node in route_state.nodes]
        
        best_solution_for_wave.unassigned = [str(node) for node in best_solution_for_wave.unassigned]
        # --- END OF FIX ---

        # Calculate the final objective cost WITHOUT the penalty for reporting
        final_objective_without_penalty = 0
        for route_state in best_solution_for_wave.routes.values():
            if 'Drone' in vehicle_id: v_type = 'D'
            elif 'Fuel' in vehicle_id: v_type = 'F'
            else: v_type = 'E'
            full_route = ['depot'] + route_state.nodes + ['depot']
            for i in range(len(full_route) - 1):
                final_objective_without_penalty += best_solution_for_wave.matrix.get((full_route[i], full_route[i+1]), {}).get(v_type, (0, 0, 0))[2]

        all_best_solutions[wave_key] = best_solution_for_wave
        total_optimized_cost += final_objective_without_penalty

        print(f"Optimized objective for {wave_key}: {final_objective_without_penalty:.2f}")
        # Use the initial objective (which also had no penalty) for a fair comparison
        initial_objective_without_penalty = initial_solution_for_wave.objective()
        print(f"Improvement: {initial_objective_without_penalty - final_objective_without_penalty:.2f}")

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
    Main entry point function to generate the complete, optimized solution.
    """
    nodes, vehicles, vehicle_matrix_rows, DIST, matrix, nodes_map, vehicles_map = await preprocess.get_data()
    wave_data, summary_info, data = preprocess.load_initial_data()
    optimized_solutions = optimize_all_waves(data, nodes_map, vehicles_map, matrix)
    
    # Format the final optimized solution into the required JSON structure
    formatted_solution = {}
    for wave_key, solution_state in optimized_solutions.items():
        wave_routes = {"drones": [], "trucks": [], "total_distance": 0, "total_cost": 0, "total_weight": 0, "total_volume": 0}

        for vehicle_id, route_state in solution_state.routes.items():
            node_ids = route_state.nodes
            route = ['depot'] + node_ids + ['depot']

            if 'Drone' in vehicle_id:
                v_type = 'D'
                vehicle_list = wave_routes["drones"]
            elif 'Fuel' in vehicle_id:
                v_type = 'F'
                vehicle_list = wave_routes["trucks"]
            else:
                v_type = 'E'
                vehicle_list = wave_routes["trucks"]

            dist, cost, total_weight, total_volume = 0, 0, 0, 0
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
                "node_ids": node_ids, # Already sanitized to strings
                "route": route,      # Already sanitized to strings
                "distance": round(dist, 4),
                "cost": round(cost, 4),
                "total_weight": round(total_weight, 2),
                "total_volume": round(total_volume, 2)
            }
            if v_type != 'D':
                vehicle = vehicles_map[vehicle_id]
                vehicle_route["capacity_utilization"] = {
                    "weight_percent": round((total_weight / vehicle["capacity_kg"]) * 100, 2) if vehicle["capacity_kg"] > 0 else 0,
                    "volume_percent": round((total_volume / vehicle["capacity_cm3"]) * 100, 2) if vehicle["capacity_cm3"] > 0 else 0
                }
            vehicle_list.append(vehicle_route)
            wave_routes["total_distance"] += vehicle_route["distance"]
            wave_routes["total_cost"] += vehicle_route["cost"]
            wave_routes["total_weight"] += vehicle_route["total_weight"]
            wave_routes["total_volume"] += vehicle_route["total_volume"]
        formatted_solution[wave_key] = wave_routes

    all_unassigned = [node for s in optimized_solutions.values() for node in s.unassigned]
    if all_unassigned:
        formatted_solution["unassigned_nodes"] = all_unassigned

    # Re-calculate the summary for the final solution
    summary = {
        "total_waves": len([k for k in formatted_solution.keys() if k.startswith("wave_")]),
        "total_nodes_assigned": 0, "total_drone_assignments": 0, "total_truck_assignments": 0,
        "total_distance": 0, "total_cost": 0, "total_weight": 0, "total_volume": 0,
        "wave_breakdown": {}
    }
    for wave_key, wave_data in formatted_solution.items():
        if not wave_key.startswith("wave_"): continue
        
        nodes_in_wave = sum(len(r["node_ids"]) for r in wave_data.get("drones", [])) + \
                        sum(len(r["node_ids"]) for r in wave_data.get("trucks", []))
        
        summary["wave_breakdown"][wave_key] = {
            "nodes_assigned": nodes_in_wave,
            "drone_routes": len(wave_data.get("drones", [])),
            "truck_routes": len(wave_data.get("trucks", [])),
            "total_distance": wave_data["total_distance"],
            "total_cost": wave_data["total_cost"],
            "total_weight": wave_data["total_weight"],
            "total_volume": wave_data["total_volume"]
        }
        
        summary["total_nodes_assigned"] += nodes_in_wave
        summary["total_drone_assignments"] += len(wave_data.get("drones", []))
        summary["total_truck_assignments"] += len(wave_data.get("trucks", []))
        summary["total_distance"] += wave_data["total_distance"]
        summary["total_cost"] += wave_data["total_cost"]
        summary["total_weight"] += wave_data["total_weight"]
        summary["total_volume"] += wave_data["total_volume"]

    summary["efficiency_metrics"] = {
        "average_cost_per_node": round(summary["total_cost"] / max(1, summary["total_nodes_assigned"]), 4),
        "average_distance_per_node": round(summary["total_distance"] / max(1, summary["total_nodes_assigned"]), 4)
    }
    summary["unassigned_nodes_count"] = len(all_unassigned)
    total_nodes = summary["total_nodes_assigned"] + len(all_unassigned)
    summary["assignment_success_rate"] = round((summary["total_nodes_assigned"] / max(1, total_nodes)) * 100, 2)
    formatted_solution["summary"] = summary

    return formatted_solution