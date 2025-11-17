# config.py

# ─────────────────────────────── 
# General Simulation Settings 
# ─────────────────────────────── 
SEED = 42  # Random seed to reproduce results

# ─────────────────────────────── 
# Node Generation 
# ─────────────────────────────── 
NUM_CUSTOMERS = 50  # number of customer nodes

# Depot Coordinates (Mangaluru region, with elevation ~20m)
DEPOT_COORDS = (74.8421, 12.8698, 20)

# Customer Location Ranges 
LAT_RANGE = (12.85, 12.95) 
LON_RANGE = (74.8, 74.9) 
ELEV_RANGE = (10, 150)  # meters

# Node Generation 
WEIGHT_MEAN = 2.0   # kg 
WEIGHT_STDDEV = 1.5 
VOLUME_MEAN = 50000   # cm³ 
VOLUME_STDDEV = 20000    

TRUCK_SPEED = 96.0  # km/h (≈60 mph from general truck spec)

# ─────────────────────────────── 
# Total cost weights (from provided α, β, γ) 
# ─────────────────────────────── 
ALPHA = 0.430  # delivery speed weight
BETA = 0.259   # noise score weight
GAMMA = 0.311  # CO₂ score weight

# ─────────────────────────────── 
# Fuel Truck (Tata LPT 1212 Diesel) 
# ─────────────────────────────── 
FUEL_TRUCK_NAME = "TATA LPT 1212"
FUEL_TRUCK_GVW = 11990.0  # kg
FUEL_TRUCK_PAYLOAD_KG = 7500.0
FUEL_TRUCK_PAYLOAD_CM3 = 27_000_000  # unchanged (approx cargo volume)
FUEL_TRUCK_SPEED = 96.0  # km/h (≈60 mph)
FUEL_TRUCK_ENGINE_LITERS = 3.3
FUEL_TRUCK_GEARS = "5F+1R"
FUEL_TRUCK_EMISSION_STANDARD = "BS VI"

# Fuel consumption and cost
FUEL_TRUCK_L_PER_100KM = 16.7
FUEL_TRUCK_KM_PER_LITER = 100.0 / FUEL_TRUCK_L_PER_100KM  # ≈5.99 km/L
FUEL_PRICE = 91.63  # ₹/liter (Mangalore, Sept 2025)

# CO₂ factors
DIESEL_CO2_TTW = 2.68  # kg CO₂ per liter (tank-to-wheel combustion)
DIESEL_CO2_WTT = 0.73  # kg CO₂e per liter (well-to-tank)
DIESEL_CO2_WTW = DIESEL_CO2_TTW + 0.73  # ≈3.41 kg CO₂e per liter
FUEL_TRUCK_CO2_PER_KM = DIESEL_CO2_WTW / FUEL_TRUCK_KM_PER_LITER
DIESEL_CO2 = DIESEL_CO2_TTW

# ─────────────────────────────── 
# Grid Emission Factor 
# ─────────────────────────────── 
GRID_CO2 = 0.727  # kg CO₂ per kWh (India, 2025)

# ─────────────────────────────── 
# Electric Truck (Tata LPT 1212 EV) 
# ─────────────────────────────── 
ELECTRIC_TRUCK_NAME = "TATA LPT 1212 EV"
ELECTRIC_TRUCK_GVW = 11990.0
ELECTRIC_TRUCK_PAYLOAD_KG = 6900.0
ELECTRIC_TRUCK_PAYLOAD_CM3 = 27_000_000
ELECTRIC_TRUCK_SPEED = 96.0  # km/h (≈60 mph)
ELECTRIC_TRUCK_BATTERY_KWH = 92.0
ELECTRIC_TRUCK_RANGE_KM = 150.0
ELECTRIC_TRUCK_KWH_PER_KM = 0.39
ELECTRICITY_PRICE = 9.23  # ₹ per kWh (Mangaluru, Jan 2025)
ELECTRIC_TRUCK_CO2_PER_KM = ELECTRIC_TRUCK_KWH_PER_KM * GRID_CO2

# ─────────────────────────────── 
# Drone (MD4-3000 Small-category) 
# ─────────────────────────────── 
DRONE_NAME = "MD4-3000"
DRONE_TYPE = "Small"
DRONE_SPEED = 96.0  # km/h (≈60 mph)
DRONE_MAX_RANGE = 36.0
DRONE_PAYLOAD_KG = 5.0
DRONE_PAYLOAD_CM3 = 20_000
DRONE_BATTERY_WH = 777.0
DRONE_KWH_PER_KM = 0.0215  # 21.5 Wh/km
DRONE_CO2_PER_KM = DRONE_KWH_PER_KM * GRID_CO2

# Drone/Truck config objects 
Drone = type("DroneConfig", (), {     
    "SPEED_KMPH": DRONE_SPEED,     
    "MAX_RANGE_KM": DRONE_MAX_RANGE,     
    "PAYLOAD_KG": DRONE_PAYLOAD_KG,     
    "PAYLOAD_CM3": DRONE_PAYLOAD_CM3,     
    "KWH_PER_KM": DRONE_KWH_PER_KM,     
    "CO2_PER_KM": DRONE_CO2_PER_KM 
})

# ─────────────────────────────── 
# Noise Levels (dB) 
# ─────────────────────────────── 
NOISE_LEVELS = {
    "Fuel Truck": 80,
    "Electric Truck": 70,
    "Drone": 90,
}

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
# FRONTEND CONFIGURATION CONSTANTS (unchanged except values) 
# ═══════════════════════════════════════════════════════════════════════════

# Default configuration values
DEFAULT_DEPOT_COORDS = [12.8500, 74.9200, 20]  # Default Mangaluru with elevation
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

# Vehicle speeds (km/h)
VEHICLE_SPEEDS = {
    "Drone": DRONE_SPEED,
    "Electric Truck": ELECTRIC_TRUCK_SPEED,
    "Fuel Truck": FUEL_TRUCK_SPEED,
}

# Vehicle weight ranges (kg)
VEHICLE_WEIGHTS = {
    "Drone": (1, 5),
    "Electric Truck": (200, 500),
    "Fuel Truck": (300, 700)
}

# Vehicle operational characteristics
VEHICLE_CHARACTERISTICS = {
    "Drone": {
        "max_range_km": DRONE_MAX_RANGE,
        "battery_life_hours": 3,   # Drone lifetime ~3 years
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

# Map settings
MAP_UPDATE_INTERVAL = 500  # milliseconds
SOUND_UPDATE_INTERVAL = 1000  # milliseconds

# Delivery point generation settings
DELIVERY_DISTANCE_MIN = 15  # km
DELIVERY_DISTANCE_MAX = 45  # km
MAX_CUSTOMERS = 50
MIN_CUSTOMERS = 1

# Customer and delivery constraints
CUSTOMER_CONSTRAINTS = {
    "min_customers": 1,
    "max_customers": 999,
    "default_customers": 5
}

# Performance and optimization settings
PERFORMANCE_CONFIG = {
    "max_route_points": 100,
    "update_frequency_ms": 500,
    "max_concurrent_vehicles": 200
}

# Validation functions
def validate_fleet_config(electric_trucks, fuel_trucks, drones):
    """Validate fleet configuration against constraints"""
    total_vehicles = electric_trucks + fuel_trucks + drones
    
    errors = []
    
    if electric_trucks < FLEET_CONSTRAINTS["min_electric_trucks"] or electric_trucks > FLEET_CONSTRAINTS["max_electric_trucks"]:
        errors.append(f"Electric trucks must be between {FLEET_CONSTRAINTS['min_electric_trucks']} and {FLEET_CONSTRAINTS['max_electric_trucks']}")
    
    if fuel_trucks < FLEET_CONSTRAINTS["min_fuel_trucks"] or fuel_trucks > FLEET_CONSTRAINTS["max_fuel_trucks"]:
        errors.append(f"Fuel trucks must be between {FLEET_CONSTRAINTS['min_fuel_trucks']} and {FLEET_CONSTRAINTS['max_fuel_trucks']}")
    
    if drones < FLEET_CONSTRAINTS["min_drones"] or drones > FLEET_CONSTRAINTS["max_drones"]:
        errors.append(f"Drones must be between {FLEET_CONSTRAINTS['min_drones']} and {FLEET_CONSTRAINTS['max_drones']}")
    
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
    
    daily_deliveries = total_vehicles * 8
    coverage_radius = total_vehicles * 5
    
    summary += f"\nEstimated Capacity:\n"
    summary += f"  • Daily Deliveries: ~{daily_deliveries} packages\n"
    summary += f"  • Coverage Area: ~{coverage_radius}km radius\n"
    
    return summary
