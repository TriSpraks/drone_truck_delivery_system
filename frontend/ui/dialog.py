"""
Depot selection dialog - ENHANCED VERSION with standardized fonts
"""
import os
import json
import time
from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QFrame, QPushButton, QSpinBox, QFormLayout,
                           QMessageBox, QGroupBox, QLineEdit)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl, Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator
from config.app_config import DARK_STYLE
from utils.nfz_data import get_depot_selection_no_fly_zones
from resources.map_templates import DEPOT_SELECTION_HTML



class PlaceholderSpinBox(QSpinBox):
    """Custom SpinBox with placeholder text that vanishes on click"""
    
    def __init__(self, placeholder_text="", parent=None):
        super().__init__(parent)
        self.placeholder_text = placeholder_text
        self.setRange(0, 999)
        self.setValue(0)
        self.setSpecialValueText(placeholder_text)
        
    def focusInEvent(self, event):
        """Clear field when user clicks (focus in)"""
        if self.value() == self.minimum():
            line_edit = self.lineEdit()
            line_edit.clear()
            line_edit.setSelection(0, 0)
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        """Restore placeholder if field is empty when focus is lost"""
        line_edit = self.lineEdit()
        text = line_edit.text().strip()
        
        if not text or not text.isdigit():
            self.setValue(self.minimum())
        else:
            value = int(text)
            if value < 1:
                self.setValue(self.minimum())
        
        super().focusOutEvent(event)


class DepotSelectionWindow(QDialog):
    depot_selected = pyqtSignal(float, float, int, int, int, int)
    
    def __init__(self, parent=None, as_widget=False):
        super().__init__(parent)
        
        if as_widget:
            self.setWindowFlags(Qt.Widget)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | 
                               Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        
        self.setWindowTitle("Select Depot Location & Fleet Configuration - India Airspace Management")
        self.setGeometry(100, 100, 1800, 1000)
        self.setMinimumSize(1600, 800)
        
        self.as_widget = as_widget
        self.setStyleSheet(DARK_STYLE)
        
        self.selected_depot = None
        self.customer_count = 0
        self.electric_trucks = 0
        self.fuel_trucks = 0
        self.drones = 0
        self.map_ready = False
        
        self.map_center = [20.5937, 78.9629]
        self.map_zoom = 5
        
        self.no_fly_zones = get_depot_selection_no_fly_zones()
        
        self.setup_ui()
        self.create_map_file()
        self.setWindowState(Qt.WindowMaximized)
        
    def setup_ui(self):
        """Setup the user interface"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel
        left_panel = QFrame()
        left_panel.setMaximumWidth(450)
        left_panel.setMinimumWidth(400)
        left_panel.setStyleSheet("QFrame { background-color: #2d2d2d; padding: 15px; }")
        left_layout = QVBoxLayout(left_panel)
        
        # Configuration title - STANDARDIZED
        config_title = QLabel("Drone Truck Delivery System")
        config_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: #ff6b35; margin-bottom: 20px; padding: 10px;")
        
        # Customer count group - STANDARDIZED
        customer_group = QGroupBox("Delivery Configuration")
        customer_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                background-color: #333333;
                padding: 15px;
                border-radius: 8px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        customer_layout = QFormLayout(customer_group)
        
        # Customer label - STANDARDIZED (removed bold)
        customer_label = QLabel("Number of Customers:")
        customer_label.setStyleSheet(f"font-size: 13px; color: #ffffff;")

        self.customer_spinbox = PlaceholderSpinBox("Customers")
        self.customer_spinbox.setStyleSheet(f"font-size: 13px; padding: 8px;")
        self.customer_spinbox.valueChanged.connect(self.on_customer_count_changed)

        customer_layout.addRow(customer_label, self.customer_spinbox)
        
        # Fleet configuration group - STANDARDIZED
        fleet_group = QGroupBox("Fleet Configuration")
        fleet_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                background-color: #333333;
                padding: 15px;
                border-radius: 8px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        fleet_layout = QFormLayout(fleet_group)
        
        # Fleet labels - STANDARDIZED (removed bold)
        electric_label = QLabel("Electric Trucks:")
        electric_label.setStyleSheet(f"font-size: 13px; color: #4CAF50;")
        
        self.electric_spinbox = PlaceholderSpinBox("Electric Trucks")
        self.electric_spinbox.setStyleSheet(f"font-size: 13px; padding: 8px; color: #4CAF50;")
        self.electric_spinbox.valueChanged.connect(self.on_fleet_changed)
        
        fuel_label = QLabel("Fuel Trucks:")
        fuel_label.setStyleSheet(f"font-size: 13px; color: #FF9800;")

        self.fuel_spinbox = PlaceholderSpinBox("Fuel Trucks")
        self.fuel_spinbox.setStyleSheet(f"font-size: 13px; padding: 8px; color: #FF9800;")
        self.fuel_spinbox.valueChanged.connect(self.on_fleet_changed)
        
        drone_label = QLabel("Drones:")
        drone_label.setStyleSheet(f"font-size: 13px; color: #2196F3;")

        self.drone_spinbox = PlaceholderSpinBox("Drones")
        self.drone_spinbox.setStyleSheet(f"font-size: 13px; padding: 8px; color: #2196F3;")
        self.drone_spinbox.valueChanged.connect(self.on_fleet_changed)
        
        fleet_layout.addRow(electric_label, self.electric_spinbox)
        fleet_layout.addRow(fuel_label, self.fuel_spinbox)
        fleet_layout.addRow(drone_label, self.drone_spinbox)
        
        # Fleet summary - STANDARDIZED
        self.fleet_summary = QLabel()
        self.fleet_summary.setTextFormat(Qt.RichText)
        self.fleet_summary.setStyleSheet(f"""
            font-size: 13px; 
            color: #cccccc; 
            padding: 10px; 
            background-color: #404040; 
            border-radius: 4px;
            margin-top: 10px;
        """)
        self.fleet_summary.setWordWrap(True)
        self.update_fleet_summary()
        
        
        # Depot instructions - STANDARDIZED (removed inline font sizes)
        depot_instructions = QLabel("""
<b>Setup Instructions:</b><br/>
1. Configure customer count and fleet size above<br/>
2. Click on the map to choose depot location<br/>
3. Avoid red No-Fly Zones<br/>
4. Consider proximity to major cities<br/>
5. Click "Confirm" to proceed<br/>
<br/>
<b>Fleet Guidelines:</b><br/>
• Electric trucks: Eco-friendly, limited range<br/>
• Fuel trucks: Longer range, higher capacity<br/>
• Drones: Fast delivery, weather dependent<br/>
• Balance fleet based on delivery requirements<br/>
        """)
        depot_instructions.setStyleSheet(f"""
            font-size: 13px; 
            color: #ffffff; 
            padding: 15px; 
            background-color: #404040; 
            border-radius: 8px; 
            line-height: 1.4;
        """)
        depot_instructions.setWordWrap(True)
        
        # Current selection display - STANDARDIZED
        self.selection_display = QLabel("No depot selected")
        self.selection_display.setStyleSheet(f"""
            font-size: 13px; 
            color: #ff6b35; 
            font-weight: bold; 
            padding: 15px; 
            background-color: #404040; 
            border-radius: 4px; 
            text-align: center;
        """)
        self.selection_display.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(config_title)
        left_layout.addWidget(customer_group)
        left_layout.addWidget(fleet_group)
        left_layout.addWidget(self.fleet_summary)
        left_layout.addWidget(depot_instructions)
        left_layout.addWidget(self.selection_display)
        left_layout.addStretch()
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
       # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background-color: #2d2d2d; padding: 10px; }")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(0)
        header_layout.setContentsMargins(0, 0, 0, 5)

        # Main Title - STANDARDIZED (same as left panel)
        title_label = QLabel("Drone Truck Delivery System")
        title_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: #ff6b35; margin-bottom: 0px;")

        # Subtitle - STANDARDIZED
        subtitle_label = QLabel("Select Your Depot Location")
        subtitle_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #ffffff; margin-top: 0px; margin-bottom: 5px;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        # Map container
        map_container = QFrame()
        map_container.setStyleSheet("QFrame { border: 2px solid #404040; border-radius: 8px; }")
        map_container.setMinimumHeight(750)
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(3, 3, 3, 3)
        
        # Map view
        self.map_view = QWebEngineView()
        self.map_view.loadFinished.connect(self.on_map_ready)
        map_layout.addWidget(self.map_view)
        
        # Bottom controls
        controls_frame = QFrame()
        controls_frame.setStyleSheet("QFrame { background-color: #2d2d2d; padding: 15px; }")
        controls_layout = QHBoxLayout(controls_frame)
        
        # Instructions - STANDARDIZED
        instructions_label = QLabel(
            "Click anywhere on the map to select your depot location. "
            "This will generate delivery points around your depot."
        )
        instructions_label.setStyleSheet(f"font-size: 13px; color: #cccccc;")
        instructions_label.setWordWrap(True)
        self.instructions_label = instructions_label
        
        # Status display - STANDARDIZED
        self.status_label = QLabel("No location selected")
        self.status_label.setStyleSheet(f"font-size: 13px; color: #ff6b35; font-weight: bold;")
        
        # Buttons - STANDARDIZED
        self.confirm_btn = QPushButton("Confirm Configuration and Continue")
        self.confirm_btn.clicked.connect(self.confirm_depot_selection)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet(f"QPushButton {{ padding: 12px 30px; font-size: 14px; }}")
        
        self.reset_btn = QPushButton("Reset Selection")
        self.reset_btn.clicked.connect(self.reset_selection)
        self.reset_btn.setEnabled(False)
        self.reset_btn.setStyleSheet(f"QPushButton {{ padding: 10px 20px; font-size: 14px; }}")
        
        self.cancel_btn = QPushButton("Exit")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(f"QPushButton {{ padding: 10px 20px; font-size: 14px; }}")
        
        # Layout controls
        controls_layout.addWidget(instructions_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.status_label)
        controls_layout.addWidget(self.reset_btn)
        controls_layout.addWidget(self.cancel_btn)
        controls_layout.addWidget(self.confirm_btn)
        
        # Add to right layout
        right_layout.addWidget(header_frame)
        right_layout.addWidget(map_container, 1)
        right_layout.addWidget(controls_frame)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
    
    def update_fleet_summary(self):
        """Update the fleet summary display"""
        customers = self.customer_count if self.customer_count > 0 else 0
        electric = self.electric_trucks if self.electric_trucks > 0 else 0
        fuel = self.fuel_trucks if self.fuel_trucks > 0 else 0
        drones = self.drones if self.drones > 0 else 0
        total_vehicles = electric + fuel + drones
        
        summary_text = f"""<html><body>
<b>Fleet Summary:</b><br/>
Customers: {customers}<br/>
Total Vehicles: {total_vehicles}<br/>
•  Electric Trucks: {electric}<br/>
•  Fuel Trucks: {fuel}<br/>
•  Drones: {drones}<br/>
</body></html>"""
        
        self.fleet_summary.setText(summary_text)
    
    def on_customer_count_changed(self, value):
        """Handle customer count change"""
        if value > 0:
            self.customer_count = value
        else:
            self.customer_count = 0
            
        self.update_instructions()
        self.update_selection_display()
        self.update_fleet_summary()
        
        if self.map_ready and value > 0:
            js_code = f"window.updateCustomerCount({value});"
            self.map_view.page().runJavaScript(js_code)
    
    def on_fleet_changed(self):
        """Handle fleet configuration changes"""
        self.electric_trucks = self.electric_spinbox.value() if self.electric_spinbox.value() > 0 else 0
        self.fuel_trucks = self.fuel_spinbox.value() if self.fuel_spinbox.value() > 0 else 0
        self.drones = self.drone_spinbox.value() if self.drone_spinbox.value() > 0 else 0
        
        self.update_fleet_summary()
        self.update_selection_display()
    
    def update_instructions(self):
        """Update instruction text"""
        if self.customer_count > 0:
            self.instructions_label.setText(
                f"Click anywhere on the map to select your depot location. "
                f"This will generate {self.customer_count} delivery points around your depot."
            )
        else:
            self.instructions_label.setText(
                "Click anywhere on the map to select your depot location. "
                "Configure customer count first to generate delivery points."
            )
    
    def update_selection_display(self):
        """Update selection display with current configuration"""
        if self.selected_depot:
            lat, lng = self.selected_depot
            display_text = f"""Depot: {lat:.4f}, {lng:.4f}
Customers: {self.customer_count if self.customer_count > 0 else 'Not set'}
Fleet: {self.electric_trucks}E + {self.fuel_trucks}F + {self.drones}D"""
        else:
            display_text = f"""No depot selected
Customers: {self.customer_count if self.customer_count > 0 else 'Not set'}
Fleet: {self.electric_trucks}E + {self.fuel_trucks}F + {self.drones}D"""
        
        self.selection_display.setText(display_text)
    
    def create_map_file(self):
        """Create or update the HTML map file, reusing the same file to prevent multiple files"""
        # Use frontend directory for the file
        frontend_dir = os.path.dirname(os.path.dirname(__file__))
        self.map_path = os.path.join(frontend_dir, "depot_selection_map.html")

        # Clean up old HTML files before creating new one
        for file in os.listdir(frontend_dir):
            if file.endswith('.html') and (file.startswith('depot_selection_map_') or file.startswith('optimized_map_') or file == 'map.html'):
                try:
                    os.remove(os.path.join(frontend_dir, file))
                    print(f"Cleaned up old file: {file}")
                except Exception as e:
                    print(f"Error cleaning up {file}: {e}")

        with open(self.map_path, "w", encoding="utf-8") as f:
            f.write(DEPOT_SELECTION_HTML)
        self.map_view.setUrl(QUrl.fromLocalFile(self.map_path))
    
    def on_map_ready(self, success):
        """Initialize map when ready"""
        if not success:
            QMessageBox.critical(self, "Error", "Failed to load the map!")
            return
            
        self.map_ready = True
        
        suggested_locations = [
            {
            'name': 'Outskirts of Bangalore', 
             'coords': [13.0500, 77.7500], 
             'description': 'Good connectivity, away from airport NFZ'
             },
            {'name': 'Chennai Surroundings', 
             'coords': [12.8500, 80.0500], 
             'description': 'Industrial area, good for logistics'
            },
            {'name': 'Mumbai Suburbs', 
             'coords': [19.2000, 72.9500], 
             'description': 'Outside nuclear facility zone'
            },
            {'name': 'Delhi NCR Edge', 
             'coords': [28.4000, 77.3000], 
             'description': 'Away from airport and government areas'
            },
            {'name': 'Hyderabad Outskirts', 
             'coords': [17.1000, 78.6000], 
             'description': 'Developing logistics hub'
            },
            {'name': 'Pune Industrial Area', 
             'coords': [18.4000, 73.7000], 
             'description': 'Away from air force station'
            }
        ]
        
        map_data = {
            "center": self.map_center,
            "zoom": self.map_zoom,
            "cities": [
                {'name': 'New Delhi', 'coords': [28.6139, 77.2090]},
                {'name': 'Mumbai', 'coords': [19.0760, 72.8777]},
                {'name': 'Bangalore', 'coords': [12.9716, 77.5946]},
                {'name': 'Chennai', 'coords': [13.0827, 80.2707]},
                {'name': 'Kolkata', 'coords': [22.5726, 88.3639]},
                {'name': 'Hyderabad', 'coords': [17.3850, 78.4867]},
                {'name': 'Pune', 'coords': [18.5204, 73.8567]},
                {'name': 'Ahmedabad', 'coords': [23.0225, 72.5714]}
            ],
            "nfzones": self.no_fly_zones,
            "suggested": suggested_locations
        }
        
        try:
            js_code = f"window.initializeDepotMap({json.dumps(map_data)});"
            self.map_view.page().runJavaScript(js_code)
            
            if self.customer_count > 0:
                js_code = f"window.updateCustomerCount({self.customer_count});"
                self.map_view.page().runJavaScript(js_code)
            
            self.setup_js_callback()
            print("Enhanced depot selection map initialized successfully!")
        except Exception as e:
            print(f"Error initializing map: {e}")
    
    def setup_js_callback(self):
        """Setup JavaScript callback for depot selection"""
        self.selection_timer = QTimer()
        self.selection_timer.timeout.connect(self.check_selection)
        self.selection_timer.start(1000)
    
    def check_selection(self):
        """Check if user has selected a location"""
        if not self.map_ready:
            return
        
        js_code = "window.getSelectedLocation();"
        self.map_view.page().runJavaScript(js_code, self.handle_selection_result)
    
    def handle_selection_result(self, result):
        """Handle the result from JavaScript"""
        if result and isinstance(result, list) and len(result) == 2:
            lat, lng = result
            if self.selected_depot != [lat, lng]:
                self.selected_depot = [lat, lng]
                self.update_selection_ui(lat, lng)
    
    def update_selection_ui(self, lat, lng):
        """Update UI when depot is selected"""
        self.status_label.setText(f"Selected: {lat:.6f}, {lng:.6f}")
        self.update_selection_display()
        self.confirm_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
        
        print(f"Depot selected: Latitude {lat:.6f}, Longitude {lng:.6f}")
        print(f"Fleet configuration: {self.electric_trucks} electric, {self.fuel_trucks} fuel, {self.drones} drones")
    
    def reset_selection(self):
        """Reset the depot selection"""
        self.selected_depot = None
        self.status_label.setText("No location selected")
        self.update_selection_display()
        self.confirm_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        
        if self.map_ready:
            try:
                js_code = """
                if (typeof depotMarker !== 'undefined' && depotMarker) {
                    map.removeLayer(depotMarker);
                    depotMarker = null;
                }
                if (typeof selectedCoords !== 'undefined') {
                    selectedCoords = null;
                }
                var selectedElement = document.getElementById('selectedLocation');
                if (selectedElement) {
                    selectedElement.style.display = 'none';
                }
                """
                self.map_view.page().runJavaScript(js_code)
            except Exception as e:
                print(f"Error resetting map selection: {e}")
    
    def validate_configuration(self):
        """Validate the current configuration"""
        errors = []
        
        if self.customer_count <= 0:
            errors.append("Please specify the number of customers")
        
        total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
        if total_vehicles == 0:
            errors.append("Please configure at least one vehicle in your fleet")
        
        if not self.selected_depot:
            errors.append("Please select a depot location on the map")
        
        return errors
    
    def confirm_depot_selection(self):
        """Confirm the depot selection and emit signal"""
        errors = self.validate_configuration()
        if errors:
            error_message = "Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in errors)
            
            if self.customer_count <= 0:
                self.customer_spinbox.setStyleSheet(self.customer_spinbox.styleSheet() + "; border: 2px solid #ff4444;")
                QTimer.singleShot(3000, lambda: self.customer_spinbox.setStyleSheet(f"font-size: 13px; padding: 8px;"))
            
            total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
            if total_vehicles == 0:
                for spinbox in [self.electric_spinbox, self.fuel_spinbox, self.drone_spinbox]:
                    original_style = spinbox.styleSheet()
                    spinbox.setStyleSheet(original_style + "; border: 2px solid #ff4444;")
                    QTimer.singleShot(3000, lambda sb=spinbox, style=original_style: sb.setStyleSheet(style))
            
            QMessageBox.warning(self, "Configuration Incomplete", error_message)
            return
        
        lat, lng = self.selected_depot
        total_vehicles = self.electric_trucks + self.fuel_trucks + self.drones
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Depot & Fleet Configuration")
        
        msg_box.setText(
            f"Confirm your configuration:\n\n"
            f"Depot Location:\n   Latitude: {lat:.6f}\n   Longitude: {lng:.6f}\n\n"
            f"Customers: {self.customer_count}\n\n"
            f"Fleet Configuration:\n"
            f"   • Electric Trucks: {self.electric_trucks}\n"
            f"   • Fuel Trucks: {self.fuel_trucks}\n"
            f"   • Drones: {self.drones}\n"
            f"   • Total Vehicles: {total_vehicles}\n\n"
            f"This will generate {self.customer_count} delivery points around your depot.\n\n"
            f"Proceed to main application?"
        )
        
        msg_box.setIcon(QMessageBox.NoIcon)
        msg_box.addButton("Yes", QMessageBox.YesRole)
        msg_box.addButton("No", QMessageBox.NoRole)
        
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QMessageBox QLabel {{
                color: #ffffff;
                font-size: 13px;
                padding: 10px;
            }}
            QPushButton {{
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: #505050;
                border-color: #666666;
            }}
            QPushButton:pressed {{
                background-color: #353535;
            }}
        """)
        
        reply = msg_box.exec_()
        
        if reply == 0:
            self.depot_selected.emit(
                lat, lng, 
                self.customer_count,
                self.electric_trucks, 
                self.fuel_trucks, 
                self.drones
            )
            print(f"Configuration confirmed:")
            print(f"  Depot: {lat:.6f}, {lng:.6f}")
            print(f"  Customers: {self.customer_count}")
            print(f"  Fleet: {self.electric_trucks}E + {self.fuel_trucks}F + {self.drones}D")
            
            if not self.as_widget:
                self.accept()
    
    def accept(self):
        """Override accept to clean up"""
        if hasattr(self, 'selection_timer'):
            self.selection_timer.stop()
        # Clean up the generated HTML file
        try:
            if hasattr(self, 'map_path') and os.path.exists(self.map_path):
                os.remove(self.map_path)
                print(f"Cleaned up map file: {self.map_path}")
        except Exception as e:
            print(f"Error cleaning up map file: {e}")
        super().accept()

    def reject(self):
        """Override reject to clean up"""
        if hasattr(self, 'selection_timer'):
            self.selection_timer.stop()
        # Clean up the generated HTML file
        try:
            if hasattr(self, 'map_path') and os.path.exists(self.map_path):
                os.remove(self.map_path)
                print(f"Cleaned up map file: {self.map_path}")
        except Exception as e:
            print(f"Error cleaning up map file: {e}")
        super().reject()
    
    def closeEvent(self, event):
        """Clean up on close"""
        if hasattr(self, 'selection_timer'):
            self.selection_timer.stop()
        
        try:
            if hasattr(self, 'map_path') and os.path.exists(self.map_path):
                os.remove(self.map_path)
                print(f"Cleaned up map file: {self.map_path}")
        except Exception as e:
            print(f"Error cleaning up map file: {e}")

        event.accept()
