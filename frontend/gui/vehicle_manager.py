"""
Vehicle management module - FIXED to preserve node_id information
Handles vehicle movement, status updates, and fleet operations
"""
import math
import time
from typing import Dict, List, Optional, Tuple
from core.api_handler import OptimizedRouteManager
from core.data_manager import VehicleData


class VehicleManager:
    """Manages vehicle fleet operations"""
    
    def __init__(self, depot_coords: List[float]):
        """
        Initialize vehicle manager
        
        Args:
            depot_coords: [latitude, longitude] of depot
        """
        self.depot_coords = depot_coords
        self.vehicles = {}
        self.vehicles_started = False
        self.vehicles_paused = False
        self.wave_running = False
        self.wave_completed = False
        self.wave_start_time = 0.0
        
    def create_assignments_from_waves(self, waves_data: List[Dict], 
                                     customer_nodes: List[Dict]) -> Dict:
        """
        Create vehicle assignments from backend's wave solution
        PRESERVES node_id information for correct map display
        
        Args:
            waves_data: List of wave information from backend
            customer_nodes: List of customer node dictionaries
            
        Returns:
            Dictionary of vehicle assignments
        """
        if not waves_data:
            print("⚠️ No wave data available")
            return {}
        
        # Use first wave
        current_wave = waves_data[0] if waves_data else None
        if not current_wave:
            print("⚠️ No valid wave found")
            return {}
        
        print(f"\n=== USING BACKEND WAVE SOLUTION ===")
        print(f"Wave: {current_wave['wave_number']}")
        print(f"Drones: {current_wave['total_drones']}, Trucks: {current_wave['total_trucks']}")
        
        assignments = {}
        
        # Process drones from backend solution
        for idx, drone in enumerate(current_wave.get('drones', [])):
            vehicle_name = f"Drone {idx + 1}"
            node_ids = drone.get('node_ids', [])  # Just the delivery node(s)
            full_route = drone.get('route', [])    # Complete route including depot
            
            # Get delivery coordinates (excludes depot)
            deliveries = self._get_deliveries_from_node_ids(node_ids, customer_nodes)
            
            # Get FULL route coordinates (includes depot)
            route_coords = self._get_full_route_coords(full_route, customer_nodes)
            
            if deliveries:
                assignments[vehicle_name] = {
                    "type": "Drone",
                    "primary_delivery": deliveries[0],
                    "all_deliveries": deliveries,
                    "node_ids": node_ids,
                    "route_node_ids": full_route,  # ← Store full route for reference
                    "route_coords": route_coords,  # ← Store actual coordinates
                    "vehicle_id": drone.get('vehicle_id'),
                    "distance": drone.get('distance', 0),
                    "cost": drone.get('cost', 0),
                    "total_weight": drone.get('total_weight', 0),
                    "total_volume": drone.get('total_volume', 0)
                }
                print(f"  {vehicle_name} (ID: {drone.get('vehicle_id')}): {len(deliveries)} deliveries")
                print(f"    Route: {' → '.join(full_route)}")
                print(f"    Distance: {drone.get('distance', 0):.2f} km | Cost: {drone.get('cost', 0):.2f}")
                print(f"    Weight: {drone.get('total_weight', 0):.2f} kg | Volume: {drone.get('total_volume', 0):.0f}")
        
        # Process trucks from backend solution
        for truck in current_wave.get('trucks', []):
            vehicle_id = truck['vehicle_id']
            vehicle_type, vehicle_name = self._parse_vehicle_id(vehicle_id)
            
            if not vehicle_type:
                continue
                
            node_ids = truck.get('node_ids', [])
            full_route = truck.get('route', [])
            deliveries = self._get_deliveries_from_node_ids(node_ids, customer_nodes)
            route_coords = self._get_full_route_coords(full_route, customer_nodes)
            
            if deliveries:
                capacity_util = truck.get('capacity_utilization', {})
                assignments[vehicle_name] = {
                    "type": vehicle_type,
                    "primary_delivery": deliveries[0],
                    "all_deliveries": deliveries,
                    "node_ids": node_ids,
                    "route_node_ids": full_route,
                    "route_coords": route_coords,
                    "vehicle_id": vehicle_id,
                    "distance": truck.get('distance', 0),
                    "cost": truck.get('cost', 0),
                    "total_weight": truck.get('total_weight', 0),
                    "total_volume": truck.get('total_volume', 0),
                    "capacity_utilization": capacity_util,
                    "weight_percent": capacity_util.get('weight_percent', 0),
                    "volume_percent": capacity_util.get('volume_percent', 0)
                }
                print(f"  {vehicle_name} (ID: {vehicle_id}): {len(deliveries)} deliveries")
                print(f"    Route: {' → '.join(full_route)}")
                print(f"    Distance: {truck.get('distance', 0):.2f} km | Cost: {truck.get('cost', 0):.2f}")
                print(f"    Weight: {truck.get('total_weight', 0):.2f} kg ({capacity_util.get('weight_percent', 0):.1f}%)")
                print(f"    Volume: {truck.get('total_volume', 0):.0f} ({capacity_util.get('volume_percent', 0):.1f}%)")
        
        total_vehicles = len(assignments)
        total_deliveries = sum(len(a['all_deliveries']) for a in assignments.values())
        
        print(f"✅ Created {total_vehicles} vehicle assignments from backend")
        print(f"📦 Total deliveries assigned: {total_deliveries}\n")
        
        return assignments
    
    def _get_deliveries_from_node_ids(self, node_ids: List[str], 
                                     customer_nodes: List[Dict]) -> List[List[float]]:
        """
        Convert node IDs to coordinate list (EXCLUDING depot for deliveries)
        
        Args:
            node_ids: List of node ID strings from solution.json
            customer_nodes: List of customer node dictionaries
            
        Returns:
            List of [lat, lon] coordinates for actual deliveries only
        """
        deliveries = []
        for node_id in node_ids:
            # Skip depot nodes (depot isn't a delivery point)
            if node_id == 'depot':
                continue
            
            # Find matching customer node
            for node in customer_nodes:
                if node['node_id'] == node_id:
                    deliveries.append(node['coords'])
                    break
        
        return deliveries
    
    def _get_full_route_coords(self, node_ids: List[str], 
                              customer_nodes: List[Dict]) -> List[List[float]]:
        """
        Convert ALL node IDs to coordinates INCLUDING depot
        
        Args:
            node_ids: Complete route from solution.json (includes depot)
            customer_nodes: List of customer node dictionaries
            
        Returns:
            Complete route as [lat, lon] coordinates
        """
        route_coords = []
        for node_id in node_ids:
            if node_id == 'depot':
                route_coords.append(self.depot_coords[:])
            else:
                # Find matching customer node
                for node in customer_nodes:
                    if node['node_id'] == node_id:
                        route_coords.append(node['coords'])
                        break
        
        return route_coords
    
    def _parse_vehicle_id(self, vehicle_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse vehicle ID to get type and name
        
        Args:
            vehicle_id: Vehicle ID string (e.g., "E_Truck_1", "F_Truck_2")
            
        Returns:
            Tuple of (vehicle_type, vehicle_name) or (None, None)
        """
        if 'E_Truck' in vehicle_id:
            truck_num = vehicle_id.split('_')[-1]
            return "Electric Truck", f"Electric Truck {truck_num}"
        elif 'F_Truck' in vehicle_id:
            truck_num = vehicle_id.split('_')[-1]
            return "Fuel Truck", f"Fuel Truck {truck_num}"
        return None, None
    
    def create_optimal_delivery_assignments(self, delivery_points: List[List[float]], 
                                          electric_trucks: int, 
                                          fuel_trucks: int, 
                                          drones: int) -> Dict:
        """
        Create delivery assignments ensuring ALL points are covered
        Uses round-robin distribution for complete coverage
        """
        total_vehicles = electric_trucks + fuel_trucks + drones
        total_points = len(delivery_points)
        
        print(f"\n=== FRONTEND FALLBACK ASSIGNMENT ===")
        print(f"Delivery points: {total_points}")
        print(f"Total vehicles: {total_vehicles}")
        
        if total_vehicles == 0:
            print("ERROR: No vehicles configured!")
            return {}
        
        deliveries_per_vehicle = math.ceil(total_points / total_vehicles)
        print(f"Strategy: Each vehicle handles up to {deliveries_per_vehicle} deliveries")
        
        assignments = {}
        
        # Create vehicle list
        all_vehicles = []
        for i in range(drones):
            all_vehicles.append(("Drone", i + 1))
        for i in range(electric_trucks):
            all_vehicles.append(("Electric Truck", i + 1))
        for i in range(fuel_trucks):
            all_vehicles.append(("Fuel Truck", i + 1))
        
        # Distribute ALL delivery points using round-robin
        for i, delivery_point in enumerate(delivery_points):
            vehicle_index = i % total_vehicles
            vehicle_type, vehicle_num = all_vehicles[vehicle_index]
            vehicle_name = f"{vehicle_type} {vehicle_num}"
            
            if vehicle_name not in assignments:
                # First delivery for this vehicle
                assignments[vehicle_name] = {
                    "type": vehicle_type,
                    "primary_delivery": delivery_point[:],
                    "all_deliveries": [delivery_point[:]]
                }
            else:
                # Additional delivery for this vehicle
                assignments[vehicle_name]["all_deliveries"].append(delivery_point[:])
        
        # Verify complete coverage
        total_assigned = sum(len(assignment["all_deliveries"]) for assignment in assignments.values())
        
        print(f"Assignment Results:")
        for vehicle_name, assignment in assignments.items():
            deliveries_count = len(assignment["all_deliveries"])
            print(f"  {vehicle_name}: {deliveries_count} deliveries")
        
        print(f"Total assigned: {total_assigned} delivery assignments")
        print(f"✅ All delivery points assigned!")
        
        return assignments
    
    def tick_movement(self, dt: float = 1.0/3600.0) -> bool:
        """Update vehicle positions for one time tick"""
        if self.vehicles_paused or not self.vehicles:
            return False
        
        vehicles_moved = False
        
        for name, v in self.vehicles.items():
            # Check if vehicle completed route
            if v["route_index"] >= len(v["route"]) - 1:
                continue
            
            # Current segment
            lat1, lon1 = v["route"][v["route_index"]]
            lat2, lon2 = v["route"][v["route_index"] + 1]
            
            # Calculate distance (cache to avoid recalculation)
            if not hasattr(v, 'segment_distance'):
                v['segment_distance'] = OptimizedRouteManager.haversine(
                    lat1, lon1, lat2, lon2
                )
            
            dist = v['segment_distance']
            
            # Handle zero-distance segments
            if dist == 0:
                v["route_index"] += 1
                v["progress"] = 0.0
                if 'segment_distance' in v:
                    del v['segment_distance']
                if v["route_index"] < len(v["route"]):
                    v["pos"] = v["route"][v["route_index"]]
                vehicles_moved = True
                continue
            
            # Calculate movement
            step_km = v["speed"] * dt
            frac = step_km / dist
            v["progress"] += frac
            
            if v["progress"] >= 1.0:
                # Move to next segment
                v["route_index"] += 1
                v["progress"] = 0.0
                if 'segment_distance' in v:
                    del v['segment_distance']
                if v["route_index"] < len(v["route"]):
                    v["pos"] = v["route"][v["route_index"]]
            else:
                # Interpolate position
                v["pos"] = [
                    lat1 + (lat2 - lat1) * v["progress"],
                    lon1 + (lon2 - lon1) * v["progress"]
                ]
            
            vehicles_moved = True
        
        return vehicles_moved
    
    def all_vehicles_returned(self) -> bool:
        """Check if all vehicles completed their routes"""
        for v in self.vehicles.values():
            if v["route_index"] < len(v["route"]) - 1:
                return False
        return True
    
    def restart_vehicles(self):
        """Reset all vehicles to start of their routes"""
        for name, v in self.vehicles.items():
            v["route_index"] = 0
            v["progress"] = 0.0
            v["pos"] = v["route"][0][:]
            if 'segment_distance' in v:
                del v['segment_distance']
        
        self.vehicles_paused = False
        self.wave_running = True
        self.wave_start_time = time.time()
        print("All vehicles restarted from depot!")
    
    def pause_vehicles(self) -> bool:
        """Pause all vehicle movement"""
        self.vehicles_paused = True
        print("Vehicle movement paused!")
        return True
    
    def resume_vehicles(self) -> bool:
        """Resume vehicle movement"""
        self.vehicles_paused = False
        print("Vehicle movement resumed!")
        return True
    
    def get_vehicle_data_for_ui(self, vehicle_name: str) -> Optional[VehicleData]:
        """Get formatted vehicle data for UI display"""
        if vehicle_name not in self.vehicles:
            return None
        
        v = self.vehicles[vehicle_name]
        status = "Stopped" if self.vehicles_paused else "Moving"
        speed = 0 if self.vehicles_paused else v["speed"]
        
        return VehicleData(
            vehicle_name, 
            v["type"], 
            v["pos"][0], 
            v["pos"][1], 
            status, 
            speed
        )
    
    def get_vehicles_for_map(self, max_route_points: int = 25) -> Dict:
        """Get vehicle data formatted for map display"""
        return {
            "vehicles": [
                {
                    "name": name,
                    "type": v["type"],
                    "pos": v["pos"],
                    "route": v["route"][:max_route_points],
                    "speed": v["speed"],
                    "weight": v.get("weight", 0),
                    "volume": v.get("volume", "N/A"),
                    "delivery_count": len(v.get("all_deliveries", [])),
                    "node_ids": v.get("node_ids", []),
                    "distance": v.get("distance", 0),
                    "cost": v.get("cost", 0),
                    "weight_percent": v.get("weight_percent", 0),
                    "volume_percent": v.get("volume_percent", 0)
                }
                for name, v in self.vehicles.items()
            ]
        }
    
    def get_wave_statistics(self) -> Dict:
        """Calculate current wave statistics"""
        total_distance = sum(v.get("distance", 0) for v in self.vehicles.values())
        total_cost = sum(v.get("cost", 0) for v in self.vehicles.values())
        total_weight = sum(v.get("backend_weight", 0) for v in self.vehicles.values())
        total_deliveries = sum(len(v.get("all_deliveries", [])) for v in self.vehicles.values())
        
        return {
            "distance": total_distance,
            "cost": total_cost,
            "weight": total_weight,
            "deliveries": total_deliveries,
            "vehicle_count": len(self.vehicles)
        }
    
    def get_vehicle_progress_summary(self) -> Dict:
        """Get summary of vehicle progress"""
        completed_count = sum(
            1 for v in self.vehicles.values() 
            if v["route_index"] >= len(v["route"]) - 1
        )
        
        total_progress = 0
        for v in self.vehicles.values():
            if len(v["route"]) > 1:
                progress_pct = (v["route_index"] + v["progress"]) / (len(v["route"]) - 1)
                total_progress += min(progress_pct, 1.0)
        
        avg_progress = (total_progress / len(self.vehicles)) if self.vehicles else 0
        
        return {
            "total_vehicles": len(self.vehicles),
            "completed_vehicles": completed_count,
            "in_progress_vehicles": len(self.vehicles) - completed_count,
            "average_progress": avg_progress * 100
        }
    
    def clear_vehicles(self):
        """Clear all vehicles"""
        self.vehicles.clear()
        self.vehicles_started = False
        self.vehicles_paused = False
        self.wave_running = False
        self.wave_completed = False
        print("All vehicles cleared!")