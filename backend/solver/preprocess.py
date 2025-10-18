import ast
from ..utils import db_handler

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

def calculate_route_distance(route, matrix, vtype):
    """Calculate total distance for a route"""
    total_distance = 0
    for i in range(len(route) - 1):
        if (route[i], route[i+1]) in matrix and vtype in matrix[(route[i], route[i+1])]:
            total_distance += matrix[(route[i], route[i+1])][vtype][0]
        else:
            return float('inf')  # Route not feasible
    return total_distance

def check_range_constraint(route, matrix, vtype, vehicle_range):
    """Check if route respects vehicle range constraint"""
    total_distance = calculate_route_distance(route, matrix, vtype)
    return total_distance <= vehicle_range
