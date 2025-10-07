import ast
import json
import os
from ..solver import preprocess as sp

def create_distance_matrix(matrix_rows):
    """
    Refined function to process the vehicle_matrix data.
    It converts the string representation of the distance tuple (e.g., '(124.5,)')
    into a usable float.
    """
    dist_matrix = {}
    for row in matrix_rows:
        origin = row["origin_id"]
        dest = row["dest_id"]
        
        # 1. Get the distance value, which is likely a string like '(124.5,)'
        distance_str = row["distance"]
        
        try:
            # 2. Safely evaluate the string to get a Python tuple, e.g., (124.5,)
            distance_tuple = ast.literal_eval(distance_str)
            
            # 3. Extract the first number from the tuple
            distance = float(distance_tuple[0])
            
            # 4. Add the entry to our dictionary
            dist_matrix[(origin, dest)] = distance
            
        except (ValueError, SyntaxError):
            print(f"Warning: Could not parse distance for ({origin}, {dest}): {distance_str}")
            
    return dist_matrix

def preprocess_matrix(matrix_rows):
    """
    Converts the raw vehicle_matrix_rows into a nested dictionary for easy lookups:
    matrix[(origin, dest)][v_type] = (distance, duration, cost)
    """
    matrix = {}
    for row in matrix_rows:
        origin, dest = row["origin_id"], row["dest_id"]
        
        # Safely parse the string tuples into actual Python tuples
        vtypes = ast.literal_eval(row["vehicle_type"])
        dist_tuple = ast.literal_eval(row["distance"])
        dur_tuple = ast.literal_eval(row["duration"])
        cost_tuple = ast.literal_eval(row["total_cost"])

        # Create the nested dictionary structure
        if (origin, dest) not in matrix:
            matrix[(origin, dest)] = {}

        # Populate the matrix for each vehicle type
        for i, v_type in enumerate(vtypes):
            matrix[(origin, dest)][v_type] = (dist_tuple[i], dur_tuple[i], cost_tuple[i])
            
    return matrix

async def get_data():
    nodes, vehicles, vehicle_matrix_rows = await sp.fetch_data()
    DIST = create_distance_matrix(vehicle_matrix_rows)
    matrix = preprocess_matrix(vehicle_matrix_rows)
    nodes_map = {node['node_id']: node for node in nodes}
    vehicles_map = {vehicle['vehicle_id']: vehicle for vehicle in vehicles}
    return nodes, vehicles, vehicle_matrix_rows, DIST, matrix, nodes_map, vehicles_map

def load_initial_data():
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'initial_solution.json')
    with open(file_path, 'r') as f:
        data = json.load(f)
    wave_data = {}
    for wave_key, wave_value in data.items():
        if wave_key.startswith('wave_'):
            drones = [
                {'route': drone['route']}
                for drone in wave_value.get('drones', [])
            ]
            trucks = [
                {'route': truck['route']}
                for truck in wave_value.get('trucks', [])
            ]
            wave_data[wave_key] = {
                'drones': drones,
                'trucks': trucks
            }
    summary_info = data['summary']
    return wave_data, summary_info, data

class TspState:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def __repr__(self):
        return f"TspState(nodes={self.nodes}, edges={self.edges})"

def create_initial_routes(data, depot_id='depot'):
    initial_routes = {}
    for wave_value in data.values():
        if not isinstance(wave_value, dict): continue
        all_vehicles = wave_value.get('drones', []) + wave_value.get('trucks', [])
        for vehicle_route in all_vehicles:
            vehicle_id = vehicle_route['vehicle_id']
            route_nodes = vehicle_route['node_ids']
            full_route_list = [depot_id] + route_nodes + [depot_id]
            edges = {start: end for start, end in zip(full_route_list, full_route_list[1:])}
            initial_routes[vehicle_id] = TspState(route_nodes, edges)
    return initial_routes
