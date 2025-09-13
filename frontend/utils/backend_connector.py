# frontend/utils/backend_connector.py

import requests
import json
from typing import Dict, Any, Tuple, List

class BackendConnector:
    """Connector to communicate with backend and access backend configuration"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):  # CHANGED: 8001 -> 8000
        self.backend_url = backend_url.rstrip('/')
    
    def get_backend_config(self) -> Dict[str, Any]:
        """Get all configuration constants from backend"""
        try:
            response = requests.get(f"{self.backend_url}/api/config")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to get backend config: {e}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Fallback configuration if backend is unavailable"""
        return {
            "DEFAULT_DEPOT_COORDS": [12.8500, 74.9200],
            "DEFAULT_CUSTOMER_COUNT": 5,
            "MAP_CENTER": [20.5937, 78.9629],
            "MAP_ZOOM": 5,
            "DEFAULT_FLEET_CONFIG": {
                "electric_trucks": 2,
                "fuel_trucks": 1, 
                "drones": 3
            },
            "FLEET_CONSTRAINTS": {
                "min_electric_trucks": 0,
                "max_electric_trucks": 50,
                "min_fuel_trucks": 0,
                "max_fuel_trucks": 50,
                "min_drones": 0,
                "max_drones": 100,
                "min_total_vehicles": 1,
                "max_total_vehicles": 200
            },
            "VEHICLE_SPEEDS": {
                "Drone": 60,
                "Electric Truck": 40,
                "Fuel Truck": 35
            },
            "VEHICLE_WEIGHTS": {
                "Drone": [1, 5],
                "Electric Truck": [200, 500],
                "Fuel Truck": [300, 700]
            },
            "VEHICLE_CHARACTERISTICS": {
                "Drone": {
                    "max_range_km": 100,
                    "battery_life_hours": 2,
                    "weather_dependent": True,
                    "color": "#2196F3",
                    "icon": "🚁"
                },
                "Electric Truck": {
                    "max_range_km": 300,
                    "battery_life_hours": 8,
                    "weather_dependent": False,
                    "color": "#4CAF50",
                    "icon": "🔋"
                },
                "Fuel Truck": {
                    "max_range_km": 800,
                    "battery_life_hours": 12,
                    "weather_dependent": False,
                    "color": "#FF9800",
                    "icon": "⛽"
                }
            }
        }

# Global backend connector instance
backend_connector = BackendConnector()

# Get configuration from backend
_backend_config = backend_connector.get_backend_config()

# Import constants from backend
DEFAULT_DEPOT_COORDS = _backend_config.get("DEFAULT_DEPOT_COORDS", [12.8500, 74.9200])
DEFAULT_CUSTOMER_COUNT = _backend_config.get("DEFAULT_CUSTOMER_COUNT", 5)
MAP_CENTER = _backend_config.get("MAP_CENTER", [20.5937, 78.9629])
MAP_ZOOM = _backend_config.get("MAP_ZOOM", 5)
DEFAULT_FLEET_CONFIG = _backend_config.get("DEFAULT_FLEET_CONFIG", {"electric_trucks": 2, "fuel_trucks": 1, "drones": 3})
FLEET_CONSTRAINTS = _backend_config.get("FLEET_CONSTRAINTS", {})
DEFAULT_WAVES = _backend_config.get("DEFAULT_WAVES", [])
PAUSE_BETWEEN_WAVES = _backend_config.get("PAUSE_BETWEEN_WAVES", 3.0)
VEHICLE_SPEEDS = _backend_config.get("VEHICLE_SPEEDS", {})
VEHICLE_WEIGHTS = _backend_config.get("VEHICLE_WEIGHTS", {})
VEHICLE_CHARACTERISTICS = _backend_config.get("VEHICLE_CHARACTERISTICS", {})
MAP_UPDATE_INTERVAL = _backend_config.get("MAP_UPDATE_INTERVAL", 500)
SOUND_UPDATE_INTERVAL = _backend_config.get("SOUND_UPDATE_INTERVAL", 1000)
DELIVERY_DISTANCE_MIN = _backend_config.get("DELIVERY_DISTANCE_MIN", 15)
DELIVERY_DISTANCE_MAX = _backend_config.get("DELIVERY_DISTANCE_MAX", 45)
MAX_CUSTOMERS = _backend_config.get("MAX_CUSTOMERS", 50)
MIN_CUSTOMERS = _backend_config.get("MIN_CUSTOMERS", 1)
CUSTOMER_CONSTRAINTS = _backend_config.get("CUSTOMER_CONSTRAINTS", {})
PERFORMANCE_CONFIG = _backend_config.get("PERFORMANCE_CONFIG", {})

def validate_fleet_config(electric_trucks: int, fuel_trucks: int, drones: int) -> Tuple[bool, List[str]]:
    """Validate fleet configuration against constraints from backend"""
    try:
        response = requests.post(f"{backend_connector.backend_url}/api/validate/fleet", json={
            "electric_trucks": electric_trucks,
            "fuel_trucks": fuel_trucks,
            "drones": drones
        })
        if response.status_code == 200:
            result = response.json()
            return result["is_valid"], result["errors"]
    except requests.RequestException:
        pass
    
    # Fallback validation if backend unavailable
    total_vehicles = electric_trucks + fuel_trucks + drones
    errors = []
    
    constraints = FLEET_CONSTRAINTS
    if electric_trucks < constraints.get("min_electric_trucks", 0) or electric_trucks > constraints.get("max_electric_trucks", 50):
        errors.append(f"Electric trucks must be between {constraints.get('min_electric_trucks', 0)} and {constraints.get('max_electric_trucks', 50)}")
    
    if fuel_trucks < constraints.get("min_fuel_trucks", 0) or fuel_trucks > constraints.get("max_fuel_trucks", 50):
        errors.append(f"Fuel trucks must be between {constraints.get('min_fuel_trucks', 0)} and {constraints.get('max_fuel_trucks', 50)}")
    
    if drones < constraints.get("min_drones", 0) or drones > constraints.get("max_drones", 100):
        errors.append(f"Drones must be between {constraints.get('min_drones', 0)} and {constraints.get('max_drones', 100)}")
    
    if total_vehicles < constraints.get("min_total_vehicles", 1):
        errors.append(f"Total vehicles must be at least {constraints.get('min_total_vehicles', 1)}")
    
    if total_vehicles > constraints.get("max_total_vehicles", 200):
        errors.append(f"Total vehicles cannot exceed {constraints.get('max_total_vehicles', 200)}")
    
    return len(errors) == 0, errors

def validate_customer_count(customer_count: int) -> Tuple[bool, str]:
    """Validate customer count against constraints from backend"""
    try:
        response = requests.post(f"{backend_connector.backend_url}/api/validate/customers", json={
            "customer_count": customer_count
        })
        if response.status_code == 200:
            result = response.json()
            return result["is_valid"], result["error"]
    except requests.RequestException:
        pass
    
    # Fallback validation if backend unavailable
    constraints = CUSTOMER_CONSTRAINTS
    if customer_count < constraints.get("min_customers", 1) or customer_count > constraints.get("max_customers", 999):
        return False, f"Customer count must be between {constraints.get('min_customers', 1)} and {constraints.get('max_customers', 999)}"
    return True, ""

def get_fleet_summary(electric_trucks: int, fuel_trucks: int, drones: int) -> str:
    """Generate a human-readable fleet summary using backend data"""
    try:
        response = requests.post(f"{backend_connector.backend_url}/api/fleet/summary", json={
            "electric_trucks": electric_trucks,
            "fuel_trucks": fuel_trucks,
            "drones": drones
        })
        if response.status_code == 200:
            return response.json()["summary"]
    except requests.RequestException:
        pass
    
    # Fallback summary if backend unavailable
    total_vehicles = electric_trucks + fuel_trucks + drones
    
    summary = f"Fleet Configuration: {total_vehicles} Total Vehicles\n"
    summary += f"  • Electric Trucks: {electric_trucks} ({VEHICLE_CHARACTERISTICS.get('Electric Truck', {}).get('icon', '🔋')})\n"
    summary += f"  • Fuel Trucks: {fuel_trucks} ({VEHICLE_CHARACTERISTICS.get('Fuel Truck', {}).get('icon', '⛽')})\n" 
    summary += f"  • Drones: {drones} ({VEHICLE_CHARACTERISTICS.get('Drone', {}).get('icon', '🚁')})\n"
    
    # Calculate capacity estimates
    daily_deliveries = total_vehicles * 8  # Rough estimate: 8 deliveries per vehicle per day
    coverage_radius = total_vehicles * 5   # Rough estimate: 5km radius per vehicle
    
    summary += f"\nEstimated Capacity:\n"
    summary += f"  • Daily Deliveries: ~{daily_deliveries} packages\n"
    summary += f"  • Coverage Area: ~{coverage_radius}km radius\n"
    
    return summary

# Export key configuration for easy import
__all__ = [
    'DEFAULT_DEPOT_COORDS',
    'DEFAULT_CUSTOMER_COUNT',
    'MAP_CENTER',
    'MAP_ZOOM',
    'DEFAULT_FLEET_CONFIG',
    'FLEET_CONSTRAINTS',
    'VEHICLE_SPEEDS',
    'VEHICLE_WEIGHTS',
    'VEHICLE_CHARACTERISTICS',
    'validate_fleet_config',
    'validate_customer_count',
    'get_fleet_summary',
    'backend_connector'
]