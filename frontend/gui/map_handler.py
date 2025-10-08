"""
Map handling module
Manages all map-related operations and JavaScript communication
"""
import os
import json
from PyQt5.QtCore import QUrl, QTimer


class MapHandler:
    """Handles map display and updates"""
    
    def __init__(self, map_view, html_template):
        self.map_view = map_view
        self.html_template = html_template
        self.map_ready = False
        self.map_path = None
        self.pending_map_update = False
        
    def create_map_file(self):
        """Create HTML map file"""
        try:
            self.map_path = os.path.abspath("map.html")
            with open(self.map_path, "w", encoding="utf-8") as f:
                f.write(self.html_template)
            self.map_view.setUrl(QUrl.fromLocalFile(self.map_path))
        except Exception as e:
            print(f"Error creating map file: {e}")
    
    def initialize_map(self, depot_coords, delivery_points, no_fly_zones, 
                      map_center, map_zoom):
        """Initialize map with basic data"""
        if not self.map_ready:
            return
        
        suggested_locations = [
            {'name': 'Outskirts of Bangalore', 'coords': [13.0500, 77.7500], 
             'description': 'Good connectivity'},
            {'name': 'Chennai Surroundings', 'coords': [12.8500, 80.0500], 
             'description': 'Industrial area'},
            {'name': 'Mumbai Suburbs', 'coords': [19.2000, 72.9500], 
             'description': 'Outside nuclear facility zone'},
            {'name': 'Delhi NCR Edge', 'coords': [28.4000, 77.3000], 
             'description': 'Away from airport'},
            {'name': 'Hyderabad Outskirts', 'coords': [17.1000, 78.6000], 
             'description': 'Developing logistics hub'},
            {'name': 'Pune Industrial Area', 'coords': [18.4000, 73.7000], 
             'description': 'Away from air force station'}
        ]
        
        basic_data = {
            "center": map_center,
            "zoom": map_zoom,
            "depot": depot_coords,
            "deliveries": delivery_points,
            "total_deliveries": len(delivery_points),
            "cities": [
                {'name': 'New Delhi', 'coords': [28.6139, 77.2090]},
                {'name': 'Mumbai', 'coords': [19.0760, 72.8777]},
                {'name': 'Bangalore', 'coords': [12.9716, 77.5946]},
                {'name': 'Chennai', 'coords': [13.0827, 80.2707]},
                {'name': 'Kolkata', 'coords': [22.5726, 88.3639]},
                {'name': 'Hyderabad', 'coords': [17.3850, 78.4867]},
                {'name': 'Pune', 'coords': [18.5204, 73.8567]},
                {'name': 'Ahmedabad', 'coords': [23.0225, 72.5714]}
            ],
            "nfzones": no_fly_zones,
            "suggested": suggested_locations
        }
        
        js_code = f"""
        console.log('Initializing map with {len(delivery_points)} delivery points...');
        if (typeof window.initializeOptimizedMap === 'function') {{
            window.initializeOptimizedMap({json.dumps(basic_data)});
        }} else if (typeof window.initializeMap === 'function') {{
            window.initializeMap({json.dumps(basic_data)});
        }}
        """
        
        self._run_js_code(js_code)
        print(f"✅ Map initialized with {len(delivery_points)} delivery points")
    
    def update_map_configuration(self, depot_coords, delivery_points):
        """Update map with new depot/delivery configuration"""
        if not self.map_ready:
            return
        
        essential_data = {
            "depot": depot_coords,
            "deliveries": delivery_points,
            "total_deliveries": len(delivery_points)
        }
        
        js_code = f"""
        console.log('Updating map configuration...');
        if (typeof window.updateMapConfiguration === 'function') {{
            window.updateMapConfiguration({json.dumps(essential_data)});
        }}
        """
        
        self._run_js_code(js_code)
    
    def send_vehicles_to_map_batch(self, vehicles_dict, batch_size=12):
        """Send vehicle data in batches"""
        if not self.map_ready:
            return
        
        vehicle_list = list(vehicles_dict.items())
        
        for i in range(0, len(vehicle_list), batch_size):
            batch = vehicle_list[i:i + batch_size]
            
            vehicle_data = {
                "vehicles": [
                    {
                        "name": name,
                        "type": v["type"],
                        "pos": v["pos"],
                        "route": v["route"][:25],  # Limit for performance
                        "speed": v["speed"],
                        "weight": v["weight"],
                        "volume": v.get("volume", "N/A"),
                        "delivery_count": len(v.get("all_deliveries", []))
                    }
                    for name, v in batch
                ],
                "is_batch": True,
                "batch_index": i // batch_size
            }
            
            js_code = f"window.addVehicleBatch && window.addVehicleBatch({json.dumps(vehicle_data)});"
            self._run_js_code(js_code)
    
    def update_vehicle_positions(self, vehicles_dict, paused=False):
        """Update vehicle positions on map"""
        if not self.map_ready or not vehicles_dict:
            return
        
        position_data = {
            "position_updates": [
                {
                    "name": name,
                    "pos": v["pos"],
                    "speed": v["speed"] if not paused else 0
                }
                for name, v in vehicles_dict.items()
            ]
        }
        
        js_code = f"window.updateVehiclePositionsOptimized && window.updateVehiclePositionsOptimized({json.dumps(position_data)});"
        self._run_js_code(js_code)
    
    def clear_all_vehicles(self):
        """Clear all vehicles from map"""
        if not self.map_ready:
            return
        
        js_code = "window.clearAllVehicles && window.clearAllVehicles();"
        self._run_js_code(js_code)
    
    def toggle_no_fly_zones(self, show):
        """Toggle no-fly zones visibility"""
        if not self.map_ready:
            return
        
        js_code = f"window.toggleNoFlyZonesOptimized && window.toggleNoFlyZonesOptimized({str(show).lower()});"
        self._run_js_code(js_code)
    
    def toggle_vehicles(self, show):
        """Toggle vehicles visibility"""
        if not self.map_ready:
            return
        
        js_code = f"window.toggleVehiclesOptimized && window.toggleVehiclesOptimized({str(show).lower()});"
        self._run_js_code(js_code)
    
    def _run_js_code(self, js_code):
        """Safely run JavaScript code on map"""
        try:
            self.map_view.page().runJavaScript(js_code)
        except Exception as e:
            print(f"Error running JS code: {e}")
    
    def cleanup(self):
        """Clean up map file on exit"""
        try:
            if self.map_path and os.path.exists(self.map_path):
                os.remove(self.map_path)
                print(f"Cleaned up map file: {self.map_path}")
        except Exception as e:
            print(f"Warning: Could not clean up map file: {e}")