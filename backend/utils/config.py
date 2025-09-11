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
