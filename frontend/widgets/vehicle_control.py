"""
Vehicle control panel widget - DISPLAYS ACTUAL BACKEND SOLUTION DATA
Shows real vehicle assignments and live tracking from solution.json

FILE LOCATION: frontend/widgets/vehicle_control.py
"""
import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                           QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer


class VehicleControlPanel(QWidget):
    """Control panel for vehicle tracking with backend data"""
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.current_solution = None
        self.last_solution_hash = None
        self.vehicle_data_cache = {}
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_vehicle_data)
        self.refresh_timer.start(1000)  # Refresh every 1 second for live updates
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status display with backend data
        status_group = QGroupBox("Vehicle Status (Backend Data)")
        status_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                background-color: #2a2a2a;
                padding: 15px;
                border-radius: 4px;
                margin-top: 10px;
                border: 1px solid #3a3a3a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ff6b35;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        
        status_layout = QVBoxLayout(status_group)
        
        # Vehicle list
        self.status_list = QListWidget()
        self.status_list.setMinimumHeight(150)
        self.status_list.setWordWrap(True)
        self.status_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.status_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 2px;
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #ff6b35;
                color: white;
                border-color: #ff6b35;
            }
            QListWidget::item:hover {
                background-color: #4d4d4d;
                border-color: #ff6b35;
            }
            QScrollBar:vertical {
                width: 12px;
                border-radius: 5px;
            }
        """)
        
        status_layout.addWidget(self.status_list, 1)
        layout.addWidget(status_group, 1)
        
        # Load initial data
        self.load_backend_solution()
    
    def load_backend_solution(self):
        """Load backend solution data after backend processing completes"""
        try:
            # First try to get shared solution data from main window
            if hasattr(self.parent_window, 'shared_solution_data') and self.parent_window.shared_solution_data:
                solution = self.parent_window.shared_solution_data
            else:
                # Fallback to API fetch if shared data not available
                # Check if backend processing is still in progress
                if hasattr(self.parent_window, '_backend_processing') and self.parent_window._backend_processing:
                    print("[VehicleControl] Backend still processing, skipping solution fetch")
                    self.show_no_solution_message()
                    return

                import aiohttp
                import asyncio

                async def fetch_solution():
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            "https://trispark.onrender.com/api/solution",
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            if response.status == 200:
                                return await response.json()
                            else:
                                print(f"[VehicleControl] API error: {response.status}")
                                return None

                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    solution = loop.run_until_complete(fetch_solution())
                finally:
                    loop.close()

            if solution:
                self.current_solution = solution
                self.display_backend_vehicles(solution)
            else:
                self.show_no_solution_message()

        except Exception as e:
            print(f"Error loading backend solution: {e}")
            self.show_error_message(str(e))
    
    def refresh_vehicle_data(self):
        """Refresh vehicle data - fetch once after backend completion, no polling during processing"""
        if self.parent_window and hasattr(self.parent_window, 'vehicle_manager'):
            vm = self.parent_window.vehicle_manager
            if vm.vehicles_started and vm.vehicles:
                # Update with live data when vehicles are running
                self.update_live_vehicle_status(vm.vehicles)
                return  # Continue polling for live updates

        # Only fetch when backend is complete
        if hasattr(self.parent_window, '_backend_ready') and self.parent_window._backend_ready:
            # If we already have solution data, stop polling
            if self.current_solution and self.refresh_timer.isActive():
                self.refresh_timer.stop()
                return

            # Fetch solution data once
            solution = None

            # First priority: shared solution data from main window
            if hasattr(self.parent_window, 'shared_solution_data') and self.parent_window.shared_solution_data:
                solution = self.parent_window.shared_solution_data
            # Second priority: API fetch
            else:
                try:
                    import aiohttp
                    import asyncio

                    async def fetch_solution():
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                "https://trispark.onrender.com/api/solution",
                                timeout=aiohttp.ClientTimeout(total=10)
                            ) as response:
                                if response.status == 200:
                                    return await response.json()
                                else:
                                    return None

                    # Run async function in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        solution = loop.run_until_complete(fetch_solution())
                    finally:
                        loop.close()
                except Exception as e:
                    print(f"[VehicleControl] Error fetching solution: {e}")
                    solution = None

            if solution:
                solution_str = json.dumps(solution, sort_keys=True)
                solution_hash = hash(solution_str)

                if solution_hash != self.last_solution_hash:
                    self.last_solution_hash = solution_hash
                    self.current_solution = solution
                    self.display_backend_vehicles(solution)

                # Stop polling after fetching
                if self.refresh_timer.isActive():
                    self.refresh_timer.stop()
        elif not self.current_solution:
            # Try to load solution if not available
            self.load_backend_solution()
    
    def display_backend_vehicles(self, solution):
        """Display vehicle assignments from backend solution - ADAPTIVE PARSING"""
        try:
            self.status_list.clear()

            print(f"[VehicleControl] Solution keys: {solution.keys()}")

            # ADAPTIVE: Try different ways to get wave data
            waves = None

            # Try 1: waves array
            if 'waves' in solution and isinstance(solution['waves'], list):
                waves = solution['waves']
                print(f"[VehicleControl] Found waves array with {len(waves)} waves")

            # Try 2: Check if top-level has wave_X keys
            elif any(key.startswith('wave_') for key in solution.keys()):
                print(f"[VehicleControl] Found wave_X structure in solution")
                wave_keys = sorted([k for k in solution.keys() if k.startswith('wave_')])
                waves = [solution[k] for k in wave_keys]
                print(f"[VehicleControl] Extracted {len(waves)} waves")

            if not waves:
                print(f"[VehicleControl] No waves found. Solution structure: {json.dumps(solution, indent=2)[:500]}")
                self.status_list.addItem("⏳ Waiting for backend solution...")
                self.status_list.addItem("")
                self.status_list.addItem("Backend optimization is processing")
                return

            current_wave = waves[0]
            wave_num = current_wave.get('wave_number', 1)
            print(f"[VehicleControl] Processing first wave. Keys: {current_wave.keys()}")

            # Header
            header_item = QListWidgetItem(f"═══ WAVE {wave_num} ASSIGNMENTS ═══")
            header_item.setForeground(Qt.yellow)
            self.status_list.addItem(header_item)

            # Display drones
            drones = current_wave.get('drones', [])
            print(f"[VehicleControl] Found {len(drones)} drones")
            for i, drone in enumerate(drones, 1):
                self.add_vehicle_item(drone, "Drone", "🚁")

            # Display trucks
            trucks = current_wave.get('trucks', [])
            print(f"[VehicleControl] Found {len(trucks)} trucks")
            for truck in trucks:
                vehicle_id = truck.get('vehicle_id', '')
                if "E_Truck" in vehicle_id:
                    self.add_vehicle_item(truck, "E-Truck", "🔋")
                else:
                    self.add_vehicle_item(truck, "F-Truck", "⛽")

        except Exception as e:
            print(f"Error displaying vehicles: {e}")
            self.status_list.addItem(f"❌ Error: {str(e)}")
    
    def add_vehicle_item(self, vehicle_data, vehicle_type, icon):
        """Add a vehicle item to the list"""
        vehicle_id = vehicle_data.get('vehicle_id', 'Unknown')
        node_ids = vehicle_data.get('node_ids', [])
        distance = vehicle_data.get('distance', 0)
        cost = vehicle_data.get('cost', 0)
        weight = vehicle_data.get('total_weight', 0)
        volume = vehicle_data.get('total_volume', 0)
        capacity = vehicle_data.get('capacity_utilization', {})
        
        status_text = f"{icon} {vehicle_id}\n"
        status_text += f"Type: {vehicle_type}\n"
        status_text += f"Deliveries: {len(node_ids)} nodes\n"
        status_text += f"Distance: {distance:.2f} km\n"
        status_text += f"Cost: {cost:.2f}\n"
        status_text += f"Weight: {weight:.2f} kg"
        
        if capacity:
            status_text += f" ({capacity.get('weight_percent', 0):.1f}%)"
        
        status_text += f"\nVolume: {volume:.0f} cm³"
        
        if capacity:
            status_text += f" ({capacity.get('volume_percent', 0):.1f}%)"
        
        status_text += f"\nStatus: 🟡 Ready to dispatch"
        
        self.status_list.addItem(status_text)
    
    def update_live_vehicle_status(self, vehicles_dict):
        """Update with live vehicle tracking data"""
        try:
            self.status_list.clear()
            
            # Header
            header_item = QListWidgetItem("═══ LIVE VEHICLE TRACKING ═══")
            header_item.setForeground(Qt.green)
            self.status_list.addItem(header_item)
            
            for vehicle_name, vehicle in vehicles_dict.items():
                # Get backend data if available
                backend_weight = vehicle.get('backend_weight', vehicle.get('weight', 0))
                backend_volume = vehicle.get('backend_volume', vehicle.get('volume', 0))
                backend_distance = vehicle.get('distance', 0)
                backend_cost = vehicle.get('cost', 0)
                
                # Determine status
                paused = self.parent_window.vehicle_manager.vehicles_paused
                completed = vehicle.get('route_index', 0) >= len(vehicle.get('route', [])) - 1
                
                if completed:
                    status_icon = "✅"
                    status_text = "Completed"
                elif paused:
                    status_icon = "⏸"
                    status_text = "Paused"
                else:
                    status_icon = "🟢"
                    status_text = "Moving"
                
                # Get icon
                v_type = vehicle.get('type', '')
                if 'Drone' in v_type:
                    icon = "🚁"
                elif 'Electric' in v_type:
                    icon = "🔋"
                else:
                    icon = "⛽"
                
                # Build status text
                item_text = f"{icon} {vehicle_name}\n"
                item_text += f"Type: {v_type}\n"
                item_text += f"Status: {status_icon} {status_text}\n"
                
                # Position
                pos = vehicle.get('pos', [0, 0])
                item_text += f"Position:\n"
                item_text += f"  Lat: {pos[0]:.6f}\n"
                item_text += f"  Lon: {pos[1]:.6f}\n"
                
                # Backend metrics
                item_text += f"Distance: {backend_distance:.2f} km\n"
                item_text += f"Cost: {backend_cost:.2f}\n"
                item_text += f"Weight: {backend_weight:.2f} kg\n"
                item_text += f"Volume: {backend_volume:.0f} cm³\n"
                
                # Progress
                route_idx = vehicle.get('route_index', 0)
                route_len = len(vehicle.get('route', []))
                if route_len > 0:
                    progress_pct = (route_idx / max(route_len - 1, 1)) * 100
                    item_text += f"Progress: {progress_pct:.1f}%"
                
                self.status_list.addItem(item_text)
                
        except Exception as e:
            print(f"Error updating live status: {e}")
    
    def update_vehicle_status(self, vehicle_data):
        """Update single vehicle status (legacy compatibility)"""
        # Check if we should use live tracking
        if self.parent_window and hasattr(self.parent_window, 'vehicle_manager'):
            vm = self.parent_window.vehicle_manager
            if vm.vehicles_started and vm.vehicles:
                # Use full live update instead
                self.update_live_vehicle_status(vm.vehicles)
                return
        
        # Legacy single vehicle update
        status_text = f"🚁 {vehicle_data.vehicle_id}\n"
        status_text += f"Type: {vehicle_data.vehicle_type}\n"
        
        status_icon = "🟢" if vehicle_data.status == "Moving" else "🔴" if vehicle_data.status == "Stopped" else "🟡"
        status_text += f"Status: {status_icon} {vehicle_data.status}\n"
        
        status_text += f"Speed: {vehicle_data.speed:.1f} km/h\n"
        status_text += f"Position:\n"
        status_text += f"Lat: {vehicle_data.lat:.6f}\n"
        status_text += f"Lon: {vehicle_data.lon:.6f}"
        
        # Find existing item or create new
        found = False
        for i in range(self.status_list.count()):
            item = self.status_list.item(i)
            if vehicle_data.vehicle_id in item.text():
                item.setText(status_text)
                found = True
                break
        
        if not found:
            self.status_list.addItem(status_text)
    
    def show_no_solution_message(self):
        """Show message when no solution available"""
        self.status_list.clear()
        self.status_list.addItem("⏳ Waiting for backend solution...")
        self.status_list.addItem("")
        self.status_list.addItem("Backend optimization is processing")
        self.status_list.addItem("")
        self.status_list.addItem("Vehicle assignments will appear here")
        self.status_list.addItem("once optimization completes")
    
    def show_error_message(self, error):
        """Show error message"""
        self.status_list.clear()
        self.status_list.addItem("❌ Error loading vehicle data")
        self.status_list.addItem("")
        self.status_list.addItem(f"Error: {error}")
    
    def clear_vehicle_status(self):
        """Clear all vehicle status items"""
        self.status_list.clear()
        if self.current_solution:
            self.display_backend_vehicles(self.current_solution)
    
    def get_vehicle_count(self):
        """Get current number of vehicles being tracked"""
        return self.status_list.count()
    
    def remove_vehicle_status(self, vehicle_id):
        """Remove a specific vehicle from the status list"""
        for i in range(self.status_list.count()):
            item = self.status_list.item(i)
            if vehicle_id in item.text():
                self.status_list.takeItem(i)
                break
    
    def get_backend_folder_path(self):
        """Get path to backend folder"""
        try:
            current_file = os.path.abspath(__file__)
            # from widgets/vehicle_control.py -> frontend/widgets -> frontend -> project_root
            frontend_dir = os.path.dirname(os.path.dirname(current_file))
            project_root = os.path.dirname(frontend_dir)
            return os.path.join(project_root, 'backend')
        except Exception as e:
            print(f"Error getting backend folder path: {e}")
            return None
    
    def closeEvent(self, event):
        """Clean up on close"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)