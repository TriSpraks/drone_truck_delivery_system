"""
Widgets package initialization - UPDATED for Analytics Dashboard
"""

# Import widgets
from .vehicle_control import VehicleControlPanel
from .delivery_info import DeliveryInfoWidget
from .analytics_dashboard import AnalyticsDashboard

__all__ = [
    'VehicleControlPanel',
    'DeliveryInfoWidget',
    'AnalyticsDashboard',
]