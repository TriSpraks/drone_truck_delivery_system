import asyncio
import threading
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Global flag to track initialization status
initialization_complete = False
initialization_in_progress = True

def run_heavy_initialization():
    """Run heavy initialization tasks in background thread"""
    global initialization_complete, initialization_in_progress
    
    print("Starting background initialization...")
    start_time = time.time()
    
    try:
        # Your existing heavy initialization code here
        print("Initializing database...")
        # database_init()  # Your database initialization
        time.sleep(0.27)  # Simulating database init time
        print("Database initialized successfully.")
        print(f"Database initialized in 0.27 sec")
        
        print("Generating nodes...")
        # generate_nodes()  # Your node generation
        time.sleep(1.83)  # Simulating node generation time
        print("Frontend: 51 nodes inserted into DB.")
        print(f"Nodes generated in 1.83 sec")
        
        print("Computing distances...")
        print("Calculating distances for 51 nodes...")
        # compute_distances()  # Your distance computation
        time.sleep(1.40)  # Simulating distance computation time
        print("Backend: all distances computed successfully.")
        print("🔎 Debug CSV written: data/distances_debug.csv")
        print(f"Distances computed in 1.40 sec")
        
        print("Generating vehicle matrix...")
        print("Building vehicle matrix...")
        # generate_vehicle_matrix()  # Your vehicle matrix generation
        time.sleep(0.84)  # Simulating vehicle matrix generation time
        print("Vehicle matrix inserted into DB successfully (2454 entries).")
        print(f"Vehicle matrix generated in 0.84 sec")
        
        total_time = time.time() - start_time
        print(f"Background initialization completed in {total_time:.2f} sec")
        
        initialization_complete = True
        initialization_in_progress = False
        
    except Exception as e:
        print(f"Error during background initialization: {e}")
        initialization_in_progress = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""
    # Startup
    print("FastAPI starting up...")
    
    # Start heavy initialization in background thread
    init_thread = threading.Thread(target=run_heavy_initialization, daemon=True)
    init_thread.start()
    
    print("Server ready to accept requests!")
    yield
    
    # Shutdown
    print("INFO:     Shutting down")
    print("INFO:     Waiting for application shutdown.")
    print("Closing DB client...")
    # close_db_client()  # Your cleanup code
    print("DB client closed in 0.00 sec")
    print("Shutdown completed.")

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/config")
async def get_config():
    """Return configuration - available immediately even during initialization"""
    
    # Basic config that's always available
    config = {
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
        },
        "MAP_UPDATE_INTERVAL": 500,
        "SOUND_UPDATE_INTERVAL": 1000,
        "DELIVERY_DISTANCE_MIN": 15,
        "DELIVERY_DISTANCE_MAX": 45,
        "MAX_CUSTOMERS": 50,
        "MIN_CUSTOMERS": 1,
        "CUSTOMER_CONSTRAINTS": {
            "min_customers": 1,
            "max_customers": 999
        },
        "PERFORMANCE_CONFIG": {},
        # Add status info
        "initialization_status": {
            "complete": initialization_complete,
            "in_progress": initialization_in_progress
        }
    }
    
    return config

@app.get("/api/status")
async def get_status():
    """Check initialization status"""
    return {
        "initialization_complete": initialization_complete,
        "initialization_in_progress": initialization_in_progress,
        "ready_for_heavy_operations": initialization_complete
    }

@app.post("/api/validate/fleet")
async def validate_fleet(fleet_data: dict):
    """Validate fleet configuration"""
    electric_trucks = fleet_data.get("electric_trucks", 0)
    fuel_trucks = fleet_data.get("fuel_trucks", 0)
    drones = fleet_data.get("drones", 0)
    total_vehicles = electric_trucks + fuel_trucks + drones
    
    errors = []
    
    # Basic validation (always available)
    if electric_trucks < 0 or electric_trucks > 50:
        errors.append("Electric trucks must be between 0 and 50")
    if fuel_trucks < 0 or fuel_trucks > 50:
        errors.append("Fuel trucks must be between 0 and 50")
    if drones < 0 or drones > 100:
        errors.append("Drones must be between 0 and 100")
    if total_vehicles < 1:
        errors.append("Total vehicles must be at least 1")
    if total_vehicles > 200:
        errors.append("Total vehicles cannot exceed 200")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }

@app.post("/api/validate/customers")
async def validate_customers(customer_data: dict):
    """Validate customer count"""
    customer_count = customer_data.get("customer_count", 0)
    
    if customer_count < 1 or customer_count > 999:
        return {
            "is_valid": False,
            "error": "Customer count must be between 1 and 999"
        }
    
    return {
        "is_valid": True,
        "error": ""
    }

@app.post("/api/fleet/summary")
async def get_fleet_summary(fleet_data: dict):
    """Generate fleet summary"""
    electric_trucks = fleet_data.get("electric_trucks", 0)
    fuel_trucks = fleet_data.get("fuel_trucks", 0)
    drones = fleet_data.get("drones", 0)
    total_vehicles = electric_trucks + fuel_trucks + drones
    
    summary = f"Fleet Configuration: {total_vehicles} Total Vehicles\n"
    summary += f"  • Electric Trucks: {electric_trucks} (🔋)\n"
    summary += f"  • Fuel Trucks: {fuel_trucks} (⛽)\n" 
    summary += f"  • Drones: {drones} (🚁)\n"
    
    # Calculate capacity estimates
    daily_deliveries = total_vehicles * 8
    coverage_radius = total_vehicles * 5
    
    summary += f"\nEstimated Capacity:\n"
    summary += f"  • Daily Deliveries: ~{daily_deliveries} packages\n"
    summary += f"  • Coverage Area: ~{coverage_radius}km radius\n"
    
    if not initialization_complete:
        summary += f"\n⚠️  Note: Background optimization still in progress...\n"
    
    return {"summary": summary}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)