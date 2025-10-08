"""
Vehicle Controller Module
Handles vehicle start, stop, and movement control
"""
import time
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt, QTimer


class VehicleController:
    """Controls vehicle operations"""
    
    def __init__(self, parent):
        self.parent = parent
        self.route_builder = None
        self.progress_dialog = None
    
    def toggle_start_stop(self):
        """Toggle vehicle start/stop"""
        if self.parent.start_stop_action.isChecked():
            self.start_vehicles_optimized()
        else:
            self.parent.vehicle_manager.pause_vehicles()
            self.parent.start_stop_action.setText("▶ Resume Vehicles")
    
    def start_vehicles_optimized(self):
        """Start vehicle simulation with optimized routing"""
        if not self.parent.map_handler.map_ready:
            QMessageBox.warning(
                self.parent,
                "Map Not Ready",
                "Please wait for map to load"
            )
            return False
        
        if not self.parent.vehicle_manager.vehicles_started:
            # Wait for backend if still processing
            if (hasattr(self.parent, 'backend_processor') and 
                self.parent.backend_processor.isRunning()):
                QMessageBox.information(
                    self.parent,
                    "Backend Processing",
                    "Backend is computing routes. Please wait."
                )
                return False
            
            # Create assignments
            if self.parent.waves_data:
                delivery_assignments = self.parent.vehicle_manager.create_assignments_from_waves(
                    self.parent.waves_data,
                    self.parent.customer_nodes
                )
                use_backend_routes = True
            else:
                delivery_assignments = self.parent.vehicle_manager.create_optimal_delivery_assignments(
                    self.parent.delivery_points,
                    self.parent.electric_trucks,
                    self.parent.fuel_trucks,
                    self.parent.drones
                )
                use_backend_routes = False
            
            if not delivery_assignments:
                QMessageBox.warning(
                    self.parent,
                    "No Assignments",
                    "Could not create assignments"
                )
                return False
            
            # Show progress dialog
            self._show_progress_dialog()
            
            # Start route building
            from gui.route_builder import OptimizedRouteBuilder
            self.route_builder = OptimizedRouteBuilder(
                self.parent.depot_coords,
                delivery_assignments,
                self.parent,
                preserve_backend_order=use_backend_routes
            )
            self.route_builder.progress_updated.connect(self.on_route_progress)
            self.route_builder.all_routes_completed.connect(self.on_routes_completed)
            self.route_builder.start()
            
            self.parent.vehicle_manager.vehicles_started = True
        else:
            # Resume
            self.parent.vehicle_manager.vehicles_paused = False
            self.parent.start_stop_action.setChecked(True)
            self.parent.start_stop_action.setText("⏸ Pause Vehicles")
        
        return True
    
    def _show_progress_dialog(self):
        """Show progress dialog"""
        self.parent._progress_mutex.lock()
        try:
            self.progress_dialog = QProgressDialog(
                "Building routes...",
                "Cancel",
                0, 100,
                self.parent
            )
            self.progress_dialog.setWindowModality(Qt.NonModal)
            self.progress_dialog.show()
        finally:
            self.parent._progress_mutex.unlock()
    
    def on_route_progress(self, progress, status):
        """Handle route building progress"""
        if self.parent._widgets_destroyed:
            return
        
        self.parent._progress_mutex.lock()
        try:
            if self.progress_dialog:
                self.progress_dialog.setValue(progress)
                self.progress_dialog.setLabelText(status)
                
                if self.progress_dialog.wasCanceled():
                    if self.route_builder:
                        self.route_builder.requestInterruption()
                    self.parent.vehicle_manager.vehicles_started = False
                    self.progress_dialog = None
        finally:
            self.parent._progress_mutex.unlock()
    
    def on_routes_completed(self, vehicles_dict):
        """Handle route building completion"""
        if self.parent._widgets_destroyed:
            return
        
        # Close progress dialog
        self._close_progress_dialog()
        
        # Update vehicle manager
        self.parent.vehicle_manager.vehicles = vehicles_dict
        self.parent.vehicle_manager.wave_running = True
        self.parent.vehicle_manager.wave_start_time = time.time()
        
        # Send to map
        self.parent.map_handler.send_vehicles_to_map_batch(vehicles_dict)
        
        # Show success
        stats = self.parent.vehicle_manager.get_wave_statistics()
        QMessageBox.information(
            self.parent,
            "Fleet Optimized",
            f"Vehicles: {stats['vehicle_count']}\n"
            f"Deliveries: {stats['deliveries']}\n"
            f"Distance: {stats['distance']:.2f} km\n"
            f"Cost: ${stats['cost']:.2f}"
        )
        
        # Update UI
        self.parent.start_stop_action.setText("⏸ Pause Vehicles")
        self.parent.restart_action.setVisible(True)
    
    def _close_progress_dialog(self):
        """Close progress dialog"""
        self.parent._progress_mutex.lock()
        try:
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
        finally:
            self.parent._progress_mutex.unlock()
    
    def tick_movement(self):
        """Update vehicle positions"""
        if not self.parent.vehicle_manager.vehicles_started or self.parent._widgets_destroyed:
            return
        
        # Move vehicles
        moved = self.parent.vehicle_manager.tick_movement()
        
        if moved:
            self.parent.map_handler.pending_map_update = True
            
            # Update UI every 3 seconds
            if int(time.time()) % 3 == 0:
                self.update_vehicle_ui()
        
        # Check if wave completed
        if (self.parent.vehicle_manager.wave_running and
            self.parent.vehicle_manager.all_vehicles_returned() and
            not self.parent.wave_controller.wave_completed):
            self.parent.wave_controller.on_wave_completed()
    
    def update_vehicle_ui(self):
        """Update vehicle status in UI"""
        for vehicle_name in self.parent.vehicle_manager.vehicles.keys():
            vehicle_data = self.parent.vehicle_manager.get_vehicle_data_for_ui(vehicle_name)
            if vehicle_data and hasattr(self.parent.vehicle_control, 'update_vehicle_status'):
                self.parent.vehicle_control.update_vehicle_status(vehicle_data)
    
    def restart_vehicles(self):
        """Restart vehicles from beginning"""
        if not self.parent.vehicle_manager.vehicles_started:
            return
        
        self.parent.vehicle_manager.restart_vehicles()
        self.parent.start_stop_action.setChecked(True)
        self.parent.start_stop_action.setText("⏸ Pause Vehicles")
        self.parent.map_handler.send_vehicles_to_map_batch(
            self.parent.vehicle_manager.vehicles
        )
        
        QMessageBox.information(
            self.parent,
            "Vehicles Restarted",
            "All vehicles reset to depot and restarted."
        )
    
    def stop_vehicles_complete(self):
        """Completely stop and clear vehicles"""
        self.parent.vehicle_manager.vehicles_started = False
        self.parent.vehicle_manager.vehicles_paused = False
        self.parent.vehicle_manager.wave_running = False
        
        # Cancel route building
        if self.route_builder and self.route_builder.isRunning():
            self.route_builder.requestInterruption()
            self.route_builder.quit()
            self.route_builder.wait(3000)
        
        # Clear progress dialog
        self._close_progress_dialog()
        
        # Clear vehicles
        self.parent.vehicle_manager.vehicles.clear()
        
        # Clear UI
        if hasattr(self.parent.vehicle_control, 'status_list'):
            self.parent.vehicle_control.status_list.clear()
        
        # Clear map
        self.parent.map_handler.clear_all_vehicles()
        
        # Reset buttons
        self.parent.start_stop_action.setChecked(False)
        self.parent.start_stop_action.setText("▶ Start Vehicles")
        self.parent.restart_action.setVisible(False)
    
    def cleanup(self):
        """Clean up controller resources"""
        if self.route_builder and self.route_builder.isRunning():
            self.route_builder.requestInterruption()
            self.route_builder.quit()
            self.route_builder.wait(3000)
        
        self._close_progress_dialog()