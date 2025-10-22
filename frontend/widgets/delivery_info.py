"""
Delivery information widget - DISPLAYS ACTUAL BACKEND SOLUTION DATA
Fixed to work with actual backend solution.json structure

FILE LOCATION: frontend/widgets/delivery_info.py
"""
import os
import json
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                           QListWidget, QGridLayout)
from PyQt5.QtCore import Qt, QTimer


class DeliveryInfoWidget(QWidget):
    """Display delivery points information from backend solution"""
    def __init__(self, depot_coords=None, customer_count=5, parent=None):
        super().__init__()
        self.depot_coords = depot_coords
        self.customer_count = customer_count
        self.parent_window = parent
        self._widget_destroyed = False
        self.current_solution = None
        self.last_solution_hash = None
        self.init_ui()
        
        self.backend_complete = False  # Flag to track if backend processing is done
        self.solution_fetched = False  # Track if we've already fetched solution

        # No initial load - wait for main window to trigger loading after backend completion
        
    def init_ui(self):
        """Initialize UI matching original design"""
        try:
            layout = QVBoxLayout(self)
            layout.setSpacing(10)
            layout.setContentsMargins(5, 5, 5, 5)
            
            # Delivery Information group
            info_group = QGroupBox("Delivery Information")
            info_group.setStyleSheet("""
                QGroupBox {
                    font-size: 16px;
                    font-weight: bold;
                    color: #ffffff;
                    background-color: #2a2a2a;
                    padding: 15px;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    margin-top: 10px;
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
            
            info_layout = QVBoxLayout(info_group)
            
            # Customer list
            self.delivery_list = QListWidget()
            self.delivery_list.setWordWrap(True)
            self.delivery_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.delivery_list.setStyleSheet("""
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
            info_layout.addWidget(self.delivery_list)
            
            # Summary section
            summary_group = QGroupBox("Summary")
            summary_group.setStyleSheet("""
                QGroupBox {
                    font-size: 16px;
                    font-weight: bold;
                    color: #ffffff;
                    background-color: #2a2a2a;
                    padding: 15px;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    margin-top: 10px;
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
            summary_layout = QGridLayout(summary_group)
            summary_layout.setSpacing(10)
            
            # Labels with better font sizes
            label_style = "color: #cccccc; font-size: 13px; font-weight: normal; padding: 5px;"
            value_style = "color: #ffffff; font-size: 13px; font-weight: bold; padding: 5px;"
            
            total_points_label = QLabel("Total Points:")
            total_points_label.setStyleSheet(label_style)
            self.total_points = QLabel("0")
            self.total_points.setStyleSheet(value_style)
            
            total_weight_label = QLabel("Total Weight:")
            total_weight_label.setStyleSheet(label_style)
            self.total_weight = QLabel("0.0 kg")
            self.total_weight.setStyleSheet(value_style)
            
            total_distance_label = QLabel("Total Distance:")
            total_distance_label.setStyleSheet(label_style)
            self.total_distance = QLabel("0.0 km")
            self.total_distance.setStyleSheet(value_style)
            
            total_cost_label = QLabel("Total Cost:")
            total_cost_label.setStyleSheet(label_style)
            self.total_cost = QLabel("$0.00")
            self.total_cost.setStyleSheet(value_style)
            
            summary_layout.addWidget(total_points_label, 0, 0)
            summary_layout.addWidget(self.total_points, 0, 1)
            summary_layout.addWidget(total_weight_label, 1, 0)
            summary_layout.addWidget(self.total_weight, 1, 1)
            summary_layout.addWidget(total_distance_label, 2, 0)
            summary_layout.addWidget(self.total_distance, 2, 1)
            summary_layout.addWidget(total_cost_label, 3, 0)
            summary_layout.addWidget(self.total_cost, 3, 1)
            
            layout.addWidget(info_group, 3)
            layout.addWidget(summary_group, 1)
            
        except Exception as e:
            print(f"Error initializing DeliveryInfoWidget UI: {e}")
            import traceback
            traceback.print_exc()
            self._widget_destroyed = True
    
    def _is_valid_widget(self, widget):
        """Check if widget is valid and not destroyed"""
        try:
            if widget is None:
                return False
            _ = widget.isVisible()
            return True
        except (RuntimeError, AttributeError):
            return False
    
    def _safe_set_text(self, widget, text):
        """Safely set text on a widget with error handling"""
        try:
            if self._widget_destroyed or not self._is_valid_widget(widget):
                return False
            widget.setText(str(text))
            return True
        except (RuntimeError, AttributeError) as e:
            print(f"Error setting widget text: {e}")
            return False
    
    def periodic_load_solution(self):
        """Adaptive polling for solution updates from API"""
        if self._widget_destroyed:
            return

        try:
            solution = self._get_solution()
            if solution:
                solution_str = json.dumps(solution, sort_keys=True)
                solution_hash = hash(solution_str)

                if solution_hash != self.last_solution_hash:
                    # Solution changed - reset polling to faster interval
                    self.last_solution_hash = solution_hash
                    self.current_solution = solution
                    self.display_solution_data(solution)
                    self.consecutive_unchanged = 0
                    self._adjust_poll_interval(faster=True)
                    print(f"[DeliveryInfoWidget] Solution updated - hash: {solution_hash}, polling every {self.poll_interval//1000}s")
                else:
                    # Solution unchanged - gradually slow down polling
                    self.consecutive_unchanged += 1
                    self._adjust_poll_interval(faster=False)
            else:
                # No solution available - keep current polling
                pass
        except Exception as e:
            # On error, don't change polling interval
            pass

    def _adjust_poll_interval(self, faster=False):
        """Adjust polling interval based on solution change frequency"""
        if faster:
            # Speed up when solution changes
            self.poll_interval = max(2000, self.poll_interval // 2)  # Minimum 2 seconds
        else:
            # Slow down when solution unchanged
            if self.consecutive_unchanged > 5:
                self.poll_interval = min(self.max_poll_interval, self.poll_interval * 1.5)
            elif self.consecutive_unchanged > 10:
                self.poll_interval = min(self.max_poll_interval, self.poll_interval * 2)

        # Apply new interval
        if self.poll_interval != self.refresh_timer.interval():
            self.refresh_timer.setInterval(int(self.poll_interval))
    
    def load_backend_solution(self):
        """Load and display actual backend solution data"""
        try:
            if self._widget_destroyed:
                return
            
            solution = self._get_solution()
            
            if solution:
                self.current_solution = solution
                self.display_solution_data(solution)
            else:
                self.show_waiting_message()
            
        except Exception as e:
            print(f"[DeliveryInfoWidget] Error: {e}")
            self.show_waiting_message()
    
    def _get_solution(self):
        """Get solution from parent or API - only after backend completion"""
        # Try parent first
        if self.parent_window and hasattr(self.parent_window, 'solution'):
            if self.parent_window.solution:
                return self.parent_window.solution

        # Try API
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
                        print("[DeliveryInfoWidget] Backend processing complete - fetching solution once")
                        self.backend_complete = True
                        return solution
                # Backend not ready yet
                return None

            # Backend complete - use cached solution if already fetched
            if self.solution_fetched and self.current_solution:
                return self.current_solution

            # First time fetching after backend completion
            response = requests.get(
                "https://trispark.onrender.com/api/solution",
                timeout=15
            )

            if response.status_code == 200:
                solution = response.json()
                if solution:
                    self.solution_fetched = True
                    return solution
            elif response.status_code == 404:
                # Solution disappeared - reset backend complete flag
                self.backend_complete = False
                self.solution_fetched = False
                if self.refresh_timer:
                    self.refresh_timer.stop()
                    self.refresh_timer = None
                return None
            else:
                print(f"[DeliveryInfoWidget] Failed to fetch solution: HTTP {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("[DeliveryInfoWidget] Timeout fetching solution from API")
            return None
        except requests.exceptions.ConnectionError:
            print("[DeliveryInfoWidget] Connection error - cannot reach backend API")
            return None
        except Exception as e:
            print(f"[DeliveryInfoWidget] Error fetching solution: {e}")

        return None

    def _start_adaptive_polling(self):
        """Start adaptive polling once backend processing is complete"""
        if self.refresh_timer is None:
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self.periodic_load_solution)
            self.refresh_timer.start(self.poll_interval)
            print(f"[DeliveryInfoWidget] Started adaptive polling every {self.poll_interval//1000}s")
    
    def display_solution_data(self, solution):
        """Display backend solution data - WORKS WITH ACTUAL STRUCTURE"""
        try:
            if not self._is_valid_widget(self.delivery_list):
                return
            
            self.delivery_list.clear()
            
            print(f"[DeliveryInfoWidget] Solution keys: {solution.keys()}")
            
            # ADAPTIVE: Try different ways to get wave data
            waves = None
            
            # Try 1: waves array
            if 'waves' in solution and isinstance(solution['waves'], list):
                waves = solution['waves']
                print(f"[DeliveryInfoWidget] Found waves array with {len(waves)} waves")
            
            # Try 2: Check if top-level has wave_X keys
            elif any(key.startswith('wave_') for key in solution.keys()):
                print(f"[DeliveryInfoWidget] Found wave_X structure in solution")
                wave_keys = sorted([k for k in solution.keys() if k.startswith('wave_')])
                waves = [solution[k] for k in wave_keys]
                print(f"[DeliveryInfoWidget] Extracted {len(waves)} waves")
            
            if not waves:
                print(f"[DeliveryInfoWidget] No waves found. Solution structure: {json.dumps(solution, indent=2)[:500]}")
                self.show_waiting_message()
                return
            
            current_wave = waves[0]
            print(f"[DeliveryInfoWidget] Processing first wave. Keys: {current_wave.keys()}")
            
            # Collect all deliveries
            all_deliveries = []
            total_weight = 0.0
            total_distance = 0.0
            total_cost = 0.0
            
            # Process drones
            drones = current_wave.get('drones', [])
            print(f"[DeliveryInfoWidget] Found {len(drones)} drones")
            
            for drone_idx, drone in enumerate(drones):
                node_ids = drone.get('node_ids', [])
                distance = float(drone.get('distance', 0))
                weight = float(drone.get('total_weight', 0))
                cost = float(drone.get('cost', 0))
                
                num_nodes = len(node_ids)
                if num_nodes > 0:
                    for node_idx, node_id in enumerate(node_ids):
                        all_deliveries.append({
                            'vehicle': f"Drone {drone_idx + 1}",
                            'node_id': node_id,
                            'index': node_idx + 1,
                            'total': num_nodes
                        })
                
                total_weight += weight
                total_distance += distance
                total_cost += cost
                print(f"[DeliveryInfoWidget] Drone {drone_idx}: {num_nodes} nodes, {distance:.2f}km, {weight:.2f}kg, ${cost:.2f}")
            
            # Process trucks
            trucks = current_wave.get('trucks', [])
            print(f"[DeliveryInfoWidget] Found {len(trucks)} trucks")
            
            truck_counter = 1
            for truck in trucks:
                node_ids = truck.get('node_ids', [])
                distance = float(truck.get('distance', 0))
                weight = float(truck.get('total_weight', 0))
                cost = float(truck.get('cost', 0))
                vehicle_id = truck.get('vehicle_id', f'Truck {truck_counter}')
                
                num_nodes = len(node_ids)
                if num_nodes > 0:
                    for node_idx, node_id in enumerate(node_ids):
                        all_deliveries.append({
                            'vehicle': vehicle_id,
                            'node_id': node_id,
                            'index': node_idx + 1,
                            'total': num_nodes
                        })
                
                total_weight += weight
                total_distance += distance
                total_cost += cost
                print(f"[DeliveryInfoWidget] {vehicle_id}: {num_nodes} nodes, {distance:.2f}km, {weight:.2f}kg, ${cost:.2f}")
                truck_counter += 1
            
            # Display deliveries
            if all_deliveries:
                for idx, delivery in enumerate(all_deliveries, 1):
                    item_text = (
                        f"{idx}. {delivery['vehicle']}\n"
                        f"   Node ID: {delivery['node_id']}\n"
                        f"   Stop {delivery['index']} of {delivery['total']}"
                    )
                    self.delivery_list.addItem(item_text)
                print(f"[DeliveryInfoWidget] Displayed {len(all_deliveries)} deliveries")
            else:
                self.delivery_list.addItem("No delivery nodes found")
            
            # Update summary
            total_delivery_points = len(all_deliveries)
            
            self._safe_set_text(self.total_points, str(total_delivery_points))
            self._safe_set_text(self.total_weight, f"{total_weight:.2f} kg")
            self._safe_set_text(self.total_distance, f"{total_distance:.2f} km")
            self._safe_set_text(self.total_cost, f"${total_cost:.2f}")
            
            print(f"[DeliveryInfoWidget]  Display complete! Total: {total_delivery_points} points, {total_weight:.2f}kg, {total_distance:.2f}km, ${total_cost:.2f}")
            
        except Exception as e:
            print(f"[DeliveryInfoWidget] Error displaying data: {e}")
            import traceback
            traceback.print_exc()
    
    def show_waiting_message(self):
        """Show waiting message when no solution available"""
        if not self._is_valid_widget(self.delivery_list):
            return
        
        self.delivery_list.clear()
        self.delivery_list.addItem("Waiting for backend solution...")
        self.delivery_list.addItem("")
        self.delivery_list.addItem("Backend optimization is processing")
        
        # Reset summary
        self._safe_set_text(self.total_points, "0")
        self._safe_set_text(self.total_weight, "0.0 kg")
        self._safe_set_text(self.total_distance, "0.0 km")
        self._safe_set_text(self.total_cost, "$0.00")
    
    def update_depot(self, depot_coords, customer_count=None):
        """Update depot coordinates and customer count"""
        try:
            if self._widget_destroyed:
                return
                
            self.depot_coords = depot_coords
            if customer_count is not None:
                self.customer_count = customer_count
            
            # Force reload
            self.load_backend_solution()
                
        except Exception as e:
            print(f"Error updating depot: {e}")
    
    def get_backend_folder_path(self):
        """Get path to backend folder"""
        try:
            current_file = os.path.abspath(__file__)
            frontend_widgets_dir = os.path.dirname(current_file)
            frontend_dir = os.path.dirname(frontend_widgets_dir)
            project_root = os.path.dirname(frontend_dir)
            return os.path.join(project_root, 'backend')
        except Exception as e:
            return None
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self._widget_destroyed = True
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)
    
    def deleteLater(self):
        """Override deleteLater to mark widget as destroyed"""
        self._widget_destroyed = True
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().deleteLater()