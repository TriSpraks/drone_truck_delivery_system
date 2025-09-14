"""
COMPLETE OPTIMIZED Main application window for India Airspace Management System
Fixed route allocation, improved performance, and proper delivery point coverage
CORRECTED VERSION - Clean integration with unified route manager
"""
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
from utils.nfz_data import get_depot_selection_no_fly_zones
from resources.map_templates import HTML_TEMPLATE
from ui.dialog import DepotSelectionWindow


class OptimizedRouteBuilder(QThread):
    """Background thread for building routes with improved allocation"""
    route_completed = pyqtSignal(str, list)  # vehicle_name, route
    progress_updated = pyqtSignal(int, str)  # progress, status
    all_routes_completed = pyqtSignal(dict)  # all_vehicles_dict
    
    def __init__(self, depot_coords, delivery_assignments, parent=None):
        super().__init__(parent)
        self.depot_coords = depot_coords
        self.delivery_assignments = delivery_assignments
        self.vehicles = {}
        self.mutex = QMutex()
        
    def run(self):
        """Build all routes using optimized batch processing"""
        try:
            self.progress_updated.emit(10, "Initializing batch route builder...")
            
            # Use the corrected unified route manager
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
                        "weight": random.randint(*VEHICLE_WEIGHTS[assignment["type"]]),
                        "volume": random.randint(10000, 80000),  # Add volume in cm³ (10-80 liters)
                        "assigned_delivery": assignment["primary_delivery"],
                        "all_deliveries": route_data.get("all_deliveries", [assignment["primary_delivery"]])
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
        self.no_fly_zones = get_depot_selection_no_fly_zones()
        
        # Vehicle system
        self.vehicles = {}
        self.current_wave = 0
        self.wave_running = False
        self.wave_start_time = 0.0
        self.vehicles_started = False
        self.vehicles_paused = False
        
        # Route building thread
        self.route_builder = None
        self.progress_dialog = None
        
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

    def start_backend_processing(self):
        """Start backend processing asynchronously in a separate thread"""
        from PyQt5.QtCore import QThread, pyqtSignal

        class BackendProcessor(QThread):
            finished = pyqtSignal()
            error = pyqtSignal(str)

            def run(self):
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.process_nodes_and_computations())
                    loop.close()
                    self.finished.emit()
                except Exception as e:
                    self.error.emit(str(e))

            async def process_nodes_and_computations(self):
                """Async method to process nodes and trigger automatic backend computations"""
                try:
                    # Insert nodes to backend (this will automatically trigger computations)
                    insert_success = await self.insert_nodes_to_backend()
                    if not insert_success:
                        print("Node insertion and computation failed")
                        return

                    print("Backend processing completed successfully (nodes inserted and computations triggered automatically)")

                except Exception as e:
                    print(f"❌ Error in backend processing: {e}")

            async def insert_nodes_to_backend(self):
                """Insert generated delivery points to backend database via API"""
                if not hasattr(self.parent, 'customer_nodes') or not self.parent.customer_nodes:
                    print("No customer nodes to insert")
                    return False

                try:
                    # Prepare nodes data for backend API
                    nodes_data = []
                    for node in self.parent.customer_nodes:
                        nodes_data.append({
                            "node_id": node["node_id"],
                            "weight": node["weight"],
                            "volume": node["volume"],
                            "lon": node["lon"],
                            "lat": node["lat"]
                        })

                    # Add depot node
                    if hasattr(self.parent, 'depot_node'):
                        nodes_data.insert(0, {
                            "node_id": self.parent.depot_node["node_id"],
                            "weight": self.parent.depot_node["weight"],
                            "volume": self.parent.depot_node["volume"],
                            "lon": self.parent.depot_node["lon"],
                            "lat": self.parent.depot_node["lat"]
                        })

                    print(f"Inserting {len(nodes_data)} nodes to backend database...")

                    # Insert nodes via backend API
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            "http://127.0.0.1:8000/api/nodes/insert",
                            json=nodes_data,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                print(f"Successfully inserted {result.get('inserted', 0)} nodes to backend")
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



        # Create and start the processor thread
        self.backend_processor = BackendProcessor()
        self.backend_processor.parent = self  # Pass reference to parent
        self.backend_processor.finished.connect(lambda: print("Backend processing thread finished"))
        self.backend_processor.error.connect(lambda err: print(f"Backend processing error: {err}"))
        self.backend_processor.start()
    
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
        """Generate delivery points with improved distribution"""
        points = []
        depot_lat, depot_lon = self.depot_coords
    
        # First, add the depot node
        depot_node = {
            "node_id": "depot",             # Unique ID
            "type": "depot",                # Node type (used in routing logic)
            "weight": 0,                    # Depot has no demand
            "volume": 0,                    # Depot has no demand
            "lon": depot_lon,               # Longitude from depot coords
            "lat": depot_lat,               # Latitude from depot coords
            "coords": [depot_lat, depot_lon]  # Keep original coords format for compatibility
        }
    
        # Create points in concentric circles for better coverage
        circles = min(5, max(1, self.customer_count // 15))  # Better circle calculation
        points_per_circle = self.customer_count // circles
        remaining_points = self.customer_count % circles
    
        for circle in range(circles):
            circle_points = points_per_circle + (1 if circle < remaining_points else 0)
            base_distance = 10 + (circle * 15)  # 10km, 25km, 40km, etc.
        
            for i in range(circle_points):
                # Better angle distribution to avoid clustering
                angle = (i * (360 / max(1, circle_points))) + random.uniform(-8, 8)
                distance_km = base_distance + random.uniform(-2, 10)
            
                # Convert to lat/lon offset
                lat_offset = (distance_km / 111.32) * math.cos(math.radians(angle))
                lon_offset = (distance_km / (111.32 * math.cos(math.radians(depot_lat)))) * math.sin(math.radians(angle))
            
                point_lat = depot_lat + lat_offset
                point_lon = depot_lon + lon_offset
            
                # Generate volume for customer (using normal distribution)
                volume = max(1000, random.normalvariate(50000, 20000))  # Volume in cm³, minimum 1000
            
                # Create customer node
                customer_node = {
                    "node_id": f"cust_{len(points) + 1}",      # Unique ID (cust_1, cust_2, ...)
                    "type": "customer",                        # Node type
                    "weight": random.uniform(1.0, 5.0),       # Customer weight in kg
                    "volume": round(volume, 0),                # Volume in cm³, rounded
                    "lon": point_lon,                          # Longitude
                    "lat": point_lat,                          # Latitude
                    "coords": [point_lat, point_lon]           # Keep original coords format for compatibility
                }
            
                points.append(customer_node)
    
    # Shuffle for random assignment
        random.shuffle(points)
    
    # Return list that includes depot + customer points, but maintain original format for backwards compatibility
    # The function originally returned just coordinate lists, so we'll return the coords but store the full data
        self.depot_node = depot_node  # Store depot data as instance variable
        self.customer_nodes = points  # Store customer data as instance variables
    
    # Return coordinate lists for backward compatibility
        return [point["coords"] for point in points]

    async def insert_nodes_to_backend(self):
        """Insert generated delivery points to backend database via API"""
        if not hasattr(self, 'customer_nodes') or not self.customer_nodes:
            print("No customer nodes to insert")
            return False

        try:
            # Prepare nodes data for backend API
            nodes_data = []
            for node in self.customer_nodes:
                nodes_data.append({
                    "node_id": node["node_id"],
                    "weight": node["weight"],
                    "volume": node["volume"],
                    "lon": node["lon"],
                    "lat": node["lat"]
                })

            # Add depot node
            if hasattr(self, 'depot_node'):
                nodes_data.insert(0, {
                    "node_id": self.depot_node["node_id"],
                    "weight": self.depot_node["weight"],
                    "volume": self.depot_node["volume"],
                    "lon": self.depot_node["lon"],
                    "lat": self.depot_node["lat"]
                })

            print(f"Inserting {len(nodes_data)} nodes to backend database...")

            # Insert nodes via backend API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://127.0.0.1:8000/api/nodes/insert",
                    json=nodes_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"Successfully inserted {result.get('inserted', 0)} nodes to backend")
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
        """Process node insertion and backend computations"""
        try:
            # Insert nodes to backend
            insert_success = await self.insert_nodes_to_backend()
            if not insert_success:
                print("Node insertion failed, skipping computations")
                return False

            # Trigger backend computations
            compute_success = await self.trigger_backend_computations()
            if compute_success:
                print("✅ Backend processing completed successfully")
                return True
            else:
                print("Backend computations failed")
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
            left_panel.setMaximumWidth(300)
            left_panel.setMinimumWidth(250)
            left_layout = QVBoxLayout(left_panel)
            
            # Logo/Title
            title_label = QLabel("Optimized Delivery System")
            title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ff6b35; padding: 10px;")
            title_label.setAlignment(Qt.AlignCenter)
            
            # Depot and fleet configuration info
            depot_info = QLabel(f"Depot: {self.depot_coords[0]:.4f}, {self.depot_coords[1]:.4f}")
            depot_info.setStyleSheet("font-size: 12px; color: #cccccc; padding: 5px; text-align: center;")
            depot_info.setAlignment(Qt.AlignCenter)
            
            customer_info = QLabel(f"Customers: {self.customer_count}")
            customer_info.setStyleSheet("font-size: 12px; color: #8b5cf6; font-weight: bold; padding: 5px; text-align: center;")
            customer_info.setAlignment(Qt.AlignCenter)
            
            # Fleet configuration display
            fleet_info = QLabel(f"Fleet: {self.electric_trucks}E + {self.fuel_trucks}F + {self.drones}D")
            fleet_info.setStyleSheet("font-size: 12px; color: #4CAF50; font-weight: bold; padding: 5px; text-align: center;")
            fleet_info.setAlignment(Qt.AlignCenter)
            
            total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
            fleet_summary = QLabel(f"Total Vehicles: {total_vehicles}")
            fleet_summary.setStyleSheet("font-size: 11px; color: #FF9800; padding: 2px; text-align: center;")
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
            sound_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff6b35; padding: 5px;")
            
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
    
    def start_vehicles_optimized(self):
        """Start vehicles with optimized route building"""
        if self._widgets_destroyed or self._shutdown_in_progress:
            return False
            
        if not self.map_ready:
            QMessageBox.warning(self, "Map Not Ready", "Please wait for the map to finish loading.")
            return False
        
        if not self.vehicles_started:
            # Create optimal delivery assignments with FULL coverage
            delivery_assignments = self.create_optimal_delivery_assignments()
            
            if not delivery_assignments:
                QMessageBox.warning(self, "No Assignments", "No delivery assignments could be created.")
                return False
            
            # Verify all points are assigned before proceeding
            total_assigned = sum(len(assignment["all_deliveries"]) for assignment in delivery_assignments.values())
            if total_assigned < len(self.delivery_points):
                print(f"WARNING: Only {total_assigned}/{len(self.delivery_points)} points assigned!")
            
            # Thread-safe progress dialog creation
            self._progress_mutex.lock()
            try:
                if self.progress_dialog is None:
                    self.progress_dialog = QProgressDialog("Building optimized routes...", "Cancel", 0, 100, self)
                    self.progress_dialog.setWindowTitle("Optimizing Fleet Routes")
                    self.progress_dialog.setModal(True)
                    self.progress_dialog.show()
            finally:
                self._progress_mutex.unlock()
            
            # Start background route building
            self.route_builder = OptimizedRouteBuilder(self.depot_coords, delivery_assignments, self)
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
        
        # Clean up progress dialog
        self._cleanup_progress_dialog()
        
        # Store vehicles and start simulation
        self.vehicles = vehicles_dict
        self.wave_running = True
        self.wave_start_time = time.time()
        
        # Update UI
        self.update_all_vehicle_statuses("Moving")
        
        # Send to map in batches for better performance
        self.send_vehicles_to_js_batch()
        
        # Calculate actual coverage
        total_unique_deliveries = set()
        total_delivery_assignments = 0
        
        for vehicle_name, vehicle_data in self.vehicles.items():
            # Count all deliveries assigned to this vehicle
            all_deliveries = vehicle_data.get("all_deliveries", [vehicle_data["assigned_delivery"]])
            total_delivery_assignments += len(all_deliveries)
            
            # Add to unique set
            for delivery in all_deliveries:
                total_unique_deliveries.add(tuple(delivery))
        
        print(f"✅ Fleet optimization completed!")
        print(f"Created {len(self.vehicles)} vehicles")
        print(f"Total delivery assignments: {total_delivery_assignments}")
        print(f"Unique delivery points covered: {len(total_unique_deliveries)}/{len(self.delivery_points)}")
        
        try:
            coverage_percentage = (len(total_unique_deliveries) / len(self.delivery_points)) * 100
            QMessageBox.information(
                self,
                "Fleet Optimized",
                f"Fleet optimization completed!\n\n"
                f"• Created: {len(self.vehicles)} vehicles\n"
                f"• Delivery assignments: {total_delivery_assignments}\n"
                f"• Unique points covered: {len(total_unique_deliveries)}/{len(self.delivery_points)} ({coverage_percentage:.1f}%)\n"
                f"• Route building time: {time.time() - self.wave_start_time:.1f} seconds\n\n"
                f"Note: Vehicles will handle multiple delivery points through optimized multi-stop routing."
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
        if self.wave_running and self.all_vehicles_returned():
            self.wave_running = False
            print(f"All vehicles completed their delivery routes!")
            
            # Calculate final statistics
            total_deliveries = sum(len(v.get("all_deliveries", [v["assigned_delivery"]])) for v in self.vehicles.values())
            total_unique_points = set()
            for v in self.vehicles.values():
                for delivery in v.get("all_deliveries", [v["assigned_delivery"]]):
                    total_unique_points.add(tuple(delivery))
            
            # Update status bar
            try:
                if hasattr(self, 'statusBar') and not self._widgets_destroyed:
                    self.statusBar().showMessage(
                        f"Delivery cycle completed - "
                        f"Fleet: {len(self.vehicles)} vehicles - "
                        f"Completed: {total_deliveries} delivery assignments covering {len(total_unique_points)} unique points"
                    )
            except Exception as e:
                print(f"Error updating completion status: {e}")
    
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

        # Process nodes and trigger backend computations
        asyncio.create_task(self.process_nodes_and_computations())
        
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
        """Create the HTML map file with JavaScript"""
        try:
            timestamp = str(int(time.time() * 1000))
            self.map_path = os.path.abspath(f"optimized_map_{timestamp}.html")
            with open(self.map_path, "w", encoding="utf-8") as f:
                f.write(HTML_TEMPLATE)
            self.map_view.setUrl(QUrl.fromLocalFile(self.map_path))
        except Exception as e:
            print(f"Error creating map file: {e}")
    
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

