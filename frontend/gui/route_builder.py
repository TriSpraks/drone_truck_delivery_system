"""
Route building and optimization module
Handles background route construction and vehicle assignment
"""
import time
from typing import Dict, List
from PyQt5.QtCore import QThread, pyqtSignal, QMutex

from utils.backend_connector import VEHICLE_SPEEDS, VEHICLE_WEIGHTS
from core.api_handler import OptimizedRouteManager


class OptimizedRouteBuilder(QThread):
    """Background thread for building routes with improved allocation"""
    route_completed = pyqtSignal(str, list)  # vehicle_name, route
    progress_updated = pyqtSignal(int, str)  # progress, status
    all_routes_completed = pyqtSignal(dict)  # all_vehicles_dict
    
    def __init__(self, depot_coords, delivery_assignments, parent=None, preserve_backend_order=False):
        super().__init__(parent)
        self.depot_coords = depot_coords
        self.delivery_assignments = delivery_assignments
        self.preserve_backend_order = preserve_backend_order
        self.vehicles = {}
        self.mutex = QMutex()
        
    def run(self):
        """Build all routes using optimized batch processing"""
        try:
            self.progress_updated.emit(10, "Initializing batch route builder...")
            
            # Check if we should preserve backend's route order
            if self.preserve_backend_order:
                print("Building routes with BACKEND'S OPTIMIZED ORDER...")
                route_results = self._build_routes_preserving_order()
            else:
                print("Building routes with FRONTEND OPTIMIZATION...")
                route_results = OptimizedRouteManager.build_delivery_routes_batch(
                    self.depot_coords, self.delivery_assignments
                )
            
            self.progress_updated.emit(70, "Processing route results...")
            
            # Convert results to vehicle format
            self._process_route_results(route_results)
            
            if not self.isInterruptionRequested():
                self.progress_updated.emit(100, "All routes completed!")
                self.all_routes_completed.emit(self.vehicles)
                
        except Exception as e:
            print(f"Error in optimized route building: {e}")
            self._build_fallback_routes()
    
    def _process_route_results(self, route_results):
        """Convert route results to vehicle format"""
        total_vehicles = len(route_results)
        for idx, (vehicle_name, route_data) in enumerate(route_results.items()):
            if self.isInterruptionRequested():
                return
            
            progress = 70 + int((idx / total_vehicles) * 25)
            self.progress_updated.emit(progress, f"Setting up {vehicle_name}...")
            
            assignment = self.delivery_assignments[vehicle_name]
            route = route_data["route"]
            
            self.mutex.lock()
            try:
                self.vehicles[vehicle_name] = {
                    "type": assignment["type"],
                    "pos": route[0][:],
                    "route": route,
                    "route_index": 0,
                    "speed": VEHICLE_SPEEDS[assignment["type"]],
                    "progress": 0.0,
                    "weight": assignment.get("total_weight", 0),
                    "volume": assignment.get("total_volume", 0),
                    "assigned_delivery": assignment["primary_delivery"],
                    "all_deliveries": route_data.get("all_deliveries", [assignment["primary_delivery"]]),
                    "distance": assignment.get("distance", 0),
                    "cost": assignment.get("cost", 0),
                    "backend_weight": assignment.get("total_weight", 0),
                    "backend_volume": assignment.get("total_volume", 0)
                }
            finally:
                self.mutex.unlock()
            
            self.route_completed.emit(vehicle_name, route)
    
    def _build_routes_preserving_order(self):
        """Build routes preserving backend's node order"""
        route_results = {}
        total = len(self.delivery_assignments)
        
        for idx, (vehicle_name, assignment) in enumerate(self.delivery_assignments.items()):
            if self.isInterruptionRequested():
                return route_results
            
            progress = 10 + int((idx / total) * 60)
            self.progress_updated.emit(progress, f"Building {vehicle_name} route...")
            
            deliveries = assignment['all_deliveries']
            vehicle_type = assignment['type']
            
            if vehicle_type == "Drone":
                route = [
                    self.depot_coords[:],
                    deliveries[0][:] if deliveries else self.depot_coords[:],
                    self.depot_coords[:]
                ]
            else:
                route = self._get_road_route_preserving_order(deliveries)
        
            route_results[vehicle_name] = {
                "route": route,
                "all_deliveries": deliveries
            }
            print(f"✓ {vehicle_name}: {len(route)} waypoints, {len(deliveries)} deliveries")
    
        return route_results
    
    def _get_road_route_preserving_order(self, deliveries):
        """Get road geometry following backend's exact delivery sequence"""
        route = [self.depot_coords[:]]
        current_pos = self.depot_coords
        
        for i, delivery in enumerate(deliveries):
            try:
                segment = OptimizedRouteManager._get_osrm_route_fast(
                    current_pos[0], current_pos[1],
                    delivery[0], delivery[1]
                )
                
                if segment and len(segment) >= 2:
                    route.extend(segment[1:])
                else:
                    route.append(delivery[:])
            
                time.sleep(0.1)  # Rate limit
                
            except Exception as e:
                print(f"OSRM failed for segment {i}, using direct line")
                route.append(delivery[:])
                
            current_pos = delivery
            
        # Return to depot
        try:
            return_segment = OptimizedRouteManager._get_osrm_route_fast(
                current_pos[0], current_pos[1],
                self.depot_coords[0], self.depot_coords[1]
            )
            if return_segment and len(return_segment) >= 2:
                route.extend(return_segment[1:])
            else:
                route.append(self.depot_coords[:])
        except:
            route.append(self.depot_coords[:])
    
        return route
    
    def _build_fallback_routes(self):
        """Fallback route building if batch processing fails"""
        total_vehicles = len(self.delivery_assignments)
        
        for idx, (vehicle_name, assignment) in enumerate(self.delivery_assignments.items()):
            if self.isInterruptionRequested():
                return
                
            progress = int((idx / total_vehicles) * 100)
            self.progress_updated.emit(progress, f"Building fallback route for {vehicle_name}...")
            
            fallback_route = [
                self.depot_coords[:],
                assignment["primary_delivery"][:],
                self.depot_coords[:]
            ]
            
            self.mutex.lock()
            try:
                self.vehicles[vehicle_name] = {
                    "type": assignment["type"],
                    "pos": fallback_route[0][:],
                    "route": fallback_route,
                    "route_index": 0,
                    "speed": VEHICLE_SPEEDS[assignment["type"]],
                    "progress": 0.0,
                    "weight": 0,
                    "assigned_delivery": assignment["primary_delivery"],
                    "all_deliveries": assignment.get("all_deliveries", [assignment["primary_delivery"]])
                }
            finally:
                self.mutex.unlock()
        
        if not self.isInterruptionRequested():
            self.all_routes_completed.emit(self.vehicles)