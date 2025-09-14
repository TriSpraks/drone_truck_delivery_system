# config.py

# ─────────────────────────────── 
# General Simulation Settings 
# ─────────────────────────────── 
SEED = 42

# ─────────────────────────────── 
# Node Generation 
# ─────────────────────────────── 
NUM_CUSTOMERS = 50  # number of customer nodes

# Depot Coordinates (Mangaluru region) 
DEPOT_COORDS = (74.8421, 12.8698)

# Customer Location Ranges 
LAT_RANGE = (12.85, 12.95) 
LON_RANGE = (74.8, 74.9) 
ELEV_RANGE = (10, 150)  # meters

# Node Generation 
WEIGHT_MEAN = 2.0   # kg 
WEIGHT_STDDEV = 1.5 
VOLUME_MEAN = 50000   # cm³ 
VOLUME_STDDEV = 20000    

TRUCK_SPEED = 50.0  # km/h

# ─────────────────────────────── 
# Total cost weights 
# ─────────────────────────────── 
ALPHA = 1.0  # distance 
BETA = 1.0   # normalized energy 
GAMMA = 1.0  # normalized emissions

# ─────────────────────────────── 
# Fuel Truck (Tata 1212 Diesel) 
# ─────────────────────────────── 
FUEL_TRUCK_KM_PER_LITER = 6.0 
FUEL_TRUCK_PAYLOAD_KG = 6900.0 
FUEL_TRUCK_PAYLOAD_CM3 = 27_000_000 
FUEL_TRUCK_SPEED = 50.0 
FUEL_PRICE = 90.0 
DIESEL_CO2 = 2.68 
FUEL_TRUCK_CO2_PER_KM = DIESEL_CO2 / FUEL_TRUCK_KM_PER_LITER

# ─────────────────────────────── 
# Grid Emission Factor 
# ─────────────────────────────── 
GRID_CO2 = 0.7  # kg CO₂ per kWh

# ─────────────────────────────── 
# Electric Truck (Tata 1212 EV) 
# ─────────────────────────────── 
ELECTRIC_TRUCK_BATTERY_KWH = 92.0 
ELECTRIC_TRUCK_RANGE_KM = 150.0 
ELECTRIC_TRUCK_PAYLOAD_KG = 6900.0 
ELECTRIC_TRUCK_PAYLOAD_CM3 = 27_000_000 
ELECTRIC_TRUCK_SPEED = 50.0 
ELECTRICITY_PRICE = 6.0 
ELECTRIC_TRUCK_CO2_PER_KM = ELECTRIC_TRUCK_BATTERY_KWH / ELECTRIC_TRUCK_RANGE_KM * GRID_CO2

# ─────────────────────────────── 
# Drone (Small-category) 
# ─────────────────────────────── 
DRONE_SPEED = 60.0 
DRONE_MAX_RANGE = 30.0 
DRONE_PAYLOAD_KG = 3.0 
DRONE_PAYLOAD_CM3 = 20_000 
DRONE_KWH_PER_KM = 0.35 
DRONE_CO2_PER_KM = 0.28

# Drone/Truck config objects 
Drone = type("DroneConfig", (), {     
    "SPEED_KMPH": DRONE_SPEED,     
    "MAX_RANGE_KM": DRONE_MAX_RANGE,     
    "PAYLOAD_KG": DRONE_PAYLOAD_KG,     
    "PAYLOAD_CM3": DRONE_PAYLOAD_CM3,     
    "KWH_PER_KM": DRONE_KWH_PER_KM,     
    "CO2_PER_KM": DRONE_CO2_PER_KM * GRID_CO2 
})

# ─────────────────────────────── 
# OpenRouteService (Truck routing API) 
# ─────────────────────────────── 
import os 
from dotenv import load_dotenv 
load_dotenv() 
ORS_API_KEY = os.getenv("ORS_API_KEY") 
MAX_BATCH = 25 
MAX_WORKERS = 10

# ─────────────────────────────── 
# Database (Turso Cloud SQLite) 
# ─────────────────────────────── 
DB_URL = os.getenv("TURSO_DATABASE_URL") 
DB_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

# ═══════════════════════════════════════════════════════════════════════════
# FRONTEND CONFIGURATION CONSTANTS MOVED FROM FRONTEND
# ═══════════════════════════════════════════════════════════════════════════

# Default configuration values
DEFAULT_DEPOT_COORDS = [12.8500, 74.9200]  # Default Mangaluru
DEFAULT_CUSTOMER_COUNT = 5
MAP_CENTER = [20.5937, 78.9629]  # Center of India
MAP_ZOOM = 5  # Zoom level to show entire India

# Enhanced fleet configuration with more granular control
DEFAULT_FLEET_CONFIG = {
    "electric_trucks": 2,
    "fuel_trucks": 1, 
    "drones": 3
}

# Fleet constraints and validation
FLEET_CONSTRAINTS = {
    "min_electric_trucks": 0,
    "max_electric_trucks": 50,
    "min_fuel_trucks": 0,
    "max_fuel_trucks": 50,
    "min_drones": 0,
    "max_drones": 100,
    "min_total_vehicles": 1,
    "max_total_vehicles": 200
}

# Legacy waves configuration (kept for backward compatibility)
DEFAULT_WAVES = [
    {"num_drones": 3, "num_electric_trucks": 10, "num_fuel_trucks": 2},
    {"num_drones": 2, "num_electric_trucks": 4, "num_fuel_trucks": 1},
]

PAUSE_BETWEEN_WAVES = 3.0

# Vehicle speeds (km/h) - optimized for delivery operations
VEHICLE_SPEEDS = {
    "Drone": 60,           # Fast air delivery
    "Electric Truck": 40,  # Urban delivery speed
    "Fuel Truck": 35       # Heavier, slower trucks
}

# Vehicle weight ranges (kg) - realistic payload capacities
VEHICLE_WEIGHTS = {
    "Drone": (1, 5),              # Light packages only
    "Electric Truck": (200, 500),  # Medium cargo capacity
    "Fuel Truck": (300, 700)      # Heavy cargo capacity
}

# Vehicle operational characteristics
VEHICLE_CHARACTERISTICS = {
    "Drone": {
        "max_range_km": 100,        # Flight range before return
        "battery_life_hours": 2,    # Operating time
        "weather_dependent": True,   # Affected by weather
        "color": "#2196F3",         # Blue for drones
        "icon": "🚁"
    },
    "Electric Truck": {
        "max_range_km": 300,        # Range on full charge
        "battery_life_hours": 8,    # Work shift duration
        "weather_dependent": False,  # All-weather operation
        "color": "#4CAF50",         # Green for electric
        "icon": "🔋"
    },
    "Fuel Truck": {
        "max_range_km": 800,        # Long range capability
        "battery_life_hours": 12,   # Extended operation
        "weather_dependent": False,  # All-weather operation
        "color": "#FF9800",         # Orange for fuel
        "icon": "⛽"
    }
}

# Map settings
MAP_UPDATE_INTERVAL = 500  # milliseconds
SOUND_UPDATE_INTERVAL = 1000  # milliseconds

# Delivery point generation settings
DELIVERY_DISTANCE_MIN = 15  # km
DELIVERY_DISTANCE_MAX = 45  # km
MAX_CUSTOMERS = 50          # Increased for scalability
MIN_CUSTOMERS = 1

# Customer and delivery constraints
CUSTOMER_CONSTRAINTS = {
    "min_customers": 1,
    "max_customers": 999,       # Support large operations
    "default_customers": 5
}

# Performance and optimization settings
PERFORMANCE_CONFIG = {
    "max_route_points": 100,    # Limit route complexity for performance
    "update_frequency_ms": 500, # UI update interval
    "max_concurrent_vehicles": 200  # System limit
}

# Validation functions
def validate_fleet_config(electric_trucks, fuel_trucks, drones):
    """Validate fleet configuration against constraints"""
    total_vehicles = electric_trucks + fuel_trucks + drones
    
    errors = []
    
    # Check individual vehicle type limits
    if electric_trucks < FLEET_CONSTRAINTS["min_electric_trucks"] or electric_trucks > FLEET_CONSTRAINTS["max_electric_trucks"]:
        errors.append(f"Electric trucks must be between {FLEET_CONSTRAINTS['min_electric_trucks']} and {FLEET_CONSTRAINTS['max_electric_trucks']}")
    
    if fuel_trucks < FLEET_CONSTRAINTS["min_fuel_trucks"] or fuel_trucks > FLEET_CONSTRAINTS["max_fuel_trucks"]:
        errors.append(f"Fuel trucks must be between {FLEET_CONSTRAINTS['min_fuel_trucks']} and {FLEET_CONSTRAINTS['max_fuel_trucks']}")
    
    if drones < FLEET_CONSTRAINTS["min_drones"] or drones > FLEET_CONSTRAINTS["max_drones"]:
        errors.append(f"Drones must be between {FLEET_CONSTRAINTS['min_drones']} and {FLEET_CONSTRAINTS['max_drones']}")
    
    # Check total vehicle limits
    if total_vehicles < FLEET_CONSTRAINTS["min_total_vehicles"]:
        errors.append(f"Total vehicles must be at least {FLEET_CONSTRAINTS['min_total_vehicles']}")
    
    if total_vehicles > FLEET_CONSTRAINTS["max_total_vehicles"]:
        errors.append(f"Total vehicles cannot exceed {FLEET_CONSTRAINTS['max_total_vehicles']}")
    
    return len(errors) == 0, errors

def validate_customer_count(customer_count):
    """Validate customer count against constraints"""
    if customer_count < CUSTOMER_CONSTRAINTS["min_customers"] or customer_count > CUSTOMER_CONSTRAINTS["max_customers"]:
        return False, f"Customer count must be between {CUSTOMER_CONSTRAINTS['min_customers']} and {CUSTOMER_CONSTRAINTS['max_customers']}"
    return True, ""

def get_fleet_summary(electric_trucks, fuel_trucks, drones):
    """Generate a human-readable fleet summary"""
    total_vehicles = electric_trucks + fuel_trucks + drones
    
    summary = f"Fleet Configuration: {total_vehicles} Total Vehicles\n"
    summary += f"  • Electric Trucks: {electric_trucks} ({VEHICLE_CHARACTERISTICS['Electric Truck']['icon']})\n"
    summary += f"  • Fuel Trucks: {fuel_trucks} ({VEHICLE_CHARACTERISTICS['Fuel Truck']['icon']})\n" 
    summary += f"  • Drones: {drones} ({VEHICLE_CHARACTERISTICS['Drone']['icon']})\n"
    
    # Calculate capacity estimates
    daily_deliveries = total_vehicles * 8  # Rough estimate: 8 deliveries per vehicle per day
    coverage_radius = total_vehicles * 5   # Rough estimate: 5km radius per vehicle
    
    summary += f"\nEstimated Capacity:\n"
    summary += f"  • Daily Deliveries: ~{daily_deliveries} packages\n"
    summary += f"  • Coverage Area: ~{coverage_radius}km radius\n"
    
    return summary