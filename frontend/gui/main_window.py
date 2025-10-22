"""
Main application window - BLOCKS until backend solution is ready
Shows progress dialog while backend processes, prevents premature interaction
"""
import sys
import os
import math
import asyncio
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QMessageBox, QProgressDialog, QApplication)
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
from core.delivery_generator import DeliveryPointGenerator


class BackendProcessorThread(QThread):
    """Background thread for backend processing with detailed progress"""
    finished = pyqtSignal(bool, object)  # success, solution_data
    progress_update = pyqtSignal(str)  # status message
    elapsed_time_update = pyqtSignal(int)  # elapsed seconds
    error = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.start_time = None

    def run(self):
        try:
            import time
            self.start_time = time.time()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Start timer thread
            timer = QTimer()
            timer.timeout.connect(self.update_elapsed_time)
            timer.start(1000)  # Update every second
            
            self.progress_update.emit("Connecting to backend server...")
            
            # Process backend computations
            success = loop.run_until_complete(self.process_backend())
            
            timer.stop()
            
            if success:
                self.progress_update.emit("Loading optimized solution...")
                
                # Wait for file to be written
                time.sleep(5)
                
                # Load solution
                backend_folder = self.parent.get_backend_folder_path()
                solution = BackendHandler.load_solution(backend_folder)
                
                if solution:
                    elapsed = int(time.time() - self.start_time)
                    self.progress_update.emit(f"Backend optimization complete! (took {elapsed}s)")
                    self.finished.emit(True, solution)
                else:
                    self.progress_update.emit("Warning: Solution file not found")
                    self.finished.emit(False, None)
            else:
                self.error.emit("Backend processing failed")
                self.finished.emit(False, None)
            
            loop.close()
            
        except Exception as e:
            print(f"❌ Error in backend thread: {e}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))
            self.finished.emit(False, None)
    
    def update_elapsed_time(self):
        """Update elapsed time in progress dialog"""
        if self.start_time:
            import time
            elapsed = int(time.time() - self.start_time)
            self.elapsed_time_update.emit(elapsed)

    async def process_backend(self):
        """Process backend computations with progress updates"""
        try:
            num_nodes = len(self.parent.customer_nodes)
            self.progress_update.emit(f"Sending {num_nodes} delivery nodes to backend...")
            
            vehicle_config = {
                "electric_trucks": self.parent.electric_trucks,
                "fuel_trucks": self.parent.fuel_trucks,
                "drones": self.parent.drones
            }
            
            # Send nodes to backend
            self.progress_update.emit(f"Computing distance matrix ({num_nodes}x{num_nodes} = {num_nodes*num_nodes} calculations)...")
            success = await BackendHandler.process_all_computations(
                self.parent.customer_nodes,
                self.parent.depot_node,
                vehicle_config
            )
            
            if success:
                self.progress_update.emit("Running optimization algorithm...")
                await asyncio.sleep(2)  # Give backend time to complete
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error in backend processing: {e}")
            return False


class IndiaAirspaceMap(QMainWindow):
    """Main application window - WAITS for backend before allowing interaction"""
    
    def __init__(self, depot_coords=None, customer_count=5, 
                 electric_trucks=2, fuel_trucks=1, drones=3):
        super().__init__()
        self.setWindowTitle("India Airspace Management - Backend Optimized")
        self.setGeometry(50, 50, 1800, 1000)
        self.setMinimumSize(1600, 900)
        
        # State flags
        self._widgets_destroyed = False
        self._shutdown_in_progress = False
        self._progress_mutex = QMutex()
        self._backend_ready = False
        
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
        
        # Initialize data structures
        self.waves_data = []
        self.solution = None
        
        # Generate delivery points
        print("\n" + "="*70)
        print("INITIALIZING APPLICATION")
        print("="*70)
        print("Step 1: Generating delivery points...")
        results = DeliveryPointGenerator.generate_points(
            self.depot_coords, 
            self.customer_count
        )
        self.delivery_points, self.customer_nodes, self.depot_node = results
        print(f"✅ Generated {len(self.customer_nodes)} customer nodes\n")
        
        # Initialize controllers
        print("Step 2: Initializing controllers...")
        self.vehicle_manager = VehicleManager(self.depot_coords)
        self.wave_controller = WaveController(self)
        self.vehicle_controller = VehicleController(self)
        print("✅ Controllers initialized\n")
        
        # Setup UI
        print("Step 3: Setting up user interface...")
        self.setup_ui()
        print("✅ UI setup complete\n")
        
        # Create map handler
        print("Step 4: Initializing map...")
        self.map_handler = MapHandler(self.map_view, HTML_TEMPLATE)
        self.map_handler.create_map_file()
        print("✅ Map initialized\n")
        
        # Setup timers
        self.setup_timers()
        
        # Show maximized
        self.showMaximized()
        
        print("="*70)
        print("APPLICATION WINDOW READY")
        print("="*70 + "\n")
        
        # ========== CRITICAL: START BACKEND PROCESSING ==========
        # This BLOCKS user interaction until backend completes
        QTimer.singleShot(500, self.start_backend_processing_with_dialog)
        # ========================================================
    
    def start_backend_processing_with_dialog(self):
        """Start backend processing with BLOCKING progress dialog"""
        # Calculate expected time
        num_nodes = len(self.customer_nodes)
        expected_seconds = BackendHandler.calculate_timeout(num_nodes)
        expected_minutes = expected_seconds / 60
        
        # Create blocking progress dialog
        self.backend_progress = QProgressDialog(
            f"Initializing backend optimization...\n\n"
            f"Processing {num_nodes} delivery nodes\n"
            f"Expected time: {expected_minutes:.1f} minutes\n"
            f"Elapsed: 0s",
            None,  # No cancel button
            0, 0,  # Indeterminate progress
            self
        )
        self.backend_progress.setWindowTitle("Backend Processing")
        self.backend_progress.setWindowModality(Qt.WindowModal)  # BLOCKS interaction
        self.backend_progress.setMinimumDuration(0)
        self.backend_progress.setCancelButton(None)  # Cannot cancel
        self.backend_progress.setAutoClose(False)
        self.backend_progress.setMinimumWidth(400)
        self.backend_progress.show()
        
        print("\n" + "="*70)
        print("STARTING BACKEND OPTIMIZATION")
        print(f"Nodes: {num_nodes}")
        print(f"Expected duration: {expected_minutes:.1f} minutes")
        print("="*70)
        
        # Start backend thread
        self.backend_thread = BackendProcessorThread(self)
        self.backend_thread.progress_update.connect(self.on_backend_progress)
        self.backend_thread.elapsed_time_update.connect(self.on_elapsed_time_update)
        self.backend_thread.finished.connect(self.on_backend_finished)
        self.backend_thread.error.connect(self.on_backend_error)
        self.backend_thread.start()
    
    def on_elapsed_time_update(self, elapsed_seconds):
        """Update dialog with elapsed time"""
        if hasattr(self, 'backend_progress') and self.backend_progress:
            num_nodes = len(self.customer_nodes)
            expected_seconds = BackendHandler.calculate_timeout(num_nodes)
            expected_minutes = expected_seconds / 60
            elapsed_minutes = elapsed_seconds / 60
            
            # Get current status message (preserve it)
            current_text = self.backend_progress.labelText().split('\n\n')[0]
            
            self.backend_progress.setLabelText(
                f"{current_text}\n\n"
                f"Processing {num_nodes} delivery nodes\n"
                f"Expected time: {expected_minutes:.1f} minutes\n"
                f"Elapsed: {elapsed_minutes:.1f} min ({elapsed_seconds}s)"
            )
            QApplication.processEvents()  # Force UI update
    
    def on_backend_progress(self, message):
        """Update progress dialog with backend status"""
        print(f"   {message}")
        if hasattr(self, 'backend_progress') and self.backend_progress:
            self.backend_progress.setLabelText(message)
            QApplication.processEvents()  # Force UI update
    
    def on_backend_finished(self, success, solution_data):
        """Handle backend completion"""
        print("="*70)
        
        if success and solution_data:
            print("✅ BACKEND OPTIMIZATION COMPLETE")
            self.solution = solution_data
            self.waves_data = BackendHandler.parse_wave_information(solution_data)
            self._backend_ready = True
            
            print(f"   Loaded {len(self.waves_data)} waves")
            for i, wave in enumerate(self.waves_data, 1):
                print(f"   Wave {i}: {wave['total_drones']} drones, {wave['total_trucks']} trucks")
            print("\n   🚀 READY TO USE BACKEND OPTIMIZED ROUTES")
            
            # Close progress dialog
            if hasattr(self, 'backend_progress'):
                self.backend_progress.close()
            
            # Show success message
            QMessageBox.information(
                self,
                "Backend Ready",
                f"Backend optimization complete!\n\n"
                f"Waves: {len(self.waves_data)}\n"
                f"Total vehicles: {sum(w['total_drones'] + w['total_trucks'] for w in self.waves_data)}\n\n"
                f"Click 'Start Vehicles' to see optimized routes"
            )
            
        else:
            print("⚠️  BACKEND OPTIMIZATION FAILED OR INCOMPLETE")
            print("   Will use frontend optimization as fallback")
            self._backend_ready = False
            
            # Close progress dialog
            if hasattr(self, 'backend_progress'):
                self.backend_progress.close()
            
            # Show warning
            reply = QMessageBox.warning(
                self,
                "Backend Unavailable",
                "Backend optimization could not complete.\n\n"
                "The system will use frontend route optimization instead.\n\n"
                "Routes may not be as optimal as backend solution.\n\n"
                "Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                self.close()
                return
        
        print("="*70 + "\n")
    
    def on_backend_error(self, error_message):
        """Handle backend error"""
        print(f"❌ BACKEND ERROR: {error_message}")
        
        if hasattr(self, 'backend_progress'):
            self.backend_progress.close()
        
        QMessageBox.critical(
            self,
            "Backend Error",
            f"Backend processing failed:\n\n{error_message}\n\n"
            f"The system will use frontend optimization instead."
        )
        
        self._backend_ready = False
    
    def get_backend_folder_path(self):
        """Get path to backend folder"""
        current_file = os.path.abspath(__file__)
        frontend_gui_dir = os.path.dirname(current_file)
        frontend_dir = os.path.dirname(frontend_gui_dir)
        project_root = os.path.dirname(frontend_dir)
        return os.path.join(project_root, 'backend')
    
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
        
        # Reset solution and restart backend processing
        self.solution = None
        self.waves_data = []
        self._backend_ready = False
        
        # Restart backend processing
        self.start_backend_processing_with_dialog()
    
    def update_status_bar(self):
        """Update status bar with current info"""
        try:
            if self._widgets_destroyed:
                return
            
            total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
            avg_deliveries = math.ceil(len(self.delivery_points) / max(1, total_vehicles))
            
            backend_status = "✅ Backend Ready" if self._backend_ready else "⏳ Processing..."
            
            status = (
                f"{backend_status} | "
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
        
        # Stop backend thread if running
        try:
            if hasattr(self, 'backend_thread') and self.backend_thread.isRunning():
                self.backend_thread.quit()
                self.backend_thread.wait(3000)
        except Exception as e:
            print(f"Error stopping backend thread: {e}")
        
        # Stop controllers
        try:
            self.wave_controller.stop()
            self.vehicle_controller.cleanup()
        except Exception as e:
            print(f"Error stopping controllers: {e}")
        
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