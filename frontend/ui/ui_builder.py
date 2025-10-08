"""
UI Builder Module
Handles all UI component creation for the main window
"""
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                              QToolBar, QAction, QWidget)
from PyQt5.QtCore import Qt

from widgets.vehicle_control import VehicleControlPanel
from widgets.delivery_info import DeliveryInfoWidget
from widgets.sound_monitoring import SoundGraphWidget, NoiseStatisticsWidget


class UIBuilder:
    """Builds UI components for the main window"""
    
    @staticmethod
    def create_left_panel(parent):
        """Create left sidebar panel with controls"""
        left_panel = QFrame()
        left_panel.setMaximumWidth(400)
        left_panel.setMinimumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        
        # Title
        title_label = QLabel("Drone Truck Delivery System")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ff6b35; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Info labels
        depot_info_label = QLabel(f"Depot: {parent.depot_coords[0]:.4f}, {parent.depot_coords[1]:.4f}")
        depot_info_label.setStyleSheet("font-size: 13px; color: #cccccc; padding: 5px;")
        depot_info_label.setAlignment(Qt.AlignCenter)
        
        customer_info_label = QLabel(f"Customers: {parent.customer_count}")
        customer_info_label.setStyleSheet("font-size: 13px; color: #8b5cf6; font-weight: bold; padding: 5px;")
        customer_info_label.setAlignment(Qt.AlignCenter)
        
        total_vehicles = parent.electric_trucks + parent.fuel_trucks + parent.drones
        fleet_info_label = QLabel(f"Fleet: {parent.electric_trucks}E + {parent.fuel_trucks}F + {parent.drones}D")
        fleet_info_label.setStyleSheet("font-size: 13px; color: #4CAF50; font-weight: bold; padding: 5px;")
        fleet_info_label.setAlignment(Qt.AlignCenter)
        
        fleet_summary_label = QLabel(f"Total Vehicles: {total_vehicles}")
        fleet_summary_label.setStyleSheet("font-size: 13px; color: #FF9800; padding: 2px;")
        fleet_summary_label.setAlignment(Qt.AlignCenter)
        
        # Control panels
        try:
            vehicle_control = VehicleControlPanel()
            delivery_info = DeliveryInfoWidget(parent.depot_coords, parent.customer_count)
        except Exception as e:
            print(f"Error creating control panels: {e}")
            vehicle_control = QWidget()
            delivery_info = QWidget()
        
        # Add to layout
        left_layout.addWidget(title_label)
        left_layout.addWidget(depot_info_label)
        left_layout.addWidget(customer_info_label)
        left_layout.addWidget(fleet_info_label)
        left_layout.addWidget(fleet_summary_label)
        left_layout.addWidget(vehicle_control)
        left_layout.addWidget(delivery_info)
        
        # Store references in parent
        parent.depot_info_label = depot_info_label
        parent.customer_info_label = customer_info_label
        parent.fleet_info_label = fleet_info_label
        parent.fleet_summary_label = fleet_summary_label
        parent.vehicle_control = vehicle_control
        parent.delivery_info = delivery_info
        
        return left_panel
    
    @staticmethod
    def create_right_panel(parent):
        """Create right sidebar panel with sound monitoring"""
        right_panel = QFrame()
        right_panel.setMaximumWidth(400)
        right_panel.setMinimumWidth(350)
        right_layout = QVBoxLayout(right_panel)
        
        # Sound monitoring title
        sound_title = QLabel("Drone Sound Monitoring")
        sound_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff6b35; padding: 10px;")
        
        try:
            sound_graphs = SoundGraphWidget()
            noise_stats = NoiseStatisticsWidget()
        except Exception as e:
            print(f"Error creating sound widgets: {e}")
            sound_graphs = QWidget()
            noise_stats = QWidget()
        
        right_layout.addWidget(sound_title)
        right_layout.addWidget(sound_graphs, 2)
        right_layout.addWidget(noise_stats, 1)
        
        # Store references in parent
        parent.sound_graphs = sound_graphs
        parent.noise_stats = noise_stats
        
        return right_panel
    
    @staticmethod
    def create_toolbar(parent):
        """Create toolbar with actions"""
        toolbar = QToolBar()
        
        # Change depot action
        change_depot_action = QAction("🚩 Change Depot & Fleet", parent)
        change_depot_action.triggered.connect(parent.change_depot_location)
        toolbar.addAction(change_depot_action)
        
        toolbar.addSeparator()
        
        # Toggle NFZ
        toggle_nfz_action = QAction("Toggle No-Fly Zones", parent)
        toggle_nfz_action.setCheckable(True)
        toggle_nfz_action.setChecked(True)
        toggle_nfz_action.triggered.connect(parent.toggle_no_fly_zones)
        toolbar.addAction(toggle_nfz_action)
        
        # Toggle vehicles
        toggle_vehicles_action = QAction("Toggle Vehicles", parent)
        toggle_vehicles_action.setCheckable(True)
        toggle_vehicles_action.setChecked(True)
        toggle_vehicles_action.triggered.connect(parent.toggle_vehicles)
        toolbar.addAction(toggle_vehicles_action)
        
        toolbar.addSeparator()
        
        # Start/Stop
        start_stop_action = QAction("▶ Start Vehicles", parent)
        start_stop_action.setCheckable(True)
        start_stop_action.triggered.connect(parent.toggle_start_stop_vehicles)
        toolbar.addAction(start_stop_action)
        
        # Next Wave (hidden initially)
        next_wave_action = QAction("⏭ Next Wave", parent)
        next_wave_action.triggered.connect(parent.start_next_wave)
        next_wave_action.setVisible(False)
        toolbar.addAction(next_wave_action)
        
        # Restart
        restart_action = QAction("🔄 Restart", parent)
        restart_action.triggered.connect(parent.restart_vehicles)
        restart_action.setVisible(False)
        toolbar.addAction(restart_action)
        
        # Store references in parent
        parent.change_depot_action = change_depot_action
        parent.toggle_nfz_action = toggle_nfz_action
        parent.toggle_vehicles_action = toggle_vehicles_action
        parent.start_stop_action = start_stop_action
        parent.next_wave_action = next_wave_action
        parent.restart_action = restart_action
        
        return toolbar