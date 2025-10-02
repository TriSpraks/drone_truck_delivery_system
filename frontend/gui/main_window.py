"""
COMPLETE OPTIMIZED Main application window for India Airspace Management System
Fixed route allocation, improved performance, and proper delivery point coverage
CORRECTED VERSION - Clean integration with unified route manager
"""
from platform import node
import sys
import os
import json
import time
import math
import random
import threading
import asyncio
from typing import List, Dict, Optional
from collections import defaultdict
import aiohttp

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QFrame, QToolBar, QAction, QMessageBox, QProgressDialog)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl, Qt, QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QFont, QIcon

# Import from other modules
from config.app_config import DARK_STYLE
from utils.backend_connector import (DEFAULT_DEPOT_COORDS, MAP_CENTER, MAP_ZOOM,
                                   DEFAULT_WAVES, PAUSE_BETWEEN_WAVES, VEHICLE_SPEEDS, VEHICLE_WEIGHTS)
from core.data_manager import VehicleData, DataSimulator
from core.api_handler import OptimizedRouteManager  # Use the corrected unified route manager

from widgets.vehicle_control import VehicleControlPanel
from widgets.delivery_info import DeliveryInfoWidget  
from widgets.sound_monitoring import SoundGraphWidget, NoiseStatisticsWidget
from utils.nfz_data import get_india_no_fly_zones
from resources.map_templates import HTML_TEMPLATE
from ui.dialog import DepotSelectionWindow


class OptimizedRouteBuilder(QThread):
    """Background thread for building routes with improved allocation"""
    route_completed = pyqtSignal(str, list)  # vehicle_name, route
    progress_updated = pyqtSignal(int, str)  # progress, status
    all_routes_completed = pyqtSignal(dict)  # all_vehicles_dict
    
    def __init__(self, depot_coords, delivery_assignments, parent=None, preserve_backend_order=False):
        super().__init__(parent)
        self.depot_coords = depot_coords
        self.delivery_assignments = delivery_assignments
        self.preserve_backend_order = preserve_backend_order  # ← ADD THIS
        self.vehicles = {}
        self.mutex = QMutex()
        
    def run(self):
        """Build all routes using optimized batch processing"""
        try:
            self.progress_updated.emit(10, "Initializing batch route builder...")
            
            # ✅ Check if we should preserve backend's route order
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
                        "weight": assignment.get("total_weight", random.randint(*VEHICLE_WEIGHTS[assignment["type"]])),
                        "volume": assignment.get("total_volume", random.randint(10000, 80000)),
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
            
            if not self.isInterruptionRequested():
                self.progress_updated.emit(100, "All routes completed!")
                self.all_routes_completed.emit(self.vehicles)
                
        except Exception as e:
            print(f"Error in optimized route building: {e}")
            # Fallback to simple routes
            self._build_fallback_routes()
            
    def update_vehicle_metrics(self, vehicle_name, metrics):
        """Update vehicle with backend metrics"""
        # Find or create the vehicle status item
        for i in range(self.status_list.count()):
            item_widget = self.status_list.itemWidget(self.status_list.item(i))
            if hasattr(item_widget, 'vehicle_name') and item_widget.vehicle_name == vehicle_name:
                # Update the widget with metrics
                if hasattr(item_widget, 'metrics_label'):
                    metrics_text = (
                        f"Distance: {metrics.get('distance', 0):.2f} km\n"
                        f"Cost: ${metrics.get('cost', 0):.2f}\n"
                        f"Weight: {metrics.get('total_weight', 0):.2f} kg\n"
                        f"Volume: {metrics.get('total_volume', 0)/1000:.1f} L"
                    )
                    item_widget.metrics_label.setText(metrics_text)
                break
            
    def _build_routes_preserving_order(self):
        """Build routes preserving backend's node order, only fetching road geometry"""
        from core.api_handler import OptimizedRouteManager
        route_results = {}
        total = len(self.delivery_assignments)
        
        for idx, (vehicle_name, assignment) in enumerate(self.delivery_assignments.items()):
            if self.isInterruptionRequested():
                return route_results
            
            progress = 10 + int((idx / total) * 60)
            self.progress_updated.emit(progress, f"Building {vehicle_name} route...")
            
            deliveries = assignment['all_deliveries']  # Already in backend's order
            vehicle_type = assignment['type']
            
            if vehicle_type == "Drone":
                # Drones: straight line
                route = [
                    self.depot_coords[:],
                    deliveries[0][:] if deliveries else self.depot_coords[:],
                    self.depot_coords[:]
                ]
            else:
                # Trucks: Get road waypoints in backend's exact order
                route = self._get_road_route_preserving_order(deliveries)
        
            route_results[vehicle_name] = {
                "route": route,
                "all_deliveries": deliveries
            }
            print(f"✓ {vehicle_name}: {len(route)} waypoints, {len(deliveries)} deliveries (backend order)")
    
        return route_results

    def _get_road_route_preserving_order(self, deliveries):
        """Get road geometry following backend's exact delivery sequence"""
        from core.api_handler import OptimizedRouteManager
        import time
        
        route = [self.depot_coords[:]]
        current_pos = self.depot_coords
        
        # Visit deliveries in EXACT backend order
        for i, delivery in enumerate(deliveries):
            try:
                # Get OSRM road segment from current position to next delivery
                segment = OptimizedRouteManager._get_osrm_route_fast(
                    current_pos[0], current_pos[1],
                    delivery[0], delivery[1]
                )
                
                if segment and len(segment) >= 2:
                    # Add segment points (skip first point as it's current position)
                    route.extend(segment[1:])
                else:
                    # Fallback: add delivery point directly
                    route.append(delivery[:])
            
                time.sleep(0.1)  # Rate limit OSRM calls
                
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
            
            # Simple fallback route
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
                    "weight": random.randint(*VEHICLE_WEIGHTS[assignment["type"]]),
                    "assigned_delivery": assignment["primary_delivery"],
                    "all_deliveries": assignment.get("all_deliveries", [assignment["primary_delivery"]])
                }
            finally:
                self.mutex.unlock()
        
        if not self.isInterruptionRequested():
            self.all_routes_completed.emit(self.vehicles)


class IndiaAirspaceMap(QMainWindow):
    def __init__(self, depot_coords=None, customer_count=5, electric_trucks=2, fuel_trucks=1, drones=3):
        super().__init__()
        self.setWindowTitle("India Airspace Management - Optimized Fleet System")
        self.setGeometry(50, 50, 1800, 1000)
        self.setMinimumSize(1600, 900)
        
        # Track widget destruction state
        self._widgets_destroyed = False
        self._shutdown_in_progress = False
        
        # Progress dialog mutex
        self._progress_mutex = QMutex()
        
        # Apply dark theme
        self.setStyleSheet(DARK_STYLE)
        
        # Store depot coordinates and fleet configuration
        self.depot_coords = depot_coords or DEFAULT_DEPOT_COORDS
        self.customer_count = customer_count
        self.electric_trucks = electric_trucks
        self.fuel_trucks = fuel_trucks
        self.drones = drones
        
        # India center coordinates for full country view
        self.map_center = MAP_CENTER
        self.map_zoom = MAP_ZOOM
        
        # No-fly zones data (subset for depot selection)
        self.no_fly_zones = get_india_no_fly_zones()
        
        # Vehicle system
        self.vehicles = {}
        self.current_wave = 0
        self.wave_running = False
        self.wave_start_time = 0.0
        self.vehicles_started = False
        self.vehicles_paused = False
        self.wave_completed = False
        self.auto_next_wave_timer = None
        self.waiting_for_next_wave = False
        
        # Route building thread
        self.route_builder = None
        self.progress_dialog = None
        
         # Initialize empty - will be populated from backend
        self.delivery_points = []
        self.customer_nodes = []
        self.depot_node = None
        self.waves_data = []
        self.initial_solution = None
        
        # Generate delivery points around selected depot based on customer count
        self.delivery_points = self.generate_delivery_points_around_depot()

        self.map_ready = False
        self.setup_ui()
        self.setup_data_simulator()
        self.create_map_file()

        # Movement timer - optimized update frequency
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick_vehicle_movement)
        self.timer.start(1000)  # Reduced to 1 second for better performance

        # Map update timer - separate from movement for efficiency
        self.map_update_timer = QTimer()
        self.map_update_timer.timeout.connect(self.update_map_display)
        self.map_update_timer.start(2000)  # Update map every 2 seconds

        # Batch update flag
        self.pending_map_update = False

        # Open in full screen
        self.showMaximized()

        # Process nodes and trigger backend computations after UI is shown
        QTimer.singleShot(1000, self.start_backend_processing)
    
    def _is_valid_widget(self, widget):
        """Check if widget is valid and not destroyed"""
        try:
            if self._widgets_destroyed or self._shutdown_in_progress:
                return False
            if widget is None:
                return False
            # Try to access a basic property to verify widget is still valid
            _ = widget.isVisible()
            return True
        except (RuntimeError, AttributeError):
            return False
        
    def load_initial_solution_from_file(self):
        """Load initial_solution.json from backend folder"""
        try:
            # Get the correct path to backend folder
            # Assuming structure: project_root/frontend/gui/main_window.py and project_root/backend/
            current_file = os.path.abspath(__file__)
            frontend_gui_dir = os.path.dirname(current_file)  # frontend/gui
            frontend_dir = os.path.dirname(frontend_gui_dir)  # frontend
            project_root = os.path.dirname(frontend_dir)  # project root
            backend_folder = os.path.join(project_root, 'backend')
            solution_file = os.path.join(backend_folder, 'initial_solution.json')
            
            print(f"Looking for initial_solution.json at: {solution_file}")
            
            if not os.path.exists(solution_file):
                print(f"Initial solution file not found at: {solution_file}")
                # Wait a bit longer in case backend is still writing
                import time
                time.sleep(2)
                if not os.path.exists(solution_file):
                    print("File still not found after waiting")
                    return None
            
            with open(solution_file, 'r') as f:
                solution = json.load(f)
            
            print(f"✅ Successfully loaded initial solution with {len(solution.get('summary', {}).get('wave_breakdown', {}))} waves")
            return solution
            
        except Exception as e:
            print(f"Error loading initial solution file: {e}")
            import traceback
            traceback.print_exc()
            return None

    def start_backend_processing(self):
        """Start backend processing asynchronously in a separate thread"""
        from PyQt5.QtCore import QThread, pyqtSignal

        class BackendProcessor(QThread):
            finished = pyqtSignal()
            error = pyqtSignal(str)
            timeout_signal = pyqtSignal()

            def __init__(self, parent):
                super().__init__()
                self.parent = parent
                self.timeout_seconds = 30  # 30 second timeout

            def run(self):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # Run with timeout
                    try:
                        loop.run_until_complete(
                            asyncio.wait_for(
                                self.process_nodes_and_computations(),
                                timeout=self.timeout_seconds
                            )
                        )
                    except asyncio.TimeoutError:
                        print(f"Backend processing timed out after {self.timeout_seconds} seconds")
                        self.timeout_signal.emit()
                        return
                
                    loop.close()
                    self.finished.emit()
                except Exception as e:
                    self.error.emit(str(e))

            async def process_nodes_and_computations(self):
                """Async method to process nodes and trigger backend computations"""
                try:
                    # Insert nodes to backend
                    insert_success = await self.parent.insert_nodes_to_backend()
                    if not insert_success:
                        print("Node insertion and computation failed")
                        return

                    print("✅ Backend processing completed successfully")
            
                    # Wait for backend to finish writing the file (increased wait time)
                    await asyncio.sleep(3)
            
                    # Load the initial solution from the generated JSON file
                    initial_solution = self.parent.load_initial_solution_from_file()
                    if initial_solution:
                        self.parent.initial_solution = initial_solution
                        print(f"✅ Initial solution loaded with {len(initial_solution.get('summary', {}).get('wave_breakdown', {}))} waves")
                
                        # Parse wave information
                        self.parent.parse_wave_information(initial_solution)
                    else:
                        print("⚠️ Could not load initial solution file")

                except Exception as e:
                    print(f"❌ Error in backend processing: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Create and start the processor thread
        self.backend_processor = BackendProcessor(self)
        self.backend_processor.finished.connect(lambda: print("✅ Backend processing thread finished"))
        self.backend_processor.error.connect(lambda err: print(f"❌ Backend processing error: {err}"))
        self.backend_processor.timeout_signal.connect(
            lambda: QMessageBox.warning(
                self,
                "Backend Timeout",
                "Backend processing timed out. You can still use the system with default routing."
            )
        )
        self.backend_processor.start()
        
    def parse_wave_information(self, initial_solution):
        """Parse wave information from backend's initial solution"""
        try:
            self.waves_data = []

            # Filter out the 'summary' key - only process actual wave keys
            for wave_key, wave_data in initial_solution.items():
                # Skip the summary key
                if wave_key == 'summary':
                    continue

                wave_info = {
                    'wave_number': wave_key,
                    'drones': wave_data.get('drones', []),
                    'trucks': wave_data.get('trucks', []),
                    'total_drones': len(wave_data.get('drones', [])),
                    'total_trucks': len(wave_data.get('trucks', []))
                }
                self.waves_data.append(wave_info)

            print(f"✅ Parsed {len(self.waves_data)} actual waves from backend solution")
            for wave in self.waves_data:
                print(f"  {wave['wave_number']}: {wave['total_drones']} drones, {wave['total_trucks']} trucks")

            self.update_wave_info_ui()

        except Exception as e:
            print(f"Error parsing wave information: {e}")
            import traceback
            traceback.print_exc()
    def update_wave_info_ui(self):
        """Update UI to display wave information from backend"""
        if not hasattr(self, 'waves_data') or not self.waves_data:
            return

        try:
            total_vehicles_in_waves = sum(w['total_drones'] + w['total_trucks'] for w in self.waves_data)
            wave_summary = f"Waves: {len(self.waves_data)} | Total: {total_vehicles_in_waves} vehicles"

            if hasattr(self, 'statusBar') and not self._widgets_destroyed:
                current_status = self.statusBar().currentMessage()
                self.statusBar().showMessage(f"{current_status} | {wave_summary}")

            print(f"UI updated with {len(self.waves_data)} waves")

        except Exception as e:
            print(f"Error updating wave info UI: {e}")
    
    def process_backend_nodes(self, nodes_data):
        """Process nodes fetched from backend and set up delivery points"""
        try:
            self.customer_nodes = []
            self.delivery_points = []

            for node in nodes_data:
                if node.get('node_id') == 'depot':
                    # Update depot coordinates from backend
                    self.depot_node = {
                        "node_id": "depot",
                        "type": "depot",
                        "weight": node.get('weight', 0),
                        "volume": node.get('volume', 0),
                        "lon": node['lon'],
                        "lat": node['lat'],
                        "coords": [node['lat'], node['lon']]
                    }
                    self.depot_coords = [node['lat'], node['lon']]
                else:
                    # Customer node
                    customer_node = {
                        "node_id": node['node_id'],
                        "type": "customer",
                        "weight": node.get('weight', 0),
                        "volume": node.get('volume', 0),
                        "lon": node['lon'],
                        "lat": node['lat'],
                        "coords": [node['lat'], node['lon']]
                    }
                    self.customer_nodes.append(customer_node)
                    self.delivery_points.append([node['lat'], node['lon']])

            print(f"Processed {len(self.customer_nodes)} customer nodes from backend")
            print(f"Depot at: {self.depot_coords}")

            # Update UI with backend data
            self.update_depot_and_fleet_ui()

            # Reinitialize map with backend nodes
            if self.map_ready:
                self.reinitialize_map_optimized()

        except Exception as e:
            print(f"Error processing backend nodes: {e}")
    def _safe_widget_operation(self, widget, operation, *args, **kwargs):
        """Safely perform operations on widgets with error handling"""
        try:
            if not self._is_valid_widget(widget):
                return False
            result = operation(*args, **kwargs)
            return result
        except (RuntimeError, AttributeError) as e:
            print(f"Widget operation failed safely: {e}")
            return False
    
    def _safe_set_text(self, widget, text):
        """Safely set text on a widget with error handling"""
        return self._safe_widget_operation(widget, widget.setText, str(text))
    
    def generate_delivery_points_around_depot(self):
        """Generate delivery points with inner/outer circle split, ensuring drone eligibility for inner circle."""
        points = []
        depot_lat, depot_lon = self.depot_coords

        # Depot node
        depot_node = {
            "node_id": "depot",
            "type": "depot",
            "weight": 0,
            "volume": 0,  # in cm³
            "lon": round(depot_lon, 6),
            "lat": round(depot_lat, 6),
            "coords": [round(depot_lat, 6), round(depot_lon, 6)]
        }

        # Drone limits
        drone_max_weight = 5.0      # kg
        drone_max_volume = 20000    # cm³

        # Split nodes 20% inner / 80% outer
        inner_count = max(1, int(self.customer_count * 0.1))
        outer_count = self.customer_count - inner_count

        # ---------------- Inner circle (0.5–5 km) → must be drone-eligible ----------------
        for i in range(inner_count):
            angle = random.uniform(0, 360)
            distance_km = random.uniform(0.5, 5.0)

            lat_offset = (distance_km / 111.32) * math.cos(math.radians(angle))
            lon_offset = (distance_km / (111.32 * math.cos(math.radians(depot_lat)))) * math.sin(math.radians(angle))

            weight = round(random.uniform(0.5, drone_max_weight), 2)
            volume = random.randint(500, drone_max_volume)

            points.append({
                "node_id": f"cust_{len(points) + 1}",
                "type": "customer",
                "weight": weight,
                "volume": volume,
                "lon": round(depot_lon + lon_offset, 6),
                "lat": round(depot_lat + lat_offset, 6),
                "coords": [round(depot_lat + lat_offset, 6), round(depot_lon + lon_offset, 6)]
            })

        # ---------------- Outer circle (3–60 km) → drone or truck eligible ----------------
        for i in range(outer_count):
            angle = random.uniform(0, 360)
            distance_km = random.uniform(3.0, 60.0)

            lat_offset = (distance_km / 111.32) * math.cos(math.radians(angle))
            lon_offset = (distance_km / (111.32 * math.cos(math.radians(depot_lat)))) * math.sin(math.radians(angle))

            if random.random() < 0.15:  # 15% chance → drone-eligible even if far
                weight = round(random.uniform(0.5, drone_max_weight), 2)
                volume = random.randint(500, drone_max_volume)
                eligible = "drone"
            else:
                weight = round(random.uniform(100, 1000), 2)  # strictly truck
                volume = random.randint(200000, 5400000)
                eligible = "truck"
            points.append({
                "node_id": f"cust_{len(points) + 1}",
                "type": "customer",
                "weight": weight,
                "volume": volume,
                "lon": round(depot_lon + lon_offset, 6),
                "lat": round(depot_lat + lat_offset, 6),
                "coords": [round(depot_lat + lat_offset, 6), round(depot_lon + lon_offset, 6)],
                "eligible": "truck"  # ✅ explicitly mark
            })
            
        # DON'T shuffle - backend needs consistent node ordering!
        # Sort by node_id to ensure consistent ordering
        points.sort(key=lambda x: int(x['node_id'].replace('cust_', '')))

        # Count drone-eligible inner circle
        drone_eligible_count = sum(
            1 for p in points
            if p["weight"] <= drone_max_weight and p["volume"] <= drone_max_volume
            and math.sqrt((p["lat"] - depot_lat)**2 + (p["lon"] - depot_lon)**2) * 111.32 <= 5
        )
        print(f"✅ Inner circle drone-eligible: {drone_eligible_count}/{inner_count}")

        # Store nodes
        self.depot_node = depot_node
        self.customer_nodes = points

        # Return coordinates for convenience
        return [p["coords"] for p in points]
    
    async def fetch_nodes_from_backend(self):
        """Fetch generated nodes from backend database"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:8000/api/nodes") as response:
                    if response.status == 200:
                        nodes_data = await response.json()
                        print(f"Fetched {len(nodes_data)} nodes from backend")
                        return nodes_data
                    else:
                        error_text = await response.text()
                        print(f"Failed to fetch nodes: {response.status} - {error_text}")
                        return []
        except Exception as e:
            print(f"Error fetching nodes: {e}")
            return []

    async def insert_nodes_to_backend(self):
        """Insert generated delivery points to backend database via API"""
        if not hasattr(self, 'customer_nodes') or not self.customer_nodes:
            print("No customer nodes to insert")
            return False

        try:
            # Prepare nodes data for backend API
            nodes_list = []
            for node in self.customer_nodes:
                nodes_list.append({
                    "node_id": node["node_id"],
                    "weight": node["weight"],
                    "volume": node["volume"],
                    "lon": node["lon"],
                    "lat": node["lat"]
                })

            # Add depot node
            if hasattr(self, 'depot_node'):
                nodes_list.insert(0, {
                    "node_id": self.depot_node["node_id"],
                    "weight": self.depot_node["weight"],
                    "volume": self.depot_node["volume"],
                    "lon": self.depot_node["lon"],
                    "lat": self.depot_node["lat"]
                })

            # Prepare the request data as expected by backend
            nodes_data = {
                "nodes": nodes_list,
                "vehicle_config": {
                    "electric_trucks": self.electric_trucks,
                    "fuel_trucks": self.fuel_trucks,
                    "drones": self.drones
                }
            }

            print(f"Inserting {len(nodes_list)} nodes to backend database...")

            # Insert nodes via backend API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://127.0.0.1:8000/api/nodes/insert",
                    json=nodes_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"Successfully inserted {result.get('nodes_inserted', 0)} nodes to backend")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"Failed to insert nodes: {response.status} - {error_text}")
                        return False

        except aiohttp.ClientError as e:
            print(f"Network error inserting nodes: {e}")
            return False
        except Exception as e:
            print(f"Error inserting nodes: {e}")
            return False

    async def trigger_backend_computations(self):
        """Trigger distance and vehicle matrix computations in backend"""
        try:
            print("Triggering backend distance computations...")

            async with aiohttp.ClientSession() as session:
                # Compute distances
                async with session.post("http://127.0.0.1:8000/api/compute/distances") as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Distance computation completed: {result.get('entries', 0)} entries")
                    else:
                        error_text = await response.text()
                        print(f"❌ Distance computation failed: {response.status} - {error_text}")
                        return False

                # Compute vehicle matrix
                async with session.post("http://127.0.0.1:8000/api/compute/vehicle_matrix") as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Vehicle matrix computation completed: {result.get('entries', 0)} entries")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Vehicle matrix computation failed: {response.status} - {error_text}")
                        return False

        except aiohttp.ClientError as e:
            print(f"❌ Network error triggering computations: {e}")
            return False
        except Exception as e:
            print(f"❌ Error triggering computations: {e}")
            return False

    async def process_nodes_and_computations(self):
        """Process node insertion (computations are handled automatically by /api/nodes/insert)"""
        try:
            # Insert nodes to backend (this automatically triggers computations)
            insert_success = await self.insert_nodes_to_backend()
            if insert_success:
                print("✅ Backend processing completed successfully")
                return True
            else:
                print("Node insertion failed")
                return False

        except Exception as e:
            print(f"❌ Error in backend processing: {e}")
            return False
    
    def create_optimal_delivery_assignments(self):
        """Create delivery assignments ensuring ALL points are covered with multi-delivery support"""
        total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
        delivery_points = self.delivery_points[:]
        
        print(f"\n=== OPTIMIZED DELIVERY ALLOCATION ===")
        print(f"Delivery points: {len(delivery_points)}")
        print(f"Total vehicles: {total_vehicles}")
        print(f"Fleet: {self.electric_trucks}E + {self.fuel_trucks}F + {self.drones}D")
        
        if total_vehicles == 0:
            print("ERROR: No vehicles configured!")
            return {}
        
        assignments = {}
        
        # Create all vehicles with their types
        all_vehicles = []
        for i in range(self.drones):
            all_vehicles.append(("Drone", i + 1))
        for i in range(self.electric_trucks):
            all_vehicles.append(("Electric Truck", i + 1))
        for i in range(self.fuel_trucks):
            all_vehicles.append(("Fuel Truck", i + 1))
        
        # Calculate deliveries per vehicle
        deliveries_per_vehicle = math.ceil(len(delivery_points) / total_vehicles)
        print(f"Strategy: Each vehicle will handle up to {deliveries_per_vehicle} delivery points")
        
        # Distribute ALL delivery points to vehicles using round-robin
        for i, delivery_point in enumerate(delivery_points):
            vehicle_index = i % total_vehicles
            vehicle_type, vehicle_num = all_vehicles[vehicle_index]
            vehicle_name = f"{vehicle_type} {vehicle_num}"
            
            if vehicle_name not in assignments:
                # First delivery point for this vehicle (primary delivery)
                assignments[vehicle_name] = {
                    "type": vehicle_type,
                    "primary_delivery": delivery_point[:],  # Primary delivery for route building
                    "all_deliveries": [delivery_point[:]]   # List of all deliveries for this vehicle
                }
            else:
                # Additional delivery points for this vehicle
                assignments[vehicle_name]["all_deliveries"].append(delivery_point[:])
        
        # Verify complete coverage
        total_assigned_points = sum(len(assignment["all_deliveries"]) for assignment in assignments.values())
        unique_assigned_points = set()
        for assignment in assignments.values():
            for delivery in assignment["all_deliveries"]:
                unique_assigned_points.add(tuple(delivery))
        
        print(f"Final assignment results:")
        print(f"- Created vehicles: {len(assignments)}")
        print(f"- Total delivery assignments: {total_assigned_points}")
        print(f"- Unique delivery points covered: {len(unique_assigned_points)}")
        print(f"- Original delivery points: {len(delivery_points)}")
        
        # Detailed breakdown
        for vehicle_name, assignment in assignments.items():
            deliveries_count = len(assignment["all_deliveries"])
            print(f"  {vehicle_name}: {deliveries_count} deliveries")
        
        if len(unique_assigned_points) == len(delivery_points):
            print("✅ SUCCESS: All delivery points have been assigned!")
        else:
            missing_points = len(delivery_points) - len(unique_assigned_points)
            print(f"⚠️  WARNING: {missing_points} points might have assignment issues!")
        
        return assignments
    
    def setup_ui(self):
        """Setup UI with sidebar layout"""
        try:
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout with sidebars
            main_layout = QHBoxLayout(central_widget)
            main_layout.setSpacing(10)
            main_layout.setContentsMargins(10, 10, 10, 10)
            
            # Left sidebar (300px width)
            left_panel = QFrame()
            left_panel.setMaximumWidth(400)
            left_panel.setMinimumWidth(350)
            left_layout = QVBoxLayout(left_panel)
            
            # Logo/Title
            title_label = QLabel("Drone Truck Delivery System")
            title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ff6b35; padding: 10px;")
            title_label.setAlignment(Qt.AlignCenter)
            
            # Depot and fleet configuration info
            depot_info = QLabel(f"Depot: {self.depot_coords[0]:.4f}, {self.depot_coords[1]:.4f}")
            depot_info.setStyleSheet("font-size: 13px; color: #cccccc; padding: 5px; text-align: center;")
            depot_info.setAlignment(Qt.AlignCenter)
            
            customer_info = QLabel(f"Customers: {self.customer_count}")
            customer_info.setStyleSheet("font-size: 13px; color: #8b5cf6; font-weight: bold; padding: 5px; text-align: center;")
            customer_info.setAlignment(Qt.AlignCenter)
            
            # Fleet configuration display
            fleet_info = QLabel(f"Fleet: {self.electric_trucks}E + {self.fuel_trucks}F + {self.drones}D")
            fleet_info.setStyleSheet("font-size: 13px; color: #4CAF50; font-weight: bold; padding: 5px; text-align: center;")
            fleet_info.setAlignment(Qt.AlignCenter)
            
            total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
            fleet_summary = QLabel(f"Total Vehicles: {total_vehicles}")
            fleet_summary.setStyleSheet("font-size: 13px; color: #FF9800; padding: 2px; text-align: center;")
            fleet_summary.setAlignment(Qt.AlignCenter)
            
            # Store references for updates
            self.depot_info_label = depot_info
            self.customer_info_label = customer_info
            self.fleet_info_label = fleet_info
            self.fleet_summary_label = fleet_summary
            
            # Control panels
            try:
                self.vehicle_control = VehicleControlPanel()
                self.delivery_info = DeliveryInfoWidget(self.depot_coords, self.customer_count)
            except Exception as e:
                print(f"Error creating control panels: {e}")
                self.vehicle_control = QWidget()
                self.delivery_info = QWidget()
            
            left_layout.addWidget(title_label)
            left_layout.addWidget(depot_info)
            left_layout.addWidget(customer_info)
            left_layout.addWidget(fleet_info)
            left_layout.addWidget(fleet_summary)
            left_layout.addWidget(self.vehicle_control)
            left_layout.addWidget(self.delivery_info)
            
            # Middle panel - Map
            middle_widget = QWidget()
            middle_layout = QVBoxLayout(middle_widget)
            
            # Toolbar with depot info
            toolbar = QToolBar()
            
            # Depot change action
            self.change_depot_action = QAction("🚩 Change Depot & Fleet Configuration", self)
            self.change_depot_action.triggered.connect(self.change_depot_location)
            toolbar.addAction(self.change_depot_action)
            
            toolbar.addSeparator()
            
            # Toggle controls
            self.toggle_nfz_action = QAction("Toggle No-Fly Zones", self)
            self.toggle_nfz_action.setCheckable(True)
            self.toggle_nfz_action.setChecked(True)
            self.toggle_nfz_action.triggered.connect(self.toggle_no_fly_zones)
            toolbar.addAction(self.toggle_nfz_action)
            
            self.toggle_vehicles_action = QAction("Toggle Vehicles", self)
            self.toggle_vehicles_action.setCheckable(True)
            self.toggle_vehicles_action.setChecked(True)
            self.toggle_vehicles_action.triggered.connect(self.toggle_vehicles)
            toolbar.addAction(self.toggle_vehicles_action)
            
            toolbar.addSeparator()
            
            # Start/Stop vehicles toggle button
            self.start_stop_action = QAction("▶ Start Vehicles", self)
            self.start_stop_action.setCheckable(True)
            self.start_stop_action.triggered.connect(self.toggle_start_stop_vehicles)
            toolbar.addAction(self.start_stop_action)

            # Next Wave button (hidden initially)
            self.next_wave_action = QAction("⏭ Next Wave", self)
            self.next_wave_action.triggered.connect(self.start_next_wave)
            self.next_wave_action.setVisible(False)
            toolbar.addAction(self.next_wave_action)

            # Restart vehicles button
            self.restart_action = QAction("🔄 Restart from Beginning", self)
            self.restart_action.triggered.connect(self.restart_vehicles)
            self.restart_action.setVisible(False)
            toolbar.addAction(self.restart_action)
            
            # Map view
            self.map_view = QWebEngineView()
            self.map_view.loadFinished.connect(self.on_map_ready)
            
            middle_layout.addWidget(toolbar)
            middle_layout.addWidget(self.map_view)
            
            # Right panel - Sound monitoring
            right_panel = QFrame()
            right_panel.setMaximumWidth(400)
            right_panel.setMinimumWidth(350)
            right_layout = QVBoxLayout(right_panel)
            
            # Sound monitoring title
            sound_title = QLabel("Drone Sound Monitoring")
            sound_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff6b35; padding: 10px;")
            
            try:
                self.sound_graphs = SoundGraphWidget()
                self.noise_stats = NoiseStatisticsWidget()
            except Exception as e:
                print(f"Error creating sound widgets: {e}")
                self.sound_graphs = QWidget()
                self.noise_stats = QWidget()
            
            right_layout.addWidget(sound_title)
            right_layout.addWidget(self.sound_graphs, 2)
            right_layout.addWidget(self.noise_stats, 1)
            
            # Add panels to main layout
            main_layout.addWidget(left_panel)
            main_layout.addWidget(middle_widget, 1)
            main_layout.addWidget(right_panel)
            
            # Status bar
            self.update_status_bar()
            self.statusBar().setStyleSheet("background-color: #2d2d2d; color: #ffffff; padding: 5px;")
            
        except Exception as e:
            print(f"Error setting up UI: {e}")
            self._widgets_destroyed = True
    
    def update_status_bar(self):
        """Update status bar with current configuration"""
        try:
            if self._widgets_destroyed or not hasattr(self, 'statusBar'):
                return
                
            total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
            coverage_info = f"Coverage: {len(self.delivery_points)} delivery points"
            if total_vehicles > 0:
                avg_deliveries = math.ceil(len(self.delivery_points) / total_vehicles)
                coverage_info += f" (~{avg_deliveries} per vehicle)"
            
            status_message = (
                f"Optimized Fleet System Ready - "
                f"Depot: {self.depot_coords[0]:.4f}, {self.depot_coords[1]:.4f} | "
                f"Fleet: {total_vehicles} vehicles ({self.electric_trucks}E, {self.fuel_trucks}F, {self.drones}D) | "
                f"{coverage_info}"
            )
            
            self.statusBar().showMessage(status_message)
        except Exception as e:
            print(f"Error updating status bar: {e}")
    
    def toggle_start_stop_vehicles(self):
        """Toggle between starting and stopping vehicles"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return
            
        if self.start_stop_action.isChecked():
            self.start_vehicles_optimized()
            self.start_stop_action.setText("⏸ Pause Vehicles")
            self.start_stop_action.setToolTip("Click to pause all vehicles")
            if self._is_valid_widget(self.restart_action):
                self.restart_action.setVisible(True)
        else:
            self.pause_vehicles()
            self.start_stop_action.setText("▶ Resume Vehicles")
            self.start_stop_action.setToolTip("Click to resume vehicle simulation")
            
    def create_assignments_from_waves(self):
        """Create vehicle assignments from backend's wave solution"""
        if not hasattr(self, 'waves_data') or not self.waves_data:
            print("⚠️ No wave data available, using fallback assignment method")
            return self.create_optimal_delivery_assignments()
        
        # Use only the FIRST actual wave for now
        current_wave = self.waves_data[0] if self.waves_data else None
        if not current_wave:
            print("⚠️ No valid wave found, using fallback")
            return self.create_optimal_delivery_assignments()
        
        print(f"\n=== USING BACKEND WAVE SOLUTION ===")
        print(f"Wave: {current_wave['wave_number']}")
        print(f"Drones: {current_wave['total_drones']}, Trucks: {current_wave['total_trucks']}")
        
        assignments = {}
        
        # Process drones from backend solution
        for idx, drone in enumerate(current_wave['drones']):
            vehicle_name = f"Drone {idx + 1}"
            node_ids = drone.get('node_ids', [])  # Changed from 'route' to 'node_ids'
            
            deliveries = []
            for node_id in node_ids:
                 # Skip depot nodes in the list
                if node_id == 'depot':
                    continue
            
                # Find the node coordinates
                found = False
                for node in self.customer_nodes:
                    if node['node_id'] == node_id:
                        deliveries.append(node['coords'])
                        print(f"   ✓ Found {node_id} at coords: {node['coords']}")  # ← ADD THIS
                        found = True
                        break
                
                if not found:
                    print(f"   ❌ ERROR: Could not find {node_id} in customer_nodes!")  # ← ADD THIS
            
            if deliveries:
                assignments[vehicle_name] = {
                    "type": "Drone",
                    "primary_delivery": deliveries[0],
                    "all_deliveries": deliveries,
                    "distance": drone.get('distance', 0),  # Add backend distance
                    "cost": drone.get('cost', 0),  # Add backend cost
                    "total_weight": drone.get('total_weight', 0),  # Add backend weight
                    "total_volume": drone.get('total_volume', 0)  # Add backend volume
                }
                print(f"  {vehicle_name}: {len(deliveries)} deliveries | "
                    f"Distance: {drone.get('distance', 0):.2f} km | "
                    f"Cost: ${drone.get('cost', 0):.2f} | "
                    f"Weight: {drone.get('total_weight', 0):.2f} kg")
        
        # Process trucks from backend solution
        for truck in current_wave['trucks']:
            vehicle_id = truck['vehicle_id']
            # Extract vehicle type from ID (E_Truck_1, F_Truck_1, etc.)
            if 'E_Truck' in vehicle_id:
                vehicle_type = "Electric Truck"
                truck_num = vehicle_id.split('_')[-1]
                vehicle_name = f"Electric Truck {truck_num}"
            elif 'F_Truck' in vehicle_id:
                vehicle_type = "Fuel Truck"
                truck_num = vehicle_id.split('_')[-1]
                vehicle_name = f"Fuel Truck {truck_num}"
            else:
                continue
            
            node_ids = truck.get('node_ids', [])  # Changed from 'route' to 'node_ids'
            
            deliveries = []
            for node_id in node_ids:
                # Skip depot nodes in the list
                if node_id == 'depot':
                    continue
                # Find the node coordinates
                for node in self.customer_nodes:
                    if node['node_id'] == node_id:
                        deliveries.append(node['coords'])
                        break
            
            if deliveries:
                assignments[vehicle_name] = {
                    "type": vehicle_type,
                    "primary_delivery": deliveries[0],
                    "all_deliveries": deliveries,
                    "distance": truck.get('distance', 0),
                    "cost": truck.get('cost', 0),
                    "total_weight": truck.get('total_weight', 0),
                    "total_volume": truck.get('total_volume', 0),
                    "capacity_utilization": truck.get('capacity_utilization', {})
                }
                print(f"  {vehicle_name}: {len(deliveries)} deliveries | "
                f"Distance: {truck.get('distance', 0):.2f} km | "
                f"Cost: ${truck.get('cost', 0):.2f} | "
                f"Weight: {truck.get('total_weight', 0):.2f} kg")
        
        total_vehicles = len(assignments)
        total_deliveries = sum(len(a['all_deliveries']) for a in assignments.values())
        
        print(f"✅ Created {total_vehicles} vehicle assignments from backend")
        print(f"📦 Total deliveries assigned: {total_deliveries}")
        
        return assignments
    
    def start_vehicles_optimized(self):
        """Start vehicles with optimized route building"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return False

        if not self.map_ready:
            QMessageBox.warning(self, "Map Not Ready", "Please wait for the map to finish loading.")
            return False

        if not self.vehicles_started:
            # Wait for backend processing if still in progress
            if hasattr(self, 'backend_processor') and self.backend_processor.isRunning():
                QMessageBox.information(
                    self,
                    "Backend Processing",
                    "Backend is still computing optimal routes. Please wait a few seconds and try again."
                )
                return False
            
            # CRITICAL: Use backend wave solution if available
            if hasattr(self, 'waves_data') and self.waves_data:
                print(f"\n=== USING BACKEND WAVE SOLUTION ===")
                delivery_assignments = self.create_assignments_from_waves()
                use_backend_routes = True  # ← ADD THIS FLAG
            else:
                print(f"\n=== FALLBACK: Using frontend assignment ===")
                delivery_assignments = self.create_optimal_delivery_assignments()
                use_backend_routes = False

            if not delivery_assignments:
                QMessageBox.warning(self, "No Assignments", "No delivery assignments could be created.")
                return False

            # Verify assignments
            total_assigned = sum(len(assignment["all_deliveries"]) for assignment in delivery_assignments.values())
            print(f"Total vehicles: {len(delivery_assignments)}")
            print(f"Total deliveries: {total_assigned}")

            # Thread-safe progress dialog creation
            # Create progress dialog - NON-BLOCKING
            self._progress_mutex.lock()
            try:
                if self.progress_dialog is None:
                    self.progress_dialog = QProgressDialog(
                        "Building optimized routes...", 
                        "Cancel", 
                        0, 100, 
                        self
                    )
                    self.progress_dialog.setWindowTitle("Optimizing Fleet Routes")
                    self.progress_dialog.setWindowModality(Qt.NonModal)  # ← KEY: Non-blocking
                    self.progress_dialog.setMinimumDuration(0)
                    self.progress_dialog.show()
                    
                    # Force UI update
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()
            finally:
                self._progress_mutex.unlock()

            # Start background route building
            self.route_builder = OptimizedRouteBuilder(self.depot_coords, delivery_assignments, self,preserve_backend_order=use_backend_routes )
            self.route_builder.progress_updated.connect(self.on_route_progress)
            self.route_builder.all_routes_completed.connect(self.on_routes_completed)
            self.route_builder.start()

            self.vehicles_started = True
            self.vehicles_paused = False

        else:
            # Resume paused vehicles
            self.vehicles_paused = False
            self.update_all_vehicle_statuses("Moving")

        return True
    
    def on_route_progress(self, progress, status):
        """Handle route building progress updates"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return
        
        self._progress_mutex.lock()
        try:
            if self.progress_dialog is not None and self._is_valid_widget(self.progress_dialog):
                self.progress_dialog.setValue(progress)
                self.progress_dialog.setLabelText(status)
                
                if self.progress_dialog.wasCanceled():
                    if self.route_builder and self.route_builder.isRunning():
                        self.route_builder.requestInterruption()
                        self.route_builder.quit()
                    self.vehicles_started = False
                    self._cleanup_progress_dialog()
                    return
            else:
                self.progress_dialog = None
        except (RuntimeError, AttributeError) as e:
            print(f"Progress dialog error (safely handled): {e}")
            self.progress_dialog = None
        finally:
            self._progress_mutex.unlock()
    
    def on_routes_completed(self, vehicles_dict):
        """Handle completion of route building"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return

        print("🎉 Routes completed! Cleaning up dialog...")

        # FORCE close progress dialog immediately - don't wait
        self._progress_mutex.lock()
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setValue(100)  # Set to 100% first
                self.progress_dialog.close()
                self.progress_dialog.deleteLater()  # Force deletion
                self.progress_dialog = None
                print("✅ Progress dialog force-closed")
        except Exception as e:
            print(f"Dialog cleanup error: {e}")
            self.progress_dialog = None
        finally:
            self._progress_mutex.unlock()

        # Process events to ensure dialog closes
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

        # Store vehicles and start simulation
        self.vehicles = vehicles_dict
        self.wave_running = True
        self.wave_start_time = time.time()

        # Update UI
        self.update_all_vehicle_statuses("Moving")

        # Send to map in batches
        self.send_vehicles_to_js_batch()

        # Calculate coverage
        total_unique_deliveries = set()
        total_delivery_assignments = 0

        for vehicle_name, vehicle_data in self.vehicles.items():
            all_deliveries = vehicle_data.get("all_deliveries", [vehicle_data["assigned_delivery"]])
            total_delivery_assignments += len(all_deliveries)
            for delivery in all_deliveries:
                total_unique_deliveries.add(tuple(delivery))

        print(f"✅ Fleet optimization completed!")
        print(f"Created {len(self.vehicles)} vehicles")
        print(f"Total delivery assignments: {total_delivery_assignments}")
        print(f"Unique delivery points covered: {len(total_unique_deliveries)}/{len(self.delivery_points)}")

        # Show success message
        try:
            coverage_percentage = (len(total_unique_deliveries) / len(self.delivery_points)) * 100
            QMessageBox.information(
                self,
                "Fleet Optimized",
                f"Fleet optimization completed!\n\n"
                f"• Vehicles: {len(self.vehicles)}\n"
                f"• Deliveries: {total_delivery_assignments}\n"
                f"• Coverage: {len(total_unique_deliveries)}/{len(self.delivery_points)} ({coverage_percentage:.1f}%)\n"
                f"• Time: {time.time() - self.wave_start_time:.1f}s"
            )
        except Exception as e:
            print(f"Error showing completion message: {e}")
    
    def _cleanup_progress_dialog(self):
        """Safely clean up progress dialog"""
        self._progress_mutex.lock()
        try:
            if self.progress_dialog is not None and self._is_valid_widget(self.progress_dialog):
                self.progress_dialog.close()
            self.progress_dialog = None
        except Exception as e:
            print(f"Error cleaning up progress dialog: {e}")
        finally:
            self._progress_mutex.unlock()
    
    def send_vehicles_to_js_batch(self):
        """Send vehicle data in batches to prevent blocking"""
        if not self.map_ready or not self.toggle_vehicles_action.isChecked() or self._widgets_destroyed:
            return
        
        # Split vehicles into smaller batches
        vehicle_list = list(self.vehicles.items())
        batch_size = 12  # Smaller batches for better performance
        
        for i in range(0, len(vehicle_list), batch_size):
            batch = vehicle_list[i:i + batch_size]
            
            vehicle_data = {
                "vehicles": [
                    {
                        "name": name,
                        "type": v["type"],
                        "pos": v["pos"],
                        "route": v["route"][:25],  # Limit route points for performance
                        "speed": v["speed"],
                        "weight": v["weight"],
                        "volume": v.get("volume", "N/A"),
                        "delivery_count": len(v.get("all_deliveries", [v["assigned_delivery"]]))
                    }
                    for name, v in batch
                ],
                "is_batch": True,
                "batch_index": i // batch_size
            }
            
            try:
                js_code = f"window.addVehicleBatch && window.addVehicleBatch({json.dumps(vehicle_data)});"
                self.map_view.page().runJavaScript(js_code)
            except Exception as e:
                print(f"Error sending vehicle batch to map: {e}")
    
    def update_map_display(self):
        """Batch map updates to reduce frequency"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return
            
        if self.pending_map_update and self.map_ready and self.vehicles and not self.vehicles_paused:
            self.update_vehicle_positions_js_optimized()
            self.pending_map_update = False
    
    def update_vehicle_positions_js_optimized(self):
        """Update only changed vehicle positions"""
        if not self.map_ready or not self.vehicles or not self.toggle_vehicles_action.isChecked() or self._widgets_destroyed:
            return
        
        # Only send position updates, not full vehicle data
        position_data = {
            "position_updates": [
                {
                    "name": name,
                    "pos": v["pos"],
                    "speed": v["speed"] if not self.vehicles_paused else 0
                }
                for name, v in self.vehicles.items()
            ]
        }
        
        try:
            js_code = f"window.updateVehiclePositionsOptimized && window.updateVehiclePositionsOptimized({json.dumps(position_data)});"
            self.map_view.page().runJavaScript(js_code)
        except Exception as e:
            print(f"Error updating vehicle positions: {e}")
    
    def update_all_vehicle_statuses(self, status):
        """Update all vehicle statuses in the UI"""
        if self._widgets_destroyed or not self._is_valid_widget(self.vehicle_control):
            return
            
        for name, v in self.vehicles.items():
            try:
                vehicle_data = VehicleData(
                    name, v["type"], v["pos"][0], v["pos"][1], status, 
                    v["speed"] if status == "Moving" else 0
                )
                if hasattr(self.vehicle_control, 'update_vehicle_status'):
                    self.vehicle_control.update_vehicle_status(vehicle_data)
            except Exception as e:
                print(f"Error updating vehicle status for {name}: {e}")
    
    def pause_vehicles(self):
        """Pause vehicle movement but keep them visible on map"""
        self.vehicles_paused = True
        self.update_all_vehicle_statuses("Stopped")
        print("Vehicle movement paused! Vehicles remain visible at current positions.")
        return True
    
    def start_next_wave(self):
        """Start the next wave of vehicles"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return

        # Cancel auto-start timer if running
        if self.auto_next_wave_timer:
            self.auto_next_wave_timer.stop()
            self.auto_next_wave_timer = None

        self.waiting_for_next_wave = False
        self.wave_completed = False

        # Hide next wave button
        if self._is_valid_widget(self.next_wave_action):
            self.next_wave_action.setVisible(False)

        # Move to next wave
        self.current_wave += 1

        # Check if we have more waves
        if hasattr(self, 'waves_data') and self.current_wave < len(self.waves_data):
            print(f"Starting Wave {self.current_wave + 1} of {len(self.waves_data)}")

            # Clear current vehicles
            self.vehicles.clear()
            if self.map_ready:
                try:
                    self.map_view.page().runJavaScript("window.clearAllVehicles && window.clearAllVehicles();")
                except Exception as e:
                    print(f"Error clearing map vehicles: {e}")

            # Start new wave
            self.start_vehicles_optimized()

            # Update status
            try:
                if hasattr(self, 'statusBar') and not self._widgets_destroyed:
                    self.statusBar().showMessage(
                        f"Wave {self.current_wave + 1}/{len(self.waves_data)} started - "
                        f"{len(self.vehicles)} vehicles dispatched"
                    )
            except Exception as e:
                print(f"Error updating status: {e}")
        else:
            # All waves completed
            print("All waves completed!")
            try:
                QMessageBox.information(
                    self,
                    "All Waves Completed",
                    f"All {len(self.waves_data) if hasattr(self, 'waves_data') else 'available'} waves have been completed!\n\n"
                    f"Fleet operations finished successfully."
                )
            except Exception as e:
                print(f"Error showing completion message: {e}")

            # Reset to first wave
            self.current_wave = 0
            self.vehicles_started = False

            if self._is_valid_widget(self.start_stop_action):
                self.start_stop_action.setChecked(False)
                self.start_stop_action.setText("▶ Start Vehicles")

    def start_auto_next_wave_timer(self):
        """Start 5-minute timer for automatic next wave"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return

        self.waiting_for_next_wave = True

        # Create countdown timer (5 minutes = 300 seconds)
        self.auto_next_wave_timer = QTimer()
        self.auto_next_wave_countdown = 300  # 5 minutes in seconds

        def countdown_tick():
            if self._widgets_destroyed or not self.waiting_for_next_wave:
                if self.auto_next_wave_timer:
                    self.auto_next_wave_timer.stop()
                return

            self.auto_next_wave_countdown -= 1

            # Update button text with countdown
            if self._is_valid_widget(self.next_wave_action):
                minutes = self.auto_next_wave_countdown // 60
                seconds = self.auto_next_wave_countdown % 60
                self.next_wave_action.setText(f"⏭ Next Wave (Auto in {minutes}:{seconds:02d})")

            # Update status bar
            try:
                if hasattr(self, 'statusBar') and not self._widgets_destroyed:
                    minutes = self.auto_next_wave_countdown // 60
                    seconds = self.auto_next_wave_countdown % 60
                    self.statusBar().showMessage(
                        f"Wave {self.current_wave + 1} completed - "
                        f"Next wave starting automatically in {minutes}:{seconds:02d} "
                        f"(or click 'Next Wave' to start now)"
                    )
            except Exception as e:
                print(f"Error updating countdown status: {e}")

            # When countdown reaches zero, start next wave
            if self.auto_next_wave_countdown <= 0:
                if self.auto_next_wave_timer:
                    self.auto_next_wave_timer.stop()
                print("Auto-starting next wave after 5-minute wait...")
                self.start_next_wave()

        self.auto_next_wave_timer.timeout.connect(countdown_tick)
        self.auto_next_wave_timer.start(1000)  # Update every second

        print("Started 5-minute auto-start timer for next wave")
    def restart_vehicles(self):
        """Restart vehicles from the beginning of their routes"""
        if self._widgets_destroyed or not self.vehicles_started or not self.vehicles:
            return
        
        # Reset all vehicles to start of their routes
        for name, v in self.vehicles.items():
            v["route_index"] = 0
            v["progress"] = 0.0
            v["pos"] = v["route"][0][:]
        
        # Resume movement if paused
        self.vehicles_paused = False
        self.wave_running = True
        self.wave_start_time = time.time()
        
        # Update button states
        if self._is_valid_widget(self.start_stop_action):
            self.start_stop_action.setChecked(True)
            self.start_stop_action.setText("⏸ Pause Vehicles")
        
        self.update_all_vehicle_statuses("Moving")
        self.send_vehicles_to_js_batch()
        
        print("All vehicles restarted from the beginning of their routes!")
        try:
            QMessageBox.information(self, "Vehicles Restarted", 
                                   "All vehicles have been reset to the depot and restarted their routes.")
        except Exception as e:
            print(f"Error showing restart message: {e}")
    
    def tick_vehicle_movement(self):
        """Main vehicle movement tick with optimized calculations"""
        if (not self.map_ready or not self.vehicles_started or self.vehicles_paused or 
            not self.vehicles or self._widgets_destroyed or self._shutdown_in_progress):
            return
        
        dt = 1.0 / 3600.0  # 1 second in hours
        vehicles_moved = False
        
        for name, v in self.vehicles.items():
            if v["route_index"] >= len(v["route"]) - 1:
                continue
            
            # Current segment
            lat1, lon1 = v["route"][v["route_index"]]
            lat2, lon2 = v["route"][v["route_index"] + 1]
            
            # Calculate distance (cache results to avoid recalculation)
            if not hasattr(v, 'segment_distance'):
                v['segment_distance'] = OptimizedRouteManager.haversine(lat1, lon1, lat2, lon2)
            
            dist = v['segment_distance']
            if dist == 0:
                v["route_index"] += 1
                v["progress"] = 0.0
                if 'segment_distance' in v:
                    del v['segment_distance']  # Clear cached distance
                if v["route_index"] < len(v["route"]):
                    v["pos"] = v["route"][v["route_index"]]
                vehicles_moved = True
                continue
            
            # Calculate movement
            step_km = v["speed"] * dt
            frac = step_km / dist
            v["progress"] += frac
            
            if v["progress"] >= 1.0:
                v["route_index"] += 1
                v["progress"] = 0.0
                if 'segment_distance' in v:
                    del v['segment_distance']  # Clear cached distance
                if v["route_index"] < len(v["route"]):
                    v["pos"] = v["route"][v["route_index"]]
            else:
                # Interpolate position
                v["pos"] = [
                    lat1 + (lat2 - lat1) * v["progress"],
                    lon1 + (lon2 - lon1) * v["progress"]
                ]
            
            vehicles_moved = True
        
        # Mark for map update instead of immediate update
        if vehicles_moved:
            self.pending_map_update = True
            
            # Update sidebar less frequently for performance
            if int(time.time()) % 3 == 0:  # Update every 3 seconds
                for name, v in self.vehicles.items():
                    try:
                        status = "Stopped" if self.vehicles_paused else "Moving"
                        speed = 0 if self.vehicles_paused else v["speed"]
                        vehicle_data = VehicleData(name, v["type"], v["pos"][0], v["pos"][1], status, speed)
                        if (self._is_valid_widget(self.vehicle_control) and 
                            hasattr(self.vehicle_control, 'update_vehicle_status')):
                            self.vehicle_control.update_vehicle_status(vehicle_data)
                    except Exception as e:
                        print(f"Error updating vehicle {name} status: {e}")
        
        # Check if all vehicles completed their routes
        if self.wave_running and self.all_vehicles_returned() and not self.wave_completed:
            self.wave_running = False
            self.wave_completed = True
            # Calculate wave statistics from backend data
            total_distance = sum(v.get("distance", 0) for v in self.vehicles.values())
            total_cost = sum(v.get("cost", 0) for v in self.vehicles.values())
            total_weight = sum(v.get("backend_weight", 0) for v in self.vehicles.values())
            total_deliveries = sum(len(v.get("all_deliveries", [])) for v in self.vehicles.values())
            
            print(f"Wave {self.current_wave + 1} completed!")
            print(f"  Total Distance: {total_distance:.2f} km")
            print(f"  Total Cost: ${total_cost:.2f}")
            print(f"  Total Weight: {total_weight:.2f} kg")
            print(f"  Total Deliveries: {total_deliveries}")
            
            # Calculate final statistics
            total_deliveries = sum(len(v.get("all_deliveries", [v["assigned_delivery"]])) for v in self.vehicles.values())
            total_unique_points = set()
            for v in self.vehicles.values():
                for delivery in v.get("all_deliveries", [v["assigned_delivery"]]):
                    total_unique_points.add(tuple(delivery))
                    
            # Check if there are more waves
            has_more_waves = hasattr(self, 'waves_data') and self.current_wave < len(self.waves_data) - 1
    
            if has_more_waves:
                # Show Next Wave button and start auto-timer
                if self._is_valid_widget(self.next_wave_action):
                    self.next_wave_action.setVisible(True)
                    self.next_wave_action.setText("⏭ Next Wave")
                    
                # Start 5-minute auto-start timer
                self.start_auto_next_wave_timer()
                
                # Update status bar
                try:
                    if hasattr(self, 'statusBar') and not self._widgets_destroyed:
                        self.statusBar().showMessage(
                            f"Wave {self.current_wave + 1} completed - "
                            f"{total_deliveries} deliveries | "
                            f"Distance: {total_distance:.2f} km | "
                            f"Cost: ${total_cost:.2f} | "
                            f"Weight: {total_weight:.2f} kg"
                        )
                except Exception as e:
                    print(f"Error updating completion status: {e}")
                    
                # Show notification
                try:
                    QMessageBox.information(
                        self,
                        f"Wave {self.current_wave + 1} Completed",
                        f"Wave {self.current_wave + 1} delivery cycle completed!\n\n"
                        f"Deliveries: {total_deliveries} assignments\n"
                        f"Distance: {total_distance:.2f} km\n"
                        f"Cost: ${total_cost:.2f}\n"
                        f"Weight: {total_weight:.2f} kg\n"
                        f"Vehicles: {len(self.vehicles)}\n\n"
                        f"Next wave will start automatically in 5 minutes."
                    )
                except Exception as e:
                    print(f"Error showing wave completion message: {e}")
            else:
                # Last wave completed - no more waves
                try:
                    if hasattr(self, 'statusBar') and not self._widgets_destroyed:
                        self.statusBar().showMessage(
                            f"Final wave completed - "
                            f"Fleet: {len(self.vehicles)} vehicles - "
                            f"Completed: {total_deliveries} delivery assignments covering {len(total_unique_points)} unique points"
                        )
                except Exception as e:
                    print(f"Error updating completion status: {e}")
                
                # Show completion message
                try:
                    total_waves = len(self.waves_data) if hasattr(self, 'waves_data') else 1
                    QMessageBox.information(
                        self,
                        "All Waves Completed",
                        f"All {total_waves} wave(s) completed successfully!\n\n"
                        f"Final wave statistics:\n"
                        f"• Completed: {total_deliveries} delivery assignments\n"
                        f"• Unique points: {len(total_unique_points)} points\n"
                        f"• Vehicles: {len(self.vehicles)}\n\n"
                        f"Fleet operations finished."
                    )
                except Exception as e:
                    print(f"Error showing final completion message: {e}")
    
    def all_vehicles_returned(self):
        """Check if all vehicles completed their routes"""
        for v in self.vehicles.values():
            if v["route_index"] < len(v["route"]) - 1:
                return False
        return True
    
    def change_depot_location(self):
        """Open depot selection dialog"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return
            
        if self.vehicles_started and self.vehicles:
            try:
                reply = QMessageBox.question(
                    self, 
                    "Change Configuration", 
                    "Changing depot location will stop all current vehicles and rebuild routes.\n\nContinue?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            except Exception as e:
                print(f"Error showing confirmation dialog: {e}")
                return
        
        try:
            depot_dialog = DepotSelectionWindow()
            depot_dialog.depot_selected.connect(self.on_new_depot_selected)
            depot_dialog.exec()
        except Exception as e:
            print(f"Error opening depot selection dialog: {e}")
    
    def on_new_depot_selected(self, lat, lng, customer_count, electric_trucks, fuel_trucks, drones):
        """Handle new depot and fleet configuration"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return

        # Store old values for comparison
        old_customer_count = self.customer_count
        old_total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones

        # Update configuration
        self.depot_coords = [lat, lng]
        self.customer_count = customer_count
        self.electric_trucks = electric_trucks
        self.fuel_trucks = fuel_trucks
        self.drones = drones

        # Stop current vehicles if running
        if self.vehicles_started:
            self.stop_vehicles_complete()

        # Regenerate delivery points
        self.delivery_points = self.generate_delivery_points_around_depot()

        # Process nodes and trigger backend computations using a separate thread
        self._start_backend_processing_for_new_depot()

        # Update UI components
        try:
            if self._is_valid_widget(self.delivery_info) and hasattr(self.delivery_info, 'update_depot'):
                self.delivery_info.update_depot(self.depot_coords, self.customer_count)
        except Exception as e:
            print(f"Error updating delivery info widget: {e}")

        self.update_depot_and_fleet_ui()

        # Force map update with new configuration
        if self.map_ready:
            self.reinitialize_map_optimized()

        # Show optimization summary
        new_total_vehicles = electric_trucks + fuel_trucks + drones
        avg_deliveries_per_vehicle = math.ceil(customer_count / max(1, new_total_vehicles))

        try:
            QMessageBox.information(
                self,
                "Configuration Updated",
                f"Depot and fleet configuration optimized:\n\n"
                f"📍 New Depot: {lat:.6f}, {lng:.6f}\n"
                f"👥 Customers: {old_customer_count} → {customer_count}\n"
                f"🚚 Fleet Size: {old_total_vehicles} → {new_total_vehicles} vehicles\n"
                f"📊 Avg deliveries per vehicle: ~{avg_deliveries_per_vehicle}\n\n"
                f"Fleet Breakdown:\n"
                f"• Electric Trucks: {electric_trucks}\n"
                f"• Fuel Trucks: {fuel_trucks}\n"
                f"• Drones: {drones}\n\n"
                f"System is ready for optimized operations with full delivery point coverage!"
            )
        except Exception as e:
            print(f"Error showing configuration update message: {e}")

    def _start_backend_processing_for_new_depot(self):
        """Start backend processing for new depot configuration using a separate thread"""
        from PyQt5.QtCore import QThread, pyqtSignal

        class DepotBackendProcessor(QThread):
            finished = pyqtSignal()
            error = pyqtSignal(str)

            def __init__(self, parent):
                super().__init__()
                self.parent = parent

            def run(self):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.parent.process_nodes_and_computations())

                    # Wait for backend to write file
                    import time
                    time.sleep(1)

                    # Load initial solution from file
                    initial_solution = self.parent.load_initial_solution_from_file()
                    if initial_solution:
                        self.parent.initial_solution = initial_solution
                        self.parent.parse_wave_information(initial_solution)

                    loop.close()
                    self.finished.emit()
                except Exception as e:
                    self.error.emit(str(e))

        # Create and start the processor thread
        self.depot_backend_processor = DepotBackendProcessor(self)
        self.depot_backend_processor.finished.connect(lambda: print("Depot backend processing thread finished"))
        self.depot_backend_processor.error.connect(lambda err: print(f"Depot backend processing error: {err}"))
        self.depot_backend_processor.start()
    def stop_vehicles_complete(self):
        """Completely stop and clear all vehicles with cleanup"""
        self.vehicles_started = False
        self.vehicles_paused = False
        self.wave_running = False
        
        # Cancel route building if in progress
        if self.route_builder and self.route_builder.isRunning():
            self.route_builder.requestInterruption()
            self.route_builder.quit()
            self.route_builder.wait(3000)  # Wait up to 3 seconds
        
        # Clean up progress dialog
        self._cleanup_progress_dialog()
        
        # Clear vehicles
        self.vehicles.clear()
        
        # Clear UI safely
        try:
            if (hasattr(self, 'vehicle_control') and 
                self._is_valid_widget(self.vehicle_control) and 
                hasattr(self.vehicle_control, 'status_list')):
                self.vehicle_control.status_list.clear()
        except Exception as e:
            print(f"Error clearing vehicle control: {e}")
        
        # Clear map
        if self.map_ready:
            try:
                self.map_view.page().runJavaScript("window.clearAllVehicles && window.clearAllVehicles();")
            except Exception as e:
                print(f"Error clearing map vehicles: {e}")
        
        # Reset UI buttons safely
        try:
            if hasattr(self, 'start_stop_action') and self._is_valid_widget(self.start_stop_action):
                self.start_stop_action.setChecked(False)
                self.start_stop_action.setText("▶ Start Vehicles")
                
            if hasattr(self, 'restart_action') and self._is_valid_widget(self.restart_action):
                self.restart_action.setVisible(False)
        except Exception as e:
            print(f"Error resetting UI buttons: {e}")
        
        print("All vehicles and routes cleared - system reset complete!")
    
    def reinitialize_map_optimized(self):
        """Reinitialize map showing all delivery points"""
        if not self.map_ready or self._widgets_destroyed:
            return

        # Show ALL delivery points
        essential_data = {
            "depot": self.depot_coords,
            "deliveries": self.delivery_points,  # Show ALL delivery points
            "total_deliveries": len(self.delivery_points)
        }

        js_code = f"""
        console.log('Updating map configuration with {len(self.delivery_points)} delivery points...');
        if (typeof window.updateMapConfiguration === 'function') {{
            window.updateMapConfiguration({json.dumps(essential_data)});
        }} else {{
            // Fallback to direct marker updates
            if (typeof map !== 'undefined') {{
                // Clear existing markers
                if (typeof depotMarker !== 'undefined' && depotMarker) {{
                    map.removeLayer(depotMarker);
                }}
                if (typeof deliveryMarkers !== 'undefined' && deliveryMarkers) {{
                    deliveryMarkers.forEach(m => map.removeLayer(m));
                }}

                // Add new depot marker
                var depotCoords = {json.dumps(self.depot_coords)};
                depotMarker = L.marker(depotCoords, {{
                    icon: L.divIcon({{
                        className: 'depot-marker',
                        html: '<div style="background: #ff6b35; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white;">🏢</div>',
                        iconSize: [20, 20]
                    }})
                }}).addTo(map);

                // Add ALL delivery markers
                deliveryMarkers = [];
                var deliveries = {json.dumps(self.delivery_points)};
                console.log('Adding ' + deliveries.length + ' delivery markers...');

                // Use smaller markers for large numbers to reduce visual clutter
                var markerSize = deliveries.length > 100 ? 12 : 16;
                var fontSize = deliveries.length > 100 ? '8px' : '10px';

                deliveries.forEach(function(coords, index) {{
                    var marker = L.marker(coords, {{
                        icon: L.divIcon({{
                            className: 'delivery-marker',
                            html: '<div style="background: #8b5cf6; color: white; border-radius: 50%; width: ' + markerSize + 'px; height: ' + markerSize + 'px; display: flex; align-items: center; justify-content: center; font-size: ' + fontSize + '; font-weight: bold; border: 1px solid white;">' + (index + 1) + '</div>',
                            iconSize: [markerSize, markerSize]
                        }})
                    }}).addTo(map);
                    deliveryMarkers.push(marker);
                }});

                console.log('Added ' + deliveryMarkers.length + ' delivery markers to map');

                // Center on depot
                map.setView(depotCoords, 6);  // Zoom out slightly for better overview with many points
            }}
        }}
        """

        try:
            self.map_view.page().runJavaScript(js_code)
            print(f"Map updated with depot at {self.depot_coords}, showing ALL {len(self.delivery_points)} delivery points")
        except Exception as e:
            print(f"Error reinitializing map: {e}")
    
    def update_depot_and_fleet_ui(self):
        """Update UI elements with new depot and fleet configuration"""
        try:
            self.update_status_bar()
            
            # Update left panel labels
            if self._is_valid_widget(self.depot_info_label):
                self._safe_set_text(self.depot_info_label, f"Depot: {self.depot_coords[0]:.4f}, {self.depot_coords[1]:.4f}")
            if self._is_valid_widget(self.customer_info_label):
                self._safe_set_text(self.customer_info_label, f"Customers: {self.customer_count}")
            if self._is_valid_widget(self.fleet_info_label):
                self._safe_set_text(self.fleet_info_label, f"Fleet: {self.electric_trucks}E + {self.fuel_trucks}F + {self.drones}D")
            if self._is_valid_widget(self.fleet_summary_label):
                total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
                self._safe_set_text(self.fleet_summary_label, f"Total Vehicles: {total_vehicles}")
        except Exception as e:
            print(f"Error updating depot and fleet UI: {e}")
    
    def setup_data_simulator(self):
        """Setup data simulation thread for sidebars"""
        try:
            self.data_simulator = DataSimulator()
            self.data_simulator.sound_data_updated.connect(self.on_sound_data_updated)
            self.data_simulator.start()
        except Exception as e:
            print(f"Error setting up data simulator: {e}")
            self.data_simulator = None
    
    def on_sound_data_updated(self, level, waveform):
        """Handle sound data updates for right sidebar"""
        if self._widgets_destroyed:
            return
            
        try:
            if hasattr(self, 'sound_graphs') and self._is_valid_widget(self.sound_graphs):
                if hasattr(self.sound_graphs, 'update_sound_data'):
                    self.sound_graphs.update_sound_data(level, waveform)
        except Exception as e:
            print(f"Error updating sound graphs: {e}")
            
        try:
            if hasattr(self, 'noise_stats') and self._is_valid_widget(self.noise_stats):
                if hasattr(self.noise_stats, 'update_statistics'):
                    self.noise_stats.update_statistics(level)
        except Exception as e:
            print(f"Error updating noise stats: {e}")
    
    def create_map_file(self):
        """Create or update the HTML map file with JavaScript"""
        try:
            self.map_path = os.path.abspath("map.html")
            with open(self.map_path, "w", encoding="utf-8") as f:
                f.write(HTML_TEMPLATE)
            self.map_view.setUrl(QUrl.fromLocalFile(self.map_path))
        except Exception as e:
            print(f"Error loading map content: {e}")
    
    def on_map_ready(self, success):
        """Initialize map when ready - shows all delivery points"""
        if not success:
            try:
                QMessageBox.critical(self, "Map Load Error", "Failed to load the map. Please check your internet connection.")
            except Exception as e:
                print(f"Error showing map load error dialog: {e}")
            return

        self.map_ready = True

        # Suggested depot locations
        suggested_locations = [
            {
                'name': 'Outskirts of Bangalore',
                'coords': [13.0500, 77.7500],
                'description': 'Good connectivity, away from airport NFZ'
            },
            {
                'name': 'Chennai Surroundings',
                'coords': [12.8500, 80.0500],
                'description': 'Industrial area, good for logistics'
            },
            {
                'name': 'Mumbai Suburbs',
                'coords': [19.2000, 72.9500],
                'description': 'Outside nuclear facility zone'
            },
            {
                'name': 'Delhi NCR Edge',
                'coords': [28.4000, 77.3000],
                'description': 'Away from airport and government areas'
            },
            {
                'name': 'Hyderabad Outskirts',
                'coords': [17.1000, 78.6000],
                'description': 'Developing logistics hub'
            },
            {
                'name': 'Pune Industrial Area',
                'coords': [18.4000, 73.7000],
                'description': 'Away from air force station'
            }
        ]

        # Show ALL delivery points
        basic_data = {
            "center": self.map_center,
            "zoom": self.map_zoom,
            "depot": self.depot_coords,
            "deliveries": self.delivery_points,  # Show ALL delivery points
            "total_deliveries": len(self.delivery_points),
            "cities": [
                {'name': 'New Delhi', 'coords': [28.6139, 77.2090]},
                {'name': 'Mumbai', 'coords': [19.0760, 72.8777]},
                {'name': 'Bangalore', 'coords': [12.9716, 77.5946]},
                {'name': 'Chennai', 'coords': [13.0827, 80.2707]},
                {'name': 'Kolkata', 'coords': [22.5726, 88.3639]},
                {'name': 'Hyderabad', 'coords': [17.3850, 78.4867]},
                {'name': 'Pune', 'coords': [18.5204, 73.8567]},
                {'name': 'Ahmedabad', 'coords': [23.0225, 72.5714]}
            ],
            "nfzones": self.no_fly_zones,
            "suggested": suggested_locations
        }

        js_code = f"""
        console.log('Initializing map with {len(self.delivery_points)} delivery points...');
        if (typeof window.initializeOptimizedMap === 'function') {{
            window.initializeOptimizedMap({json.dumps(basic_data)});
        }} else if (typeof window.initializeMap === 'function') {{
            window.initializeMap({json.dumps(basic_data)});
        }}
        """

        try:
            self.map_view.page().runJavaScript(js_code)
        except Exception as e:
            print(f"Error initializing map: {e}")

        total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
        avg_deliveries = math.ceil(len(self.delivery_points) / max(1, total_vehicles))

        print(f"✅ Map initialized with ALL {len(self.delivery_points)} delivery points!")
        print(f"Configuration: {len(self.delivery_points)} delivery points, {total_vehicles} vehicles (~{avg_deliveries} deliveries per vehicle)")
    
    def toggle_no_fly_zones(self):
        """Toggle no-fly zones visibility"""
        if self.map_ready and not self._widgets_destroyed:
            try:
                show = self.toggle_nfz_action.isChecked()
                js_code = f"window.toggleNoFlyZonesOptimized && window.toggleNoFlyZonesOptimized({str(show).lower()});"
                self.map_view.page().runJavaScript(js_code)
            except Exception as e:
                print(f"Error toggling no-fly zones: {e}")
    
    def toggle_vehicles(self):
        """Toggle vehicles visibility"""
        if self.map_ready and not self._widgets_destroyed:
            try:
                show = self.toggle_vehicles_action.isChecked()
                js_code = f"window.toggleVehiclesOptimized && window.toggleVehiclesOptimized({str(show).lower()});"
                self.map_view.page().runJavaScript(js_code)
                
                if show and self.vehicles:
                    # Delay vehicle display to prevent blocking
                    QTimer.singleShot(500, self.send_vehicles_to_js_batch)
            except Exception as e:
                print(f"Error toggling vehicles: {e}")
    
    def closeEvent(self, event):
        """Clean up resources on close with comprehensive error handling"""
        print("Shutting down optimized fleet system...")
        self._shutdown_in_progress = True
        
        # Clean up progress dialog first
        self._cleanup_progress_dialog()
        
        # Stop auto next wave timer
        try:
            if hasattr(self, 'auto_next_wave_timer') and self.auto_next_wave_timer:
                self.auto_next_wave_timer.stop()
                self.auto_next_wave_timer = None
        except Exception as e:
            print(f"Error stopping auto next wave timer: {e}")
        
        try:
            # Stop timers
            if hasattr(self, 'timer'):
                self.timer.stop()
        except Exception as e:
            print(f"Error stopping main timer: {e}")
            
        try:
            if hasattr(self, 'map_update_timer'):
                self.map_update_timer.stop()
        except Exception as e:
            print(f"Error stopping map update timer: {e}")
        
        # Stop background threads
        try:
            if hasattr(self, 'route_builder') and self.route_builder:
                if self.route_builder.isRunning():
                    self.route_builder.requestInterruption()
                    self.route_builder.quit()
                    self.route_builder.wait(3000)  # Wait up to 3 seconds
        except Exception as e:
            print(f"Error stopping route builder: {e}")
        
        try:
            if hasattr(self, 'data_simulator') and self.data_simulator:
                self.data_simulator.stop()
                self.data_simulator.wait(2000)  # Wait up to 2 seconds
        except Exception as e:
            print(f"Error stopping data simulator: {e}")
        
        # Mark widgets as destroyed
        self._widgets_destroyed = True
        
        # Clear route cache
        try:
            OptimizedRouteManager.clear_cache()
            print("Route cache cleared")
        except Exception as e:
            print(f"Error clearing route cache: {e}")
        
        # Clean up map file
        try:
            if hasattr(self, 'map_path') and os.path.exists(self.map_path):
                os.remove(self.map_path)
                print(f"Cleaned up map file: {self.map_path}")
        except Exception as e:
            print(f"Warning: Could not clean up map file: {e}")
        
        print("Shutdown complete.")
        event.accept()


class ImprovedDeliveryAssigner:
    """Improved delivery assignment that ensures ALL points are covered"""
    
    @staticmethod
    def create_complete_assignments(delivery_points: List[List[float]], 
                                  electric_trucks: int, fuel_trucks: int, drones: int) -> Dict:
        """
        Create assignments ensuring EVERY delivery point gets covered
        Uses intelligent distribution and multi-delivery assignments
        """
        total_vehicles = electric_trucks + fuel_trucks + drones
        total_points = len(delivery_points)
        
        print(f"\n=== COMPLETE DELIVERY ASSIGNMENT ===")
        print(f"Delivery points: {total_points}")
        print(f"Total vehicles: {total_vehicles}")
        
        if total_vehicles == 0:
            print("ERROR: No vehicles available for assignment!")
            return {}
        
        print(f"Points per vehicle (avg): {total_points / total_vehicles:.1f}")
        
        assignments = {}
        
        # Create vehicle pool
        vehicle_pool = []
        vehicle_pool.extend([("Drone", i+1) for i in range(drones)])
        vehicle_pool.extend([("Electric Truck", i+1) for i in range(electric_trucks)])
        vehicle_pool.extend([("Fuel Truck", i+1) for i in range(fuel_trucks)])
        
        # Distribute ALL delivery points using round-robin
        points_per_vehicle = math.ceil(total_points / total_vehicles)
        print(f"Strategy: Each vehicle handles up to {points_per_vehicle} deliveries")
        
        # Assign delivery points in round-robin fashion to ensure complete coverage
        for i, delivery_point in enumerate(delivery_points):
            vehicle_index = i % total_vehicles
            vehicle_type, vehicle_num = vehicle_pool[vehicle_index]
            vehicle_name = f"{vehicle_type} {vehicle_num}"
            
            if vehicle_name not in assignments:
                assignments[vehicle_name] = {
                    "type": vehicle_type,
                    "primary_delivery": delivery_point[:],  # Primary delivery for route building
                    "all_deliveries": [delivery_point[:]]   # All deliveries for this vehicle
                }
            else:
                assignments[vehicle_name]["all_deliveries"].append(delivery_point[:])
        
        # Verify complete coverage
        total_assigned = sum(len(assignment["all_deliveries"]) for assignment in assignments.values())
        unique_points = set()
        for assignment in assignments.values():
            for delivery in assignment["all_deliveries"]:
                unique_points.add(tuple(delivery))
        
        coverage_percentage = (len(unique_points) / total_points) * 100
        
        print(f"Assignment Results:")
        for vehicle_name, assignment in assignments.items():
            deliveries_count = len(assignment["all_deliveries"])
            print(f"  {vehicle_name}: {deliveries_count} deliveries")
        
        print(f"Total assigned: {total_assigned} delivery assignments")
        print(f"Unique points covered: {len(unique_points)}/{total_points} points ({coverage_percentage:.1f}% coverage)")
        
        if len(unique_points) == total_points:
            print("✅ SUCCESS: All delivery points assigned!")
        else:
            print(f"❌ ERROR: {total_points - len(unique_points)} points not assigned!")
        
        return assignments

