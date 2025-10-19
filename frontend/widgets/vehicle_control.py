"""
Vehicle control panel widget - DISPLAYS ACTUAL BACKEND SOLUTION DATA
Shows real vehicle assignments and live tracking from solution.json

FILE LOCATION: frontend/widgets/vehicle_control.py
"""
import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                           QListWidget, QListWidgetItem, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer


class VehicleControlPanel(QWidget):
    """Control panel for vehicle tracking with backend data"""
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.current_solution = None
        self.vehicle_data_cache = {}
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_vehicle_data)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
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
                background-color: #333333;
                padding: 15px;
                border-radius: 8px;
                margin-top: 10px;
                border: 2px solid #404040;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ff6b35;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        status_layout = QVBoxLayout(status_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a78bfa;
            }
        """)
        refresh_btn.clicked.connect(self.load_backend_solution)
        
        self.auto_refresh_btn = QPushButton("⏸ Auto-Refresh")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setChecked(True)
        self.auto_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34d399;
            }
            QPushButton:checked {
                background-color: #ef4444;
            }
        """)
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(self.auto_refresh_btn)
        status_layout.addLayout(button_layout)
        
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
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh timer"""
        if self.auto_refresh_btn.isChecked():
            self.refresh_timer.start(5000)
            self.auto_refresh_btn.setText("⏸ Auto-Refresh")
        else:
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText("▶ Auto-Refresh")
    
    def load_backend_solution(self):
        """Load backend solution data"""
        try:
            # Try parent first
            solution = None
            if self.parent_window and hasattr(self.parent_window, 'solution'):
                solution = self.parent_window.solution
            
            # If no solution in parent, try file
            if not solution:
                backend_folder = self.get_backend_folder_path()
                if backend_folder:
                    solution_file = os.path.join(backend_folder, 'solution.json')
                    if os.path.exists(solution_file):
                        with open(solution_file, 'r') as f:
                            solution = json.load(f)
            
            if solution:
                self.current_solution = solution
                self.display_backend_vehicles(solution)
            else:
                self.show_no_solution_message()
                
        except Exception as e:
            print(f"Error loading backend solution: {e}")
            self.show_error_message(str(e))
    
    def refresh_vehicle_data(self):
        """Refresh vehicle data if vehicles are running"""
        if self.parent_window and hasattr(self.parent_window, 'vehicle_manager'):
            vm = self.parent_window.vehicle_manager
            if vm.vehicles_started and vm.vehicles:
                # Update with live data
                self.update_live_vehicle_status(vm.vehicles)
            elif self.current_solution:
                # Show backend assignments
                self.display_backend_vehicles(self.current_solution)
    
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