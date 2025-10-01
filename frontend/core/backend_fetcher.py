"""
Backend data fetcher - retrieves wave assignments from FastAPI backend
"""
import aiohttp
import json
from typing import Dict, List, Optional

class BackendDataFetcher:
    """Fetches wave assignment data from backend API"""
    
    def __init__(self, backend_url: str = "http://127.0.0.1:8000"):
        self.backend_url = backend_url
    
    async def fetch_wave_assignments(self) -> Optional[Dict]:
        """Fetch complete wave assignments from backend"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/wave_assignments") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Fetched wave data: {len(data.get('summary', {}).get('total_waves', 0))} waves")
                        return data
                    else:
                        print(f"❌ Failed to fetch wave data: {response.status}")
                        return None
        except Exception as e:
            print(f"❌ Error fetching wave data: {e}")
            return None
    
    def parse_wave_data(self, wave_data: Dict) -> Dict[str, List[Dict]]:
        """Parse wave data into frontend-compatible format"""
        parsed_waves = {}
        
        if not wave_data:
            return parsed_waves
        
        # Extract each wave
        for wave_key in wave_data.keys():
            if wave_key.startswith("wave_"):
                wave_num = wave_key
                wave_info = wave_data[wave_key]
                
                vehicles = []
                
                # Parse drones
                for drone in wave_info.get("drones", []):
                    vehicles.append({
                        "vehicle_id": drone["vehicle_id"],
                        "type": "Drone",
                        "node_ids": drone["node_ids"],
                        "route": drone["route"],
                        "distance": drone["distance"],
                        "cost": drone["cost"],
                        "weight": drone["total_weight"],
                        "volume": drone["total_volume"]
                    })
                
                # Parse trucks
                for truck in wave_info.get("trucks", []):
                    # Determine truck type from vehicle_id
                    if truck["vehicle_id"].startswith("E_"):
                        truck_type = "Electric Truck"
                    elif truck["vehicle_id"].startswith("F_"):
                        truck_type = "Fuel Truck"
                    else:
                        truck_type = "Electric Truck"  # default
                    
                    vehicles.append({
                        "vehicle_id": truck["vehicle_id"],
                        "type": truck_type,
                        "node_ids": truck["node_ids"],
                        "route": truck["route"],
                        "distance": truck["distance"],
                        "cost": truck["cost"],
                        "weight": truck["total_weight"],
                        "volume": truck["total_volume"],
                        "capacity_utilization": truck.get("capacity_utilization", {})
                    })
                
                parsed_waves[wave_num] = vehicles
        
        return parsed_waves