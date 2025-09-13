#!/usr/bin/env python3
# simple_api_server.py - Run this alongside your existing backend
# This provides ONLY the /api/config endpoint your frontend needs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create a simple API server
app = FastAPI(title="API Config Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/config")
async def get_config():
    """Return the exact configuration your frontend expects"""
    return {
        "status": "active",
        "depot_location": {
            "latitude": 20.138470,
            "longitude": 78.881836
        },
        "customers": 5,
        "fleet_configuration": {
            "electric_trucks": 2,
            "fuel_trucks": 1, 
            "drones": 3,
            "total_vehicles": 6
        },
        "fleet_constraints": {
            "min_electric_trucks": 0,
            "max_electric_trucks": 50,
            "min_fuel_trucks": 0,
            "max_fuel_trucks": 50,
            "min_drones": 0,
            "max_drones": 100,
            "min_total_vehicles": 1,
            "max_total_vehicles": 200
        },
        "customer_constraints": {
            "min_customers": 1,
            "max_customers": 999,
            "default_customers": 5
        },
        "vehicle_speeds": {
            "Drone": 60,
            "Electric Truck": 40,
            "Fuel Truck": 35
        },
        "vehicle_characteristics": {
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
        "map_settings": {
            "center": [20.5937, 78.9629],
            "zoom": 5,
            "update_interval": 500
        },
        "delivery_settings": {
            "distance_min": 15,
            "distance_max": 45,
            "max_customers": 50,
            "min_customers": 1
        },
        "performance_config": {
            "max_route_points": 100,
            "update_frequency_ms": 500,
            "max_concurrent_vehicles": 200
        }
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Configuration API Server",
        "purpose": "Provides /api/config endpoint for frontend"
    }

@app.get("/")
async def root():
    return {
        "message": "Configuration API Server Running",
        "endpoints": ["/api/config", "/api/health"],
        "purpose": "Companion to main backend for frontend configuration"
    }

if __name__ == "__main__":
    print("🔧 Starting Configuration API Server...")
    print("📍 This server provides ONLY the /api/config endpoint")
    print("🔗 Run this ALONGSIDE your existing backend (not instead of it)")
    print("🌐 Frontend will connect to http://localhost:8001/api/config")
    print("📊 Your main backend continues running on port 8000")
    print()
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
        print("✅ API Server started successfully on http://127.0.0.1:8001")
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        print("💡 Try using a different port if 8001 is busy")