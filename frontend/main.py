#!/usr/bin/env python3
"""
Main entry point for India Airspace Management System - Enhanced with Analytics Dashboard
"""
import sys
import os

# Change to the script's directory to ensure consistent imports and file paths
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt
from gui.main_window import IndiaAirspaceMap
from ui.dialog import DepotSelectionWindow
from config.app_config import DARK_STYLE


class MainContainer(QMainWindow):
    """Container that manages the transition from depot selection to main application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Truck Delivery System")
        self.setGeometry(50, 50, 1800, 1000)
        self.setMinimumSize(1600, 900)
        self.setStyleSheet(DARK_STYLE)
        
        # Create stacked widget to hold different views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create depot selection as a widget (not dialog)
        self.depot_selection = DepotSelectionWindow(parent=self, as_widget=True)
        self.depot_selection.depot_selected.connect(self.on_depot_selected)
        
        # Add depot selection to stack
        self.stacked_widget.addWidget(self.depot_selection)
        
        # Main application window (created after depot selection)
        self.main_window = None
        
        # Show maximized
        self.showMaximized()
    
    def on_depot_selected(self, lat, lng, customer_count, electric_trucks, fuel_trucks, drones):
        """Handle depot selection and transition to main application"""
        # Stop the selection timer
        if hasattr(self.depot_selection, 'selection_timer'):
            self.depot_selection.selection_timer.stop()
        
        selected_depot = [lat, lng]
        total_vehicles = electric_trucks + fuel_trucks + drones
        
        print(f"Configuration selected:")
        print(f"  Depot: {lat:.6f}, {lng:.6f}")
        print(f"  Customers: {customer_count}")
        print(f"  Fleet: {electric_trucks} electric trucks, {fuel_trucks} fuel trucks, {drones} drones")
        print(f"  Total vehicles: {total_vehicles}")
        
        print(f"\nLaunching main application with full configuration...")
        
        # Create main window with all selected parameters
        self.main_window = IndiaAirspaceMap(
            depot_coords=selected_depot, 
            customer_count=customer_count,
            electric_trucks=electric_trucks,
            fuel_trucks=fuel_trucks,
            drones=drones
        )
        
        # Add main window to stack and switch to it
        self.stacked_widget.addWidget(self.main_window)
        self.stacked_widget.setCurrentWidget(self.main_window)
        
        # Update window title
        self.setWindowTitle("India Airspace Management - Optimized Fleet System")
        
        print("\n" + "="*70)
        print("INDIA AIRSPACE MANAGEMENT SYSTEM LAUNCHED!")
        print("="*70)
        print("Configuration Applied:")
        print(f"📍 Depot Location: {selected_depot[0]:.6f}, {selected_depot[1]:.6f}")
        print(f"👥 Customers: {customer_count}")
        print(f"🚚 Fleet Configuration:")
        print(f"   • Electric Trucks: {electric_trucks}")
        print(f"   • Fuel Trucks: {fuel_trucks}")
        print(f"   • Drones: {drones}")
        print(f"   • Total Vehicles: {total_vehicles}")
        print(f"📦 Delivery Points: {customer_count} points generated around depot")
        print("\nFeatures:")
        print("✅ Custom Fleet Configuration Applied")
        print("✅ Comprehensive No-Fly Zones across India")
        print("✅ Real-time Vehicle Movement (NO map reloading)")
        print("✅ Left Sidebar: Vehicle Controls & Delivery Info")
        print("✅ Right Sidebar: Delivery Performance Analytics")
        print("✅ Backend Optimization: Finds optimal routes for all vehicles")
        print("✅ Interactive Controls:")
        print("   • Change Depot Location & Fleet Configuration (anytime)")
        print("   • Toggle No-Fly Zones")
        print("   • Toggle Vehicles")
        print("   • Start/Stop Vehicle Movement")
        print(f"\n Your Fleet ({total_vehicles} vehicles):")
        print(f"• Drones: {drones} units - Blue icons with dotted routes (60 km/h)")
        print(f"• Electric Trucks: {electric_trucks} units - Green icons (40 km/h)")
        print(f"• Fuel Trucks: {fuel_trucks} units - Orange icons (35 km/h)")
        print(f"\n📦 Delivery System:")
        print("• All vehicles start from YOUR selected depot")
        print(f"• {customer_count} delivery points generated around depot")
        print("• Real-time vehicle trails and status monitoring")
        print("• Each vehicle gets assigned a delivery route")
        print("\n📊 Analytics Dashboard (Right Panel):")
        print("• Cost Analysis: Compare unit costs ($/delivery)")
        print("• Distance Analysis: Avg distance per delivery by vehicle")
        print("• Capacity Utilization: Weight & volume % for trucks")
        print("• Summary Statistics: Total metrics and breakdowns")
        print("• Auto-refresh: Updates every 3 seconds from backend")
        print("\n🎯 Advanced Features:")
        print("• Full depot & fleet reconfiguration without restarting")
        print("• Automatic delivery point regeneration")
        print("• Backend-optimized routing (OSRM integration)")
        print("• Comprehensive vehicle status tracking")
        print("• Real-time performance metrics visualization")
        print("• Scalable fleet management (up to 200 vehicles total)")
        print("="*70)
    
    def closeEvent(self, event):
        """Clean up on close"""
        # Stop the selection timer
        if hasattr(self.depot_selection, 'selection_timer'):
            self.depot_selection.selection_timer.stop()
        
        # Clean up depot selection map
        if hasattr(self.depot_selection, 'map_path'):
            try:
                if os.path.exists(self.depot_selection.map_path):
                    os.remove(self.depot_selection.map_path)
            except Exception as e:
                print(f"Error cleaning up depot selection map: {e}")
        
        # Clean up main app if it exists
        if self.main_window:
            # Close analytics dashboard
            if hasattr(self.main_window, 'analytics_dashboard'):
                if hasattr(self.main_window.analytics_dashboard, 'refresh_timer'):
                    self.main_window.analytics_dashboard.refresh_timer.stop()
            
            # Close main window
            self.main_window.closeEvent(event)
        
        event.accept()


def main():
    """Main application entry point with depot, customer, and fleet selection"""
    app = QApplication(sys.argv)
    app.setApplicationName("India Airspace Management - Analytics & Optimization")
    app.setStyle('Fusion')
    
    print("Starting Depot & Fleet Configuration Selection...")
    print("="*70)
    
    # Create container (handles depot selection -> main app transition)
    container = MainContainer()
    
    # Start the application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()