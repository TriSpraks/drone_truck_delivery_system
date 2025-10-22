"""
Vehicle control panel widget - DISPLAYS ACTUAL BACKEND SOLUTION DATA
Shows real vehicle assignments and live tracking from solution.json

FILE LOCATION: frontend/widgets/vehicle_control.py
"""
import os
import json
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                           QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer


class VehicleControlPanel(QWidget):
    """Control panel for vehicle tracking with backend data"""
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.current_solution = None
        self.vehicle_data_cache = {}
        self.init_ui()
        
        self.backend_complete = False  # Flag to track if backend processing is done
        self.solution_fetched = False  # Track if we've already fetched solution

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
        
        # No initial load - wait for main window to trigger loading after backend completion
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh timer - only works after backend completion"""
        if not self.backend_complete:
            print("[VehicleControlPanel] Cannot toggle auto-refresh - backend processing not complete")
            return

        if self.auto_refresh_btn.isChecked():
            if self.refresh_timer:
                self.refresh_timer.start(self.poll_interval)
            self.auto_refresh_btn.setText("⏸ Auto-Refresh")
        else:
            if self.refresh_timer:
                self.refresh_timer.stop()
            self.auto_refresh_btn.setText("▶ Auto-Refresh")

    def _start_adaptive_polling(self):
        """Start adaptive polling once backend processing is complete"""
        if self.refresh_timer is None:
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self.refresh_vehicle_data)
            self.refresh_timer.start(self.poll_interval)
            print(f"[VehicleControlPanel] Started adaptive polling every {self.poll_interval//1000}s")
    
    def load_backend_solution(self):
        """Load backend solution data"""
        try:
            # Try parent first
            solution = None
            if self.parent_window and hasattr(self.parent_window, 'solution'):
                solution = self.parent_window.solution

            # If no solution in parent, try API - only after backend completion
            if not solution:
                try:
                    import requests

                    # Don't poll if backend processing not complete
                    if not self.backend_complete:
                        # Check if backend has completed by looking for solution
                        response = requests.get(
                            "https://trispark.onrender.com/api/solution",
                            timeout=15
                        )

                        if response.status_code == 200:
                            solution = response.json()
                            if solution:
                                print("[VehicleControlPanel] Backend processing complete - fetching solution once")
                                self.backend_complete = True
                        # Backend not ready yet
                        return

                    # Backend complete - use cached solution if already fetched
                    if self.solution_fetched and self.current_solution:
                        solution = self.current_solution
                    else:
                        # First time fetching after backend completion
                        response = requests.get(
                            "https://trispark.onrender.com/api/solution",
                            timeout=15
                        )

                        if response.status_code == 200:
                            solution = response.json()
                            if solution:
                                self.solution_fetched = True
                        elif response.status_code == 404:
                            # Solution disappeared - reset backend complete flag
                            self.backend_complete = False
                            self.solution_fetched = False
                            if self.refresh_timer:
                                self.refresh_timer.stop()
                                self.refresh_timer = None
                        else:
                            print(f"Failed to fetch solution: HTTP {response.status_code}")

                except requests.exceptions.Timeout:
                    print("Timeout fetching solution from API")
                except requests.exceptions.ConnectionError:
                    print("Connection error - cannot reach backend API")
                except Exception as e:
                    print(f"Error fetching solution: {e}")

            if solution:
                self.current_solution = solution
                self.display_backend_vehicles(solution)
            else:
                self.show_no_solution_message()

        except Exception as e:
            print(f"Error loading backend solution: {e}")
            self.show_error_message(str(e))
    
    def refresh_vehicle_data(self):
        """Adaptive refresh of vehicle data based on current state"""
        try:
            changed = False

            if self.parent_window and hasattr(self.parent_window, 'vehicle_manager'):
                vm = self.parent_window.vehicle_manager
                if vm.vehicles_started and vm.vehicles:
                    # Update with live data - always refresh when vehicles are active
                    self.update_live_vehicle_status(vm.vehicles)
                    changed = True
                elif self.current_solution:
                    # Show backend assignments - check if solution changed
                    solution_str = json.dumps(self.current_solution, sort_keys=True)
                    solution_hash = hash(solution_str)

                    if solution_hash != getattr(self, 'last_solution_hash', None):
                        self.last_solution_hash = solution_hash
                        self.display_backend_vehicles(self.current_solution)
                        changed = True

            # Adjust polling based on whether data changed
            if changed:
                self.consecutive_unchanged = 0
                self._adjust_poll_interval(faster=True)
            else:
                self.consecutive_unchanged += 1
                self._adjust_poll_interval(faster=False)

        except Exception as e:
            print(f"[VehicleControlPanel] Error refreshing vehicle data: {e}")

    def _adjust_poll_interval(self, faster=False):
        """Adjust polling interval based on data change frequency"""
        if faster:
            # Speed up when data changes
            self.poll_interval = max(3000, self.poll_interval // 2)  # Minimum 3 seconds for vehicle control
        else:
            # Slow down when data unchanged
            if self.consecutive_unchanged > 3:
                self.poll_interval = min(self.max_poll_interval, self.poll_interval * 1.5)
            elif self.consecutive_unchanged > 8:
                self.poll_interval = min(self.max_poll_interval, self.poll_interval * 2)

        # Apply new interval
        if self.poll_interval != self.refresh_timer.interval():
            self.refresh_timer.setInterval(int(self.poll_interval))
            print(f"[VehicleControlPanel] Adjusted polling to {self.poll_interval//1000}s")
    
    def display_backend_vehicles(self, solution):
        """Display vehicle assignments from backend solution"""
        try:
            self.status_list.clear()
            
            waves = solution.get('waves', [])
            if not waves:
                self.status_list.addItem("⚠️ No waves in solution")
                return
            
            current_wave = waves[0]
            wave_num = current_wave.get('wave_number', 1)
            
            # Header
            header_item = QListWidgetItem(f"═══ WAVE {wave_num} ASSIGNMENTS ═══")
            header_item.setForeground(Qt.yellow)
            self.status_list.addItem(header_item)
            
            # Display drones
            drones = current_wave.get('drones', [])
            for i, drone in enumerate(drones, 1):
                self.add_vehicle_item(drone, "Drone", "🚁")
            
            # Display trucks
            trucks = current_wave.get('trucks', [])
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
        status_text += f"Cost: ${cost:.2f}\n"
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
                item_text += f"Cost: ${backend_cost:.2f}\n"
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