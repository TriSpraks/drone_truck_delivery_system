"""
Vehicle control panel widget - UPDATED to match Delivery Information exactly
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                           QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt

class VehicleControlPanel(QWidget):
    """Control panel for vehicle tracking"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status display matching Delivery Information style
        status_group = QGroupBox("Vehicle Status")
        status_group.setStyleSheet("""
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
        
        status_layout = QVBoxLayout(status_group)
        
        # QListWidget with exact same styling as Delivery Information
        self.status_list = QListWidget()
        self.status_list.setMinimumHeight(150)
        self.status_list.setWordWrap(True)
        self.status_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Exact same styling as delivery_list in DeliveryInfoWidget with visible borders
        self.status_list.setStyleSheet("""
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
            QScrollBar:horizontal {
                height: 0px;
                background: transparent;
            }
        """)
        
        status_layout.addWidget(self.status_list, 1)
        layout.addWidget(status_group, 1)
    
    def update_vehicle_status(self, vehicle_data):
        """Update vehicle status matching Delivery Information format"""
        # Format exactly like delivery items
        status_text = f"🚁 {vehicle_data.vehicle_id}\n"
        status_text += f"Type: {vehicle_data.vehicle_type}\n"
        
        # Status with indicator
        status_icon = "🟢" if vehicle_data.status == "Moving" else "🔴" if vehicle_data.status == "Stopped" else "🟡"
        status_text += f"Status: {status_icon} {vehicle_data.status}\n"
        
        status_text += f"Speed: {vehicle_data.speed:.1f} km/h\n"
        status_text += f"Position:\n"
        status_text += f"Lat: {vehicle_data.lat:.6f}\n"
        status_text += f"Lon: {vehicle_data.lon:.6f}"
        
        # Find existing item or create new
        found = False
        for i in range(self.status_list.count()):
            item = self.status_list.item(i)
            if vehicle_data.vehicle_id in item.text():
                item.setText(status_text)
                found = True
                break
        
        if not found:
            # Add new item without size hint (natural sizing like delivery list)
            item = QListWidgetItem(status_text)
            self.status_list.addItem(item)
    
    def clear_vehicle_status(self):
        """Clear all vehicle status items"""
        self.status_list.clear()
    
    def get_vehicle_count(self):
        """Get current number of vehicles being tracked"""
        return self.status_list.count()
    
    def remove_vehicle_status(self, vehicle_id):
        """Remove a specific vehicle from the status list"""
        for i in range(self.status_list.count()):
            item = self.status_list.item(i)
            if vehicle_id in item.text():
                self.status_list.takeItem(i)
                break