"""
Main container that manages transition between depot selection and main application
"""
from PyQt5.QtWidgets import QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt
from config.app_config import DARK_STYLE
from ui.dialog import DepotSelectionWindow
from main import IndiaAirspaceMap


class MainContainer(QMainWindow):
    """Container window that manages depot selection and main application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Truck Delivery System")
        self.setGeometry(50, 50, 1800, 1000)
        self.setMinimumSize(1600, 900)
        
        # Apply dark theme
        self.setStyleSheet(DARK_STYLE)
        
        # Create stacked widget to hold different views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create depot selection page (not as dialog, but as widget)
        self.depot_selection = DepotSelectionWindow(parent=self, as_widget=True)
        self.depot_selection.depot_selected.connect(self.on_depot_confirmed)
        
        # Add depot selection to stack
        self.stacked_widget.addWidget(self.depot_selection)
        
        # Main application will be added after depot selection
        self.main_app = None
        
        # Show maximized
        self.showMaximized()
    
    def on_depot_confirmed(self, lat, lng, customer_count, electric_trucks, fuel_trucks, drones):
        """Handle depot confirmation and switch to main application"""
        # Stop the selection timer if it exists
        if hasattr(self.depot_selection, 'selection_timer'):
            self.depot_selection.selection_timer.stop()
        
        # Create main application with selected configuration
        self.main_app = IndiaAirspaceMap(
            depot_coords=[lat, lng],
            customer_count=customer_count,
            electric_trucks=electric_trucks,
            fuel_trucks=fuel_trucks,
            drones=drones
        )
        
        # Add main app to stack and switch to it
        self.stacked_widget.addWidget(self.main_app)
        self.stacked_widget.setCurrentWidget(self.main_app)
        
        # Update window title
        self.setWindowTitle("India Airspace Management - Optimized Fleet System")
    
    def closeEvent(self, event):
        """Clean up on close"""
        # Clean up depot selection
        if hasattr(self.depot_selection, 'selection_timer'):
            self.depot_selection.selection_timer.stop()
        
        if hasattr(self.depot_selection, 'map_path'):
            import os
            try:
                if os.path.exists(self.depot_selection.map_path):
                    os.remove(self.depot_selection.map_path)
            except Exception as e:
                print(f"Error cleaning up depot selection map: {e}")
        
        # Clean up main app if it exists
        if self.main_app:
            self.main_app.closeEvent(event)
        
        event.accept()