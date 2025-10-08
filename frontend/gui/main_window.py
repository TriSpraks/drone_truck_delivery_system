"""
REFACTORED Main application window for India Airspace Management System
Ultra-simplified by extracting functionality into separate modules
Reduced from ~800 lines to ~200 lines
"""
import sys
import os
import math
import asyncio
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QMutex

# Import configuration
from config.app_config import DARK_STYLE
from utils.backend_connector import DEFAULT_DEPOT_COORDS, MAP_CENTER, MAP_ZOOM
from resources.map_templates import HTML_TEMPLATE
from utils.nfz_data import get_india_no_fly_zones

# Import new modular components
from ui.ui_builder import UIBuilder
from ui.dialog import DepotSelectionWindow
from gui.vehicle_manager import VehicleManager
from gui.backend_handler import BackendHandler
from gui.map_handler import MapHandler
from gui.wave_controller import WaveController
from gui.vehicle_controller import VehicleController
from core.data_manager import DataSimulator
from core.delivery_generator import DeliveryPointGenerator


class BackendProcessorThread(QThread):
    """Background thread for backend processing"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    timeout_signal = pyqtSignal()

    def __init__(self, parent, timeout_seconds=30):
        super().__init__()
        self.parent = parent
        self.timeout_seconds = timeout_seconds

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(
                    asyncio.wait_for(
                        self.process_backend(),
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

    async def process_backend(self):
        """Process backend computations"""
        try:
            vehicle_config = {
                "electric_trucks": self.parent.electric_trucks,
                "fuel_trucks": self.parent.fuel_trucks,
                "drones": self.parent.drones
            }
            
            success = await BackendHandler.process_all_computations(
                self.parent.customer_nodes,
                self.parent.depot_node,
                vehicle_config
            )
            
            if success:
                print("✅ Backend processing completed")
                await asyncio.sleep(3)
                
                backend_folder = self.parent.get_backend_folder_path()
                initial_solution = BackendHandler.load_initial_solution(backend_folder)
                
                if initial_solution:
                    self.parent.initial_solution = initial_solution
                    self.parent.waves_data = BackendHandler.parse_wave_information(initial_solution)
                    print(f"✅ Loaded {len(self.parent.waves_data)} waves")
                    
        except Exception as e:
            print(f"❌ Error in backend processing: {e}")
            import traceback
            traceback.print_exc()


class IndiaAirspaceMap(QMainWindow):
    """Main application window - ultra-simplified and modular"""
    
    def __init__(self, depot_coords=None, customer_count=5, 
                 electric_trucks=2, fuel_trucks=1, drones=3):
        super().__init__()
        self.setWindowTitle("India Airspace Management - Optimized Fleet System")
        self.setGeometry(50, 50, 1800, 1000)
        self.setMinimumSize(1600, 900)
        
        # State flags
        self._widgets_destroyed = False
        self._shutdown_in_progress = False
        self._progress_mutex = QMutex()
        
        # Apply theme
        self.setStyleSheet(DARK_STYLE)
        
        # Configuration
        self.depot_coords = depot_coords or DEFAULT_DEPOT_COORDS
        self.customer_count = customer_count
        self.electric_trucks = electric_trucks
        self.fuel_trucks = fuel_trucks
        self.drones = drones
        
        # Map configuration
        self.map_center = MAP_CENTER
        self.map_zoom = MAP_ZOOM
        self.no_fly_zones = get_india_no_fly_zones()
        
        # Data structures
        self.waves_data = []
        self.initial_solution = None
        
        # Initialize controllers
        self.vehicle_manager = VehicleManager(self.depot_coords)
        self.wave_controller = WaveController(self)
        self.vehicle_controller = VehicleController(self)
        
        # Generate delivery points
        results = DeliveryPointGenerator.generate_points(
            self.depot_coords, 
            self.customer_count
        )
        self.delivery_points, self.customer_nodes, self.depot_node = results
        
        # Setup UI
        self.setup_ui()
        self.setup_data_simulator()
        
        # Create map handler after map view is created
        self.map_handler = MapHandler(self.map_view, HTML_TEMPLATE)
        self.map_handler.create_map_file()
        
        # Setup timers
        self.setup_timers()
        
        # Show maximized
        self.showMaximized()
        
        # Start backend processing
        QTimer.singleShot(1000, self.start_backend_processing)
    
    def setup_timers(self):
        """Setup update timers"""
        # Movement timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.vehicle_controller.tick_movement)
        self.timer.start(1000)  # 1 second
        
        # Map update timer
        self.map_update_timer = QTimer()
        self.map_update_timer.timeout.connect(self.update_map_display)
        self.map_update_timer.start(2000)  # 2 seconds
    
    def setup_ui(self):
        """Setup user interface"""
        try:
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QHBoxLayout(central_widget)
            main_layout.setSpacing(10)
            main_layout.setContentsMargins(10, 10, 10, 10)
            
            # Create panels using UIBuilder
            left_panel = UIBuilder.create_left_panel(self)
            middle_widget = self.create_middle_panel()
            right_panel = UIBuilder.create_right_panel(self)
            
            # Add to layout
            main_layout.addWidget(left_panel)
            main_layout.addWidget(middle_widget, 1)
            main_layout.addWidget(right_panel)
            
            # Status bar
            self.update_status_bar()
            self.statusBar().setStyleSheet(
                "background-color: #2d2d2d; color: #ffffff; padding: 5px;"
            )
            
        except Exception as e:
            print(f"Error setting up UI: {e}")
            self._widgets_destroyed = True
    
    def create_middle_panel(self):
        """Create middle panel with map"""
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        
        # Toolbar
        toolbar = UIBuilder.create_toolbar(self)
        
        # Map view
        self.map_view = QWebEngineView()
        self.map_view.loadFinished.connect(self.on_map_ready)
        
        middle_layout.addWidget(toolbar)
        middle_layout.addWidget(self.map_view)
        
        return middle_widget
    
    def get_backend_folder_path(self):
        """Get path to backend folder"""
        current_file = os.path.abspath(__file__)
        frontend_gui_dir = os.path.dirname(current_file)
        frontend_dir = os.path.dirname(frontend_gui_dir)
        project_root = os.path.dirname(frontend_dir)
        return os.path.join(project_root, 'backend')
    
    def start_backend_processing(self):
        """Start backend processing in background thread"""
        self.backend_processor = BackendProcessorThread(self)
        self.backend_processor.finished.connect(
            lambda: print("✅ Backend processing complete")
        )
        self.backend_processor.error.connect(
            lambda err: print(f"❌ Backend error: {err}")
        )
        self.backend_processor.timeout_signal.connect(
            lambda: QMessageBox.warning(
                self, 
                "Backend Timeout",
                "Backend processing timed out. Using default routing."
            )
        )
        self.backend_processor.start()
    
    def on_map_ready(self, success):
        """Handle map ready event"""
        if not success:
            QMessageBox.critical(self, "Map Error", "Failed to load map")
            return
        
        self.map_handler.map_ready = True
        self.map_handler.initialize_map(
            self.depot_coords,
            self.delivery_points,
            self.no_fly_zones,
            self.map_center,
            self.map_zoom
        )
    
    # Vehicle control methods - delegated to VehicleController
    def toggle_start_stop_vehicles(self):
        """Toggle vehicle start/stop"""
        self.vehicle_controller.toggle_start_stop()
    
    def start_vehicles_optimized(self):
        """Start vehicle simulation"""
        return self.vehicle_controller.start_vehicles_optimized()
    
    def restart_vehicles(self):
        """Restart vehicles"""
        self.vehicle_controller.restart_vehicles()
    
    # Wave control methods - delegated to WaveController
    def start_next_wave(self):
        """Start next wave"""
        self.wave_controller.start_next_wave()
    
    # Map control methods
    def update_map_display(self):
        """Batch update map display"""
        if self.map_handler.pending_map_update and not self.vehicle_manager.vehicles_paused:
            self.map_handler.update_vehicle_positions(
                self.vehicle_manager.vehicles,
                self.vehicle_manager.vehicles_paused
            )
            self.map_handler.pending_map_update = False
    
    def toggle_no_fly_zones(self):
        """Toggle no-fly zones visibility"""
        self.map_handler.toggle_no_fly_zones(self.toggle_nfz_action.isChecked())
    
    def toggle_vehicles(self):
        """Toggle vehicles visibility"""
        show = self.toggle_vehicles_action.isChecked()
        self.map_handler.toggle_vehicles(show)
        
        if show and self.vehicle_manager.vehicles:
            QTimer.singleShot(500, lambda: self.map_handler.send_vehicles_to_map_batch(
                self.vehicle_manager.vehicles
            ))
    
    # Depot configuration
    def change_depot_location(self):
        """Open depot selection dialog"""
        if self.vehicle_manager.vehicles_started and self.vehicle_manager.vehicles:
            reply = QMessageBox.question(
                self,
                "Change Configuration",
                "Changing depot will stop vehicles. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        depot_dialog = DepotSelectionWindow()
        depot_dialog.depot_selected.connect(self.on_new_depot_selected)
        depot_dialog.exec()
    
    def on_new_depot_selected(self, lat, lng, customer_count, 
                             electric_trucks, fuel_trucks, drones):
        """Handle new depot selection"""
        if self._widgets_destroyed:
            return
        
        # Update configuration
        self.depot_coords = [lat, lng]
        self.customer_count = customer_count
        self.electric_trucks = electric_trucks
        self.fuel_trucks = fuel_trucks
        self.drones = drones
        
        # Stop vehicles
        if self.vehicle_manager.vehicles_started:
            self.vehicle_controller.stop_vehicles_complete()
        
        # Regenerate delivery points
        results = DeliveryPointGenerator.generate_points(
            self.depot_coords,
            self.customer_count
        )
        self.delivery_points, self.customer_nodes, self.depot_node = results
        self.vehicle_manager.depot_coords = self.depot_coords
        
        # Update UI
        if hasattr(self.delivery_info, 'update_depot'):
            self.delivery_info.update_depot(self.depot_coords, self.customer_count)
        
        self.update_depot_and_fleet_ui()
        
        # Update map
        if self.map_handler.map_ready:
            self.map_handler.update_map_configuration(
                self.depot_coords,
                self.delivery_points
            )
        
        # Start backend processing
        self.start_backend_processing()
        
        # Show confirmation
        total_vehicles = electric_trucks + fuel_trucks + drones
        QMessageBox.information(
            self,
            "Configuration Updated",
            f"Depot: {lat:.6f}, {lng:.6f}\n"
            f"Customers: {customer_count}\n"
            f"Fleet: {total_vehicles} vehicles\n"
            f"({electric_trucks}E + {fuel_trucks}F + {drones}D)"
        )
    
    def update_status_bar(self):
        """Update status bar with current info"""
        try:
            if self._widgets_destroyed:
                return
            
            total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
            avg_deliveries = math.ceil(len(self.delivery_points) / max(1, total_vehicles))
            
            status = (
                f"Depot: {self.depot_coords[0]:.4f}, {self.depot_coords[1]:.4f} | "
                f"Fleet: {total_vehicles} vehicles | "
                f"Coverage: {len(self.delivery_points)} points (~{avg_deliveries} per vehicle)"
            )
            
            self.statusBar().showMessage(status)
        except Exception as e:
            print(f"Error updating status bar: {e}")
    
    def update_depot_and_fleet_ui(self):
        """Update UI labels with new configuration"""
        try:
            if self._widgets_destroyed:
                return
            
            self.depot_info_label.setText(
                f"Depot: {self.depot_coords[0]:.4f}, {self.depot_coords[1]:.4f}"
            )
            self.customer_info_label.setText(f"Customers: {self.customer_count}")
            self.fleet_info_label.setText(
                f"Fleet: {self.electric_trucks}E + {self.fuel_trucks}F + {self.drones}D"
            )
            
            total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
            self.fleet_summary_label.setText(f"Total Vehicles: {total_vehicles}")
            
            self.update_status_bar()
        except Exception as e:
            print(f"Error updating UI: {e}")
    
    def setup_data_simulator(self):
        """Setup data simulator for sound monitoring"""
        try:
            self.data_simulator = DataSimulator()
            self.data_simulator.sound_data_updated.connect(self.on_sound_data_updated)
            self.data_simulator.start()
        except Exception as e:
            print(f"Error setting up data simulator: {e}")
            self.data_simulator = None
    
    def on_sound_data_updated(self, level, waveform):
        """Handle sound data updates"""
        if self._widgets_destroyed:
            return
        
        try:
            if hasattr(self.sound_graphs, 'update_sound_data'):
                self.sound_graphs.update_sound_data(level, waveform)
            if hasattr(self.noise_stats, 'update_statistics'):
                self.noise_stats.update_statistics(level)
        except Exception as e:
            print(f"Error updating sound data: {e}")
    
    def closeEvent(self, event):
        """Clean up on close"""
        print("Shutting down system...")
        self._shutdown_in_progress = True
        
        # Stop timers
        try:
            if hasattr(self, 'timer'):
                self.timer.stop()
            if hasattr(self, 'map_update_timer'):
                self.map_update_timer.stop()
        except Exception as e:
            print(f"Error stopping timers: {e}")
        
        # Stop controllers
        try:
            self.wave_controller.stop()
            self.vehicle_controller.cleanup()
        except Exception as e:
            print(f"Error stopping controllers: {e}")
        
        # Stop threads
        try:
            if hasattr(self, 'data_simulator') and self.data_simulator:
                self.data_simulator.stop()
                self.data_simulator.wait(2000)
        except Exception as e:
            print(f"Error stopping data simulator: {e}")
        
        # Mark destroyed
        self._widgets_destroyed = True
        
        # Clean up map
        try:
            if self.map_handler:
                self.map_handler.cleanup()
        except Exception as e:
            print(f"Error cleaning up map: {e}")
        
        # Clear route cache
        try:
            from core.api_handler import OptimizedRouteManager
            OptimizedRouteManager.clear_cache()
        except Exception as e:
            print(f"Error clearing cache: {e}")
        
        print("Shutdown complete.")
        event.accept()