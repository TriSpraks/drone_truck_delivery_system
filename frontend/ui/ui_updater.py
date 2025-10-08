"""
UI Updater Module
Handles UI label and status updates
"""
import math


class UIUpdater:
    """Helper class for updating UI components"""
    
    @staticmethod
    def update_depot_info(parent):
        """Update depot and fleet information labels"""
        try:
            if parent._widgets_destroyed:
                return
            
            parent.depot_info_label.setText(
                f"Depot: {parent.depot_coords[0]:.4f}, {parent.depot_coords[1]:.4f}"
            )
            parent.customer_info_label.setText(f"Customers: {parent.customer_count}")
            parent.fleet_info_label.setText(
                f"Fleet: {parent.electric_trucks}E + "
                f"{parent.fuel_trucks}F + {parent.drones}D"
            )
            
            total_vehicles = (parent.electric_trucks + 
                            parent.fuel_trucks + 
                            parent.drones)
            parent.fleet_summary_label.setText(f"Total Vehicles: {total_vehicles}")
            
            UIUpdater.update_status_bar(parent)
        except Exception as e:
            print(f"Error updating depot info: {e}")
    
    @staticmethod
    def update_status_bar(parent):
        """Update status bar with current system info"""
        try:
            if parent._widgets_destroyed:
                return
            
            total_vehicles = (parent.electric_trucks + 
                            parent.fuel_trucks + 
                            parent.drones)
            avg_deliveries = math.ceil(
                len(parent.delivery_points) / max(1, total_vehicles)
            )
            
            status = (
                f"Depot: {parent.depot_coords[0]:.4f}, {parent.depot_coords[1]:.4f} | "
                f"Fleet: {total_vehicles} vehicles | "
                f"Coverage: {len(parent.delivery_points)} points "
                f"(~{avg_deliveries} per vehicle)"
            )
            
            parent.statusBar().showMessage(status)
        except Exception as e:
            print(f"Error updating status bar: {e}")
    
    @staticmethod
    def update_vehicle_statuses(parent):
        """Update all vehicle statuses in the control panel"""
        try:
            if parent._widgets_destroyed:
                return
            
            for vehicle_name in parent.vehicle_manager.vehicles.keys():
                vehicle_data = parent.vehicle_manager.get_vehicle_data_for_ui(
                    vehicle_name
                )
                if vehicle_data and hasattr(parent.vehicle_control, 'update_vehicle_status'):
                    parent.vehicle_control.update_vehicle_status(vehicle_data)
        except Exception as e:
            print(f"Error updating vehicle statuses: {e}")