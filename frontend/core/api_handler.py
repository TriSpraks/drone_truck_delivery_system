"""
Application configuration settings
"""

# Dark theme stylesheet
DARK_STYLE = """
QMainWindow {
    background-color: #1a1a1a;
    color: #ffffff;
}

QWidget {
    background-color: #1a1a1a;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QFrame {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 8px;
}

QPushButton {
    background-color: #ff6b35;
    border: none;
    padding: 12px 20px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 14px;
    color: white;
}

QPushButton:hover {
    background-color: #e55a2e;
}

QPushButton:pressed {
    background-color: #cc4e26;
}

QPushButton:checked {
    background-color: #ff8c42;
}

QLabel {
    color: #ffffff;
    font-size: 14px;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #404040;
    border-radius: 8px;
    margin-top: 1ex;
    padding-top: 10px;
    background-color: #2d2d2d;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #ff6b35;
}

QScrollArea {
    border: none;
    background-color: #2d2d2d;
}

QListWidget {
    background-color: #333333;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 5px;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #404040;
}

QListWidget::item:selected {
    background-color: #ff6b35;
}

QProgressBar {
    border: 2px solid #404040;
    border-radius: 5px;
    text-align: center;
    background-color: #333333;
}

QProgressBar::chunk {
    background-color: #ff6b35;
    border-radius: 3px;
}

QToolBar {
    background-color: #2d2d2d;
    border: none;
    color: #ffffff;
}

QAction {
    color: #ffffff;
    padding: 8px;
}

QSpinBox {
    background-color: #333333;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 8px;
    font-size: 14px;
    color: #ffffff;
}

QSpinBox:focus {
    border: 2px solid #ff6b35;
}

QTextEdit {
    background-color: #333333;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 8px;
    font-size: 12px;
}

QMessageBox {
    background-color: #2d2d2d;
    color: #ffffff;
}

QPushButton:disabled {
    background-color: #666666;
    color: #999999;
"""

# Default configuration values
DEFAULT_DEPOT_COORDS = [12.8500, 74.9200]  # Default Mangaluru
DEFAULT_CUSTOMER_COUNT = 5
MAP_CENTER = [20.5937, 78.9629]  # Center of India
MAP_ZOOM = 5  # Zoom level to show entire India

# Vehicle configuration
DEFAULT_WAVES = [
    {"num_drones": 3, "num_electric_trucks": 10, "num_fuel_trucks": 2},
    {"num_drones": 2, "num_electric_trucks": 4, "num_fuel_trucks": 1},
]

PAUSE_BETWEEN_WAVES = 3.0

# Vehicle speeds (km/h)
VEHICLE_SPEEDS = {
    "Drone": 60,
    "Electric Truck": 40,
    "Fuel Truck": 35
}

# Vehicle weight ranges (kg)
VEHICLE_WEIGHTS = {
    "Drone": (1, 5),
    "Electric Truck": (200, 500),
    "Fuel Truck": (300, 700)
}

# Map settings
MAP_UPDATE_INTERVAL = 500  # milliseconds
SOUND_UPDATE_INTERVAL = 1000  # milliseconds

# Delivery point generation settings
DELIVERY_DISTANCE_MIN = 15  # km
DELIVERY_DISTANCE_MAX = 45  # km
MAX_CUSTOMERS = 999
MIN_CUSTOMERS = 1

"""
Road-Following Route Manager - Makes vehicles follow actual roads
Uses multiple strategies: OSRM API, road network simulation, and fallbacks
"""
"""
Road-Following Route Manager - Makes vehicles follow actual roads
Uses multiple strategies: OSRM API, road network simulation, and fallbacks
CORRECTED VERSION - Eliminates code duplication and circular references
"""
import math
import random
import time
import numpy as np
import requests
import webbrowser
from typing import List, Dict, Optional, Tuple
from core.route_plotter import build_map_from_solution, build_node_lookup
from config.app_config import BACKEND_URL  # ensure BACKEND_URL is set like "http://127.0.0.1:8000"
import threading


class BaseRouteManager:
    """Base class with core routing functionality"""
    
    def __init__(self):
        self.route_cache = {}
        self.distance_cache = {}
    
    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371.0  # Earth radius in km
        
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    def _calculate_distance(self, pos1: List[float], pos2: List[float]) -> float:
        """Calculate distance with caching"""
        cache_key = (round(pos1[0], 6), round(pos1[1], 6), round(pos2[0], 6), round(pos2[1], 6))
        
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]
        
        distance = self.haversine(pos1[0], pos1[1], pos2[0], pos2[1])
        
        # Limit cache size
        if len(self.distance_cache) < 10000:
            self.distance_cache[cache_key] = distance
        
        return distance
    
    def _create_drone_route_direct(self, depot: List[float], delivery: List[float]) -> List[List[float]]:
        """Create direct drone route (straight line)"""
        return [depot[:], delivery[:], depot[:]]
    
    def _add_intermediate_points(self, start: List[float], end: List[float], count: int) -> List[List[float]]:
        """Add intermediate waypoints for realistic routing"""
        if count <= 0:
            return []
        
        points = []
        for i in range(1, count + 1):
            t = i / (count + 1)
            
            # Linear interpolation with slight curve
            lat = start[0] + (end[0] - start[0]) * t
            lon = start[1] + (end[1] - start[1]) * t
            
            # Add slight deviation for realism
            deviation = 0.001 * math.sin(math.pi * t)
            lat += deviation * (1 if i % 2 == 0 else -1)
            lon += deviation * 0.5 * (1 if i % 2 == 1 else -1)
            
            points.append([lat, lon])
        
        return points
    
    def _create_realistic_path(self, start: List[float], end: List[float], 
                              intermediate: Optional[List[float]] = None) -> List[List[float]]:
        """Create realistic path between two points"""
        if intermediate:
            path = [start[:]]
            path.extend(self._add_intermediate_points(start, intermediate, 2))
            path.append(intermediate[:])
            path.extend(self._add_intermediate_points(intermediate, end, 2))
            path.append(end[:])
            return path
        else:
            path = [start[:]]
            path.extend(self._add_intermediate_points(start, end, 3))
            path.append(end[:])
            return path


class OptimizedRouteManager(BaseRouteManager):
    """Optimized route manager with batch processing, caching, and parallel requests"""
    
    # Class-level cache and configuration
    _route_cache = {}
    _cache_lock = threading.Lock()
    MAX_WORKERS = 4
    REQUEST_TIMEOUT = 5
    BATCH_SIZE = 10
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def clear_cache(cls):
        """Clear the route cache"""
        with cls._cache_lock:
            cls._route_cache.clear()
    
    @classmethod
    def build_delivery_routes_batch(cls, depot: List[float], delivery_assignments: Dict) -> Dict:
        """Build multiple delivery routes in parallel with optimization"""
        print(f"\n=== OPTIMIZED BATCH ROUTE BUILDING ===")
        print(f"Building routes for {len(delivery_assignments)} vehicles...")
        
        # Separate drone and truck routes
        drone_routes = []
        truck_routes = []
        
        for vehicle_name, assignment in delivery_assignments.items():
            route_request = {
                'vehicle_name': vehicle_name,
                'depot': depot,
                'delivery': assignment['primary_delivery'],
                'all_deliveries': assignment.get('all_deliveries', [assignment['primary_delivery']]),
                'use_drone': assignment['type'] == "Drone"
            }
            
            if assignment['type'] == "Drone":
                drone_routes.append(route_request)
            else:
                truck_routes.append(route_request)
        
        print(f"Route breakdown: {len(drone_routes)} drone routes, {len(truck_routes)} truck routes")
        
        all_routes = {}
        manager = cls()
        
        # Process drone routes instantly
        if drone_routes:
            print("Processing drone routes (instant)...")
            for route_req in drone_routes:
                route = manager._create_drone_route_direct(
                    route_req['depot'], route_req['delivery']
                )
                all_routes[route_req['vehicle_name']] = {
                    "route": route,
                    "all_deliveries": route_req['all_deliveries']
                }
            print(f"✓ Completed {len(drone_routes)} drone routes instantly")
        
        # Process truck routes in parallel
        if truck_routes:
            print(f"Processing {len(truck_routes)} truck routes...")
            truck_results = cls._process_truck_routes_parallel(truck_routes, manager)
            all_routes.update(truck_results)
            print(f"✓ Completed {len(truck_results)} truck routes")
        
        print(f"=== BATCH PROCESSING COMPLETE ===")
        print(f"Total routes built: {len(all_routes)}")
        return all_routes
    
    @classmethod
    def _process_truck_routes_parallel(cls, truck_routes: List[Dict], manager) -> Dict:
        """Process truck routes in parallel with batching"""
        results = {}

        # Process in smaller batches
        for i in range(0, len(truck_routes), cls.BATCH_SIZE):
            batch = truck_routes[i:i + cls.BATCH_SIZE]
            print(f"Processing batch {i//cls.BATCH_SIZE + 1}: {len(batch)} routes")

            with ThreadPoolExecutor(max_workers=cls.MAX_WORKERS) as executor:
                future_to_request = {
                    executor.submit(
                        cls._build_single_route_with_timeout,
                        req['depot'],
                        req['all_deliveries'],
                        manager
                    ): req for req in batch
                }

                for future in as_completed(future_to_request, timeout=60):  # ← 30 second batch timeout  # Increase to 60s
                    request = future_to_request[future]
                    try:
                        route = future.result(timeout=20)  # ← 20 second per-route timeout
                        if route and len(route) >= 2:
                            results[request['vehicle_name']] = {
                                "route": route,
                                "all_deliveries": request['all_deliveries']
                            }
                            print(f"✓ {request['vehicle_name']}: {len(route)} points")
                        else:
                            raise ValueError("Empty route returned")
                    except Exception as e:
                        print(f"✗ Route failed for {request['vehicle_name']}, using fallback")
                        fallback_route = manager._create_realistic_path(
                            request['depot'], request['delivery']
                        )
                        fallback_route.extend(manager._create_realistic_path(
                            request['delivery'], request['depot']
                        )[1:])  # Add return journey
                        results[request['vehicle_name']] = {
                            "route": fallback_route,
                            "all_deliveries": request['all_deliveries']
                        }

        return results
    
    @classmethod
    def _build_single_route_with_timeout(cls, depot: List[float], deliveries: List[List[float]], manager) -> List[List[float]]:
        """Build single route visiting ALL delivery points"""
        if len(deliveries) == 1:
            # Simple single delivery route
            return cls._get_truck_route_with_fallback(
                depot[0], depot[1], 
                deliveries[0][0], deliveries[0][1], 
                manager
            )
        else:
            # Multi-stop route - build path through all deliveries
            route = [depot[:]]
            current_pos = depot

            for delivery in deliveries:
                # Get route segment from current position to next delivery
                segment = cls._get_truck_route_with_fallback(
                    current_pos[0], current_pos[1],
                    delivery[0], delivery[1],
                    manager
                )
                # Add segment (skip first point as it's the current position)
                route.extend(segment[1:])
                current_pos = delivery

            # Return to depot
            return_segment = cls._get_truck_route_with_fallback(
                current_pos[0], current_pos[1],
                depot[0], depot[1],
                manager
            )
            route.extend(return_segment[1:])

            return route
    
    @classmethod
    def _get_truck_route_with_fallback(cls, start_lat: float, start_lon: float, 
                                      end_lat: float, end_lon: float, manager) -> List[List[float]]:
        """Get truck route with API and fallback"""
        cache_key = (start_lat, start_lon, end_lat, end_lon, False)
        
        # Check cache first
        with cls._cache_lock:
            if cache_key in cls._route_cache:
                return cls._route_cache[cache_key][:]
        
        try:
            # Try OSRM API
            route = cls._get_osrm_route_fast(start_lat, start_lon, end_lat, end_lon)
            if route and len(route) >= 2:
                full_route = cls._make_round_trip(route)
                
                # Cache result
                with cls._cache_lock:
                    cls._route_cache[cache_key] = full_route[:]
                
                return full_route
        except Exception as e:
            print(f"API call failed, using fallback: {e}")
        
        # Fallback to algorithmic route
        fallback_route = manager._create_realistic_path([start_lat, start_lon], [end_lat, end_lon])
        
        # Cache fallback
        with cls._cache_lock:
            cls._route_cache[cache_key] = fallback_route[:]
        
        return fallback_route

    @classmethod
    def _get_osrm_route_fast(cls, start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Optional[List[List[float]]]:
        """Fast OSRM API call with timeout"""
        start_coord = f"{start_lon},{start_lat}"
        end_coord = f"{end_lon},{end_lat}"

        url = f"http://router.project-osrm.org/route/v1/driving/{start_coord};{end_coord}"
        params = {
            'overview': 'simplified',
            'geometries': 'geojson',
            'steps': 'false'
        }

        try:
            response = requests.get(url, params=params, timeout=15)  # ← CRITICAL: 5 second timeout

            if response.status_code == 200:
                data = response.json()
                if data.get('routes') and len(data['routes']) > 0:
                    coordinates = data['routes'][0]['geometry']['coordinates']

                    route_points = []
                    for i, coord in enumerate(coordinates):
                        if i % 3 == 0 or i == len(coordinates) - 1:
                            route_points.append([coord[1], coord[0]])

                    if route_points:
                        route_points[0] = [start_lat, start_lon]
                        route_points[-1] = [end_lat, end_lon]

                    print(f"✓ OSRM route: {len(route_points)} points")
                    return route_points
                else:
                    print(f"✗ OSRM no routes found")
            else:
                print(f"✗ OSRM failed: HTTP {response.status_code}")
        except requests.Timeout:
            print(f"✗ OSRM timeout after 5s - using fallback")
            return None  # ← Return None to trigger fallback
        except requests.RequestException as e:
            print(f"✗ OSRM request error: {e}")
            return None
        except Exception as e:
            print(f"✗ OSRM error: {e}")
            return None

        return None
    
    @classmethod
    def _make_round_trip(cls, outbound_route: List[List[float]]) -> List[List[float]]:
        """Convert one-way route to round trip"""
        return_route = outbound_route[:-1]
        return_route.reverse()
        return outbound_route + return_route
    
    # Backward compatibility methods
    @staticmethod
    def build_delivery_route(depot: List[float], delivery: List[float], use_drone: bool = True) -> List[List[float]]:
        """Build single delivery route - backward compatible"""
        manager = OptimizedRouteManager()
        if use_drone:
            return manager._create_drone_route_direct(depot, delivery)
        else:
            return OptimizedRouteManager._get_truck_route_with_fallback(
                depot[0], depot[1], delivery[0], delivery[1], manager
            )


class AlgorithmicRouteManager(BaseRouteManager):
    """Pure algorithmic routing - no API calls"""
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def build_delivery_routes_batch(cls, depot: List[float], delivery_assignments: Dict) -> Dict:
        """Build ALL routes with ZERO API calls"""
        print(f"🚀 ALGORITHMIC ROUTING: {len(delivery_assignments)} vehicles")
        start_time = time.time()
        
        manager = cls()
        
        # Analyze fleet
        fleet_stats = manager._analyze_fleet_fast(delivery_assignments)
        print(f"Fleet: {fleet_stats['drones']} drones, {fleet_stats['trucks']} trucks, {fleet_stats['total_deliveries']} total deliveries")
        
        # Build all routes algorithmically
        all_routes = manager._build_all_routes_algorithmic(depot, delivery_assignments)
        
        build_time = time.time() - start_time
        print(f"✅ Built {len(all_routes)} routes in {build_time:.2f}s ({len(all_routes)/build_time:.0f} routes/sec)")
        print(f"📊 API calls: 0 (100% algorithmic)")
        
        return all_routes
    
    def _analyze_fleet_fast(self, delivery_assignments: Dict) -> Dict:
        """Fast fleet analysis"""
        stats = {'drones': 0, 'trucks': 0, 'total_deliveries': 0}
        
        for assignment in delivery_assignments.values():
            if 'drone' in assignment.get('type', '').lower():
                stats['drones'] += 1
            else:
                stats['trucks'] += 1
            stats['total_deliveries'] += len(assignment.get('all_deliveries', [assignment['primary_delivery']]))
        
        return stats
    
    def _build_all_routes_algorithmic(self, depot: List[float], delivery_assignments: Dict) -> Dict:
        """Build all routes using pure algorithms"""
        
        # Split work by vehicle type
        drones = []
        trucks = []
        
        for name, assignment in delivery_assignments.items():
            if 'drone' in assignment.get('type', '').lower():
                drones.append((name, assignment))
            else:
                trucks.append((name, assignment))
        
        all_routes = {}
        
        # Process drones instantly
        print(f"Processing {len(drones)} drones (instant)...")
        for name, assignment in drones:
            route = self._create_drone_route_direct(depot, assignment['primary_delivery'])
            all_routes[name] = {
                "route": route,
                "all_deliveries": assignment.get('all_deliveries', [assignment['primary_delivery']])
            }
        
        # Process trucks algorithmically
        if trucks:
            print(f"Processing {len(trucks)} trucks (algorithmic TSP)...")
            truck_routes = self._build_truck_routes_algorithmic(depot, trucks)
            all_routes.update(truck_routes)
        
        return all_routes
    
    def _build_truck_routes_algorithmic(self, depot: List[float], trucks: List[Tuple[str, Dict]]) -> Dict:
        """Build truck routes using algorithmic approach"""
        chunk_size = 100
        all_truck_routes = {}
        
        if len(trucks) > chunk_size:
            # Use multiprocessing for large fleets
            with ProcessPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for i in range(0, len(trucks), chunk_size):
                    chunk = trucks[i:i + chunk_size]
                    future = executor.submit(
                        self._process_truck_chunk_algorithmic,
                        chunk, depot
                    )
                    futures.append(future)
                
                # Collect results
                for future in futures:
                    chunk_routes = future.result()
                    all_truck_routes.update(chunk_routes)
        else:
            all_truck_routes = self._process_truck_chunk_algorithmic(trucks, depot)
        
        return all_truck_routes
    
    def _process_truck_chunk_algorithmic(self, truck_chunk: List[Tuple[str, Dict]], depot: List[float]) -> Dict:
        """Process truck chunk with pure algorithmic routing"""
        chunk_routes = {}
        
        for vehicle_name, assignment in truck_chunk:
            deliveries = assignment.get('all_deliveries', [assignment['primary_delivery']])
            vehicle_type = assignment.get('type', 'Truck')
            
            # Limit deliveries based on capacity
            max_capacity = self._get_vehicle_capacity(vehicle_type)
            if len(deliveries) > max_capacity:
                deliveries = deliveries[:max_capacity]
            
            # Create optimized route using TSP
            route = self._create_optimized_route_tsp(depot, deliveries)
            
            chunk_routes[vehicle_name] = {
                "route": route,
                "all_deliveries": assignment.get('all_deliveries', [assignment['primary_delivery']])
            }
        
        return chunk_routes
    
    def _create_optimized_route_tsp(self, depot: List[float], deliveries: List[List[float]]) -> List[List[float]]:
        """Create optimized route using TSP algorithms"""
        if not deliveries:
            return [depot[:], depot[:]]
        
        if len(deliveries) == 1:
            return self._create_realistic_path(depot, deliveries[0])
        
        # Use TSP with 2-opt improvement
        optimized_order = self._solve_tsp_with_2opt(depot, deliveries)
        
        # Build route with realistic waypoints
        route = [depot[:]]
        current_pos = depot
        
        for delivery in optimized_order:
            path_segment = self._create_realistic_path(current_pos, delivery)
            route.extend(path_segment[1:])
            current_pos = delivery
        
        # Return to depot
        return_path = self._create_realistic_path(current_pos, depot)
        route.extend(return_path[1:])
        
        return route
    
    def _solve_tsp_with_2opt(self, depot: List[float], deliveries: List[List[float]]) -> List[List[float]]:
        """Solve TSP using nearest neighbor + 2-opt"""
        if len(deliveries) <= 1:
            return deliveries[:]
        
        route = self._nearest_neighbor_tsp(depot, deliveries)
        
        if len(route) <= 10:
            route = self._two_opt_improvement(route, depot)
        
        return route
    
    def _nearest_neighbor_tsp(self, depot: List[float], deliveries: List[List[float]]) -> List[List[float]]:
        """Solve TSP using nearest neighbor algorithm"""
        route = []
        remaining = deliveries[:]
        current_pos = depot
        
        while remaining:
            nearest_idx = 0
            min_distance = self._calculate_distance(current_pos, remaining[0])
            
            for i, delivery in enumerate(remaining):
                distance = self._calculate_distance(current_pos, delivery)
                if distance < min_distance:
                    min_distance = distance
                    nearest_idx = i
            
            nearest_delivery = remaining.pop(nearest_idx)
            route.append(nearest_delivery)
            current_pos = nearest_delivery
        
        return route
    
    def _two_opt_improvement(self, route: List[List[float]], depot: List[float]) -> List[List[float]]:
        """Improve route using 2-opt local search"""
        if len(route) <= 3:
            return route
        
        best_route = route[:]
        best_distance = self._calculate_route_distance(depot, best_route)
        improved = True
        max_iterations = 10
        iterations = 0
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            for i in range(len(route) - 1):
                for j in range(i + 2, len(route)):
                    new_route = route[:]
                    new_route[i:j] = reversed(new_route[i:j])
                    
                    new_distance = self._calculate_route_distance(depot, new_route)
                    
                    if new_distance < best_distance:
                        best_route = new_route[:]
                        best_distance = new_distance
                        route = new_route[:]
                        improved = True
        
        return best_route
    
    def _calculate_route_distance(self, depot: List[float], route: List[List[float]]) -> float:
        """Calculate total route distance"""
        if not route:
            return 0.0
        
        total_distance = 0.0
        current_pos = depot
        
        for delivery in route:
            total_distance += self._calculate_distance(current_pos, delivery)
            current_pos = delivery
        
        total_distance += self._calculate_distance(current_pos, depot)
        return total_distance
    
    def _get_vehicle_capacity(self, vehicle_type: str) -> int:
        """Get maximum deliveries per vehicle type"""
        capacity_map = {
            'drone': 2,
            'delivery': 6,
            'electric': 8,
            'fuel': 12,
            'truck': 10,
            'van': 6
        }
        
        vehicle_lower = vehicle_type.lower()
        for key, capacity in capacity_map.items():
            if key in vehicle_lower:
                return capacity
        
        return 8  # Default capacity


# Main RouteManager class - uses OptimizedRouteManager by default
class RouteManager(OptimizedRouteManager):
    """Main RouteManager class - backward compatible"""
    
    @staticmethod
    def build_delivery_route(depot: List[float], delivery: List[float], use_drone: bool = True) -> List[List[float]]:
        """Build single delivery route - backward compatible"""
        return OptimizedRouteManager.build_delivery_route(depot, delivery, use_drone)
    
    @staticmethod
    def get_osrm_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> List[List[float]]:
        """Get OSRM route - backward compatible"""
        manager = OptimizedRouteManager()
        route = OptimizedRouteManager._get_osrm_route_fast(start_lat, start_lon, end_lat, end_lon)
        if route:
            return OptimizedRouteManager._make_round_trip(route)
        else:
            return manager._create_realistic_path([start_lat, start_lon], [end_lat, end_lon])


# Test function
def test_unified_routing():
    """Test the unified route managers"""
    print("Testing Unified Route Managers...")
    
    depot = [12.2958, 76.6394]
    delivery_assignments = {}
    
    # Generate test vehicles
    for i in range(10):
        vehicle_type = ["Drone", "Electric Truck", "Fuel Truck"][i % 3]
        
        num_deliveries = random.randint(1, 3)
        deliveries = []
        
        for j in range(num_deliveries):
            lat = depot[0] + random.uniform(-0.05, 0.05)
            lon = depot[1] + random.uniform(-0.05, 0.05)
            deliveries.append([lat, lon])
        
        delivery_assignments[f"{vehicle_type.replace(' ', '')}_{i}"] = {
            "type": vehicle_type,
            "primary_delivery": deliveries[0],
            "all_deliveries": deliveries
        }
    
    print(f"Generated {len(delivery_assignments)} vehicles")
    
    # Test OptimizedRouteManager
    print("\n--- Testing OptimizedRouteManager ---")
    start_time = time.time()
    routes_optimized = OptimizedRouteManager.build_delivery_routes_batch(depot, delivery_assignments)
    time_optimized = time.time() - start_time
    print(f"OptimizedRouteManager: {len(routes_optimized)} routes in {time_optimized:.2f}s")
    
    # Test AlgorithmicRouteManager
    print("\n--- Testing AlgorithmicRouteManager ---")
    start_time = time.time()
    routes_algorithmic = AlgorithmicRouteManager.build_delivery_routes_batch(depot, delivery_assignments)
    time_algorithmic = time.time() - start_time
    print(f"AlgorithmicRouteManager: {len(routes_algorithmic)} routes in {time_algorithmic:.2f}s")
    
    # Test backward compatibility
    print("\n--- Testing Backward Compatibility ---")
    single_route = RouteManager.build_delivery_route(depot, [12.3, 76.7], use_drone=False)
    print(f"Single route has {len(single_route)} waypoints")
    
    print("\nAll tests completed successfully!")


def fetch_solution_and_render_map(output_path: str = "routes_map.html", open_in_browser: bool = True) -> str:
    """
    Fetch solution and nodes from backend, build map via route_plotter and save HTML file.
    Returns the output file path.
    """
    sol_resp = requests.get(f"{BACKEND_URL}/api/initial_solution", timeout=15)
    sol_resp.raise_for_status()
    solution = sol_resp.json()

    nodes_resp = requests.get(f"{BACKEND_URL}/api/nodes", timeout=15)
    nodes_resp.raise_for_status()
    nodes = nodes_resp.json()

    nodes_lookup = build_node_lookup(nodes)
    m = build_map_from_solution(solution, nodes_lookup)
    m.save(output_path)

    if open_in_browser:
        webbrowser.open(output_path)
    return output_path


if __name__ == "__main__":
    test_unified_routing()