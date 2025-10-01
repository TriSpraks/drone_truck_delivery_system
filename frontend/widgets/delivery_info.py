"""
Delivery information widget - FIXED VERSION
Added proper null checks and widget validation to prevent RuntimeError
"""
import math
import random
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                           QListWidget, QGridLayout)
from PyQt5.QtCore import Qt
from core.data_manager import DeliveryPoint

class DeliveryInfoWidget(QWidget):
    """Display delivery points information - now with proper error handling"""
    def __init__(self, depot_coords=None, customer_count=5):
        super().__init__()
        self.depot_coords = depot_coords
        self.customer_count = customer_count
        self._widget_destroyed = False  # Track widget state
        self.init_ui()
        if depot_coords:
            self.setup_delivery_points()
        
    def init_ui(self):
        """Initialize UI with proper error handling"""
        try:
            layout = QVBoxLayout(self)
            
            # Depot info
            depot_group = QGroupBox("Depot Information")
            depot_group.setStyleSheet("""
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
            depot_layout = QVBoxLayout(depot_group)
            
            self.depot_info = QLabel("No depot selected")
            self.depot_info.setStyleSheet("font-size: 12px; color: #ff6b35;")
            depot_layout.addWidget(self.depot_info)
            
            # Customer count info
            self.customer_info = QLabel(f"Customers: {self.customer_count}")
            self.customer_info.setStyleSheet("font-size: 12px; color: #8b5cf6; font-weight: bold;")
            depot_layout.addWidget(self.customer_info)
            
            info_group = QGroupBox("Delivery Information")
            info_group.setStyleSheet("""
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
    QScrollBar:vertical {
        width: 12px;
        border-radius: 5px;
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
            
            info_layout = QVBoxLayout(info_group)
            
            self.delivery_list = QListWidget()
            self.delivery_list.setWordWrap(True)
            self.delivery_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            info_layout.addWidget(self.delivery_list)
            
            
            # Summary
            summary_group = QGroupBox("Summary")
            summary_group.setStyleSheet("""
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
            summary_layout = QGridLayout(summary_group)
            
            self.total_points = QLabel("0")
            self.total_weight = QLabel("0.0 kg")
            self.total_distance = QLabel("0.0 km")
            
            summary_layout.addWidget(QLabel("Total Points:"), 0, 0)
            summary_layout.addWidget(self.total_points, 0, 1)
            summary_layout.addWidget(QLabel("Total Weight:"), 1, 0)
            summary_layout.addWidget(self.total_weight, 1, 1)
            summary_layout.addWidget(QLabel("Total Distance:"), 2, 0)
            summary_layout.addWidget(self.total_distance, 2, 1)
            
            layout.addWidget(info_group)
            layout.addWidget(summary_group)
            
        except Exception as e:
            print(f"Error initializing DeliveryInfoWidget UI: {e}")
            self._widget_destroyed = True
    
    def _is_valid_widget(self, widget):
        """Check if widget is valid and not destroyed"""
        try:
            if widget is None:
                return False
            # Try to access a basic property to verify widget is still valid
            _ = widget.isVisible()
            return True
        except (RuntimeError, AttributeError):
            return False
    
    def _safe_set_text(self, widget, text):
        """Safely set text on a widget with error handling"""
        try:
            if self._widget_destroyed:
                return False
            if not self._is_valid_widget(widget):
                print(f"Widget is no longer valid, skipping text update")
                return False
            widget.setText(str(text))
            return True
        except (RuntimeError, AttributeError) as e:
            print(f"Error setting widget text: {e}")
            self._widget_destroyed = True
            return False
    
    def update_depot(self, depot_coords, customer_count=None):
        """Update depot coordinates and customer count with error handling"""
        try:
            if self._widget_destroyed:
                print("Widget destroyed, skipping depot update")
                return
                
            self.depot_coords = depot_coords
            if customer_count is not None:
                self.customer_count = customer_count
            
            # Safely update depot info
            depot_text = f"Depot: {depot_coords[0]:.4f}, {depot_coords[1]:.4f}"
            if not self._safe_set_text(self.depot_info, depot_text):
                return
            
            # Safely update customer info
            customer_text = f"Customers: {self.customer_count}"
            if not self._safe_set_text(self.customer_info, customer_text):
                return
            
            # Setup delivery points if widgets are still valid
            if self._is_valid_widget(self.delivery_list):
                self.setup_delivery_points()
            else:
                print("Delivery list widget invalid, skipping setup")
                
        except Exception as e:
            print(f"Error updating depot in DeliveryInfoWidget: {e}")
            self._widget_destroyed = True
            
    def setup_delivery_points(self):
        """Setup delivery points with comprehensive error handling"""
        try:
            if self._widget_destroyed:
                return
                
            if not self.depot_coords:
                return
            
            # Check if delivery list is still valid
            if not self._is_valid_widget(self.delivery_list):
                print("Delivery list widget is no longer valid")
                return
                
            self.delivery_list.clear()
            
            # Generate delivery points around the depot (within 10-50km radius)
            delivery_points = []
            depot_lat, depot_lon = self.depot_coords
            
            for i in range(self.customer_count):
                # Generate random points around depot
                angle = random.uniform(0, 360)
                distance_km = random.uniform(10, 50)  # 10-50 km from depot
                
                # Convert to lat/lon offset
                lat_offset = (distance_km / 111.32) * math.cos(math.radians(angle))
                lon_offset = (distance_km / (111.32 * math.cos(math.radians(depot_lat)))) * math.sin(math.radians(angle))
                
                point_lat = depot_lat + lat_offset
                point_lon = depot_lon + lon_offset
                
                point = DeliveryPoint(
                    name=f"Customer {i+1}",
                    address=f"Delivery Location {i+1} - {distance_km:.1f}km from depot",
                    lat=point_lat,
                    lon=point_lon,
                    weight=random.uniform(1.0, 5.0),
                    distance=distance_km
                )
                delivery_points.append(point)
            
            # Sort by distance
            delivery_points.sort(key=lambda p: p.distance)
            
            total_weight = 0
            total_distance = 0
            
            # Add items to list with error checking
            for point in delivery_points:
                if not self._is_valid_widget(self.delivery_list):
                    break
                    
                item_text = f"{point.name}\n{point.address}\nWeight: {point.weight:.1f} kg\nDistance: {point.distance:.1f} km"
                try:
                    self.delivery_list.addItem(item_text)
                except RuntimeError as e:
                    print(f"Error adding item to delivery list: {e}")
                    break
                    
                total_weight += point.weight
                total_distance += point.distance
            
            # Update summary labels safely
            self._safe_set_text(self.total_points, str(len(delivery_points)))
            self._safe_set_text(self.total_weight, f"{total_weight:.1f} kg")
            self._safe_set_text(self.total_distance, f"{total_distance:.1f} km")
            
        except Exception as e:
            print(f"Error setting up delivery points: {e}")
            self._widget_destroyed = True
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self._widget_destroyed = True
        super().closeEvent(event)
    
    def deleteLater(self):
        """Override deleteLater to mark widget as destroyed"""
        self._widget_destroyed = True
        super().deleteLater()