"""
Delivery Point Generator Module
Generates delivery points with proper distribution around depot
"""
import math
import random


class DeliveryPointGenerator:
    """Generates delivery points around a depot"""
    
    # Drone capacity limits
    DRONE_MAX_WEIGHT = 5.0
    DRONE_MAX_VOLUME = 20000
    
    # Distance ranges (km)
    INNER_MIN_DISTANCE = 0.5
    INNER_MAX_DISTANCE = 5.0
    OUTER_MIN_DISTANCE = 3.0
    OUTER_MAX_DISTANCE = 60.0
    
    # Distribution percentages
    INNER_PERCENTAGE = 0.1  # 10% inner circle
    DRONE_ELIGIBLE_OUTER = 0.15  # 15% drone-eligible in outer circle
    
    @staticmethod
    def generate_points(depot_coords, customer_count):
        """
        Generate delivery points around depot
        
        Args:
            depot_coords: [lat, lon] of depot
            customer_count: Number of customer points to generate
            
        Returns:
            tuple: (delivery_points, customer_nodes, depot_node)
        """
        depot_lat, depot_lon = depot_coords
        
        # Create depot node
        depot_node = {
            "node_id": "depot",
            "type": "depot",
            "weight": 0,
            "volume": 0,
            "lon": round(depot_lon, 6),
            "lat": round(depot_lat, 6),
            "coords": [round(depot_lat, 6), round(depot_lon, 6)]
        }
        
        # Split into inner and outer circles
        inner_count = max(1, int(customer_count * DeliveryPointGenerator.INNER_PERCENTAGE))
        outer_count = customer_count - inner_count
        
        customer_nodes = []
        
        # Generate inner circle points (drone-eligible)
        customer_nodes.extend(
            DeliveryPointGenerator._generate_inner_points(
                depot_lat, depot_lon, inner_count
            )
        )
        
        # Generate outer circle points (mostly truck)
        customer_nodes.extend(
            DeliveryPointGenerator._generate_outer_points(
                depot_lat, depot_lon, outer_count, len(customer_nodes)
            )
        )
        
        # Sort by node_id for consistency
        customer_nodes.sort(key=lambda x: int(x['node_id'].replace('cust_', '')))
        
        # Extract coordinates
        delivery_points = [node["coords"] for node in customer_nodes]
        
        return delivery_points, customer_nodes, depot_node
    
    @staticmethod
    def _generate_inner_points(depot_lat, depot_lon, count):
        """Generate inner circle points (drone-eligible)"""
        points = []
        
        for i in range(count):
            angle = random.uniform(0, 360)
            distance_km = random.uniform(
                DeliveryPointGenerator.INNER_MIN_DISTANCE,
                DeliveryPointGenerator.INNER_MAX_DISTANCE
            )
            
            lat, lon = DeliveryPointGenerator._calculate_offset(
                depot_lat, depot_lon, distance_km, angle
            )
            
            # Drone-eligible package
            weight = round(
                random.uniform(0.5, DeliveryPointGenerator.DRONE_MAX_WEIGHT), 
                2
            )
            volume = random.randint(500, DeliveryPointGenerator.DRONE_MAX_VOLUME)
            
            points.append({
                "node_id": f"cust_{len(points) + 1}",
                "type": "customer",
                "weight": weight,
                "volume": volume,
                "lon": round(lon, 6),
                "lat": round(lat, 6),
                "coords": [round(lat, 6), round(lon, 6)]
            })
        
        return points
    
    @staticmethod
    def _generate_outer_points(depot_lat, depot_lon, count, start_id):
        """Generate outer circle points (mostly truck)"""
        points = []
        
        for i in range(count):
            angle = random.uniform(0, 360)
            distance_km = random.uniform(
                DeliveryPointGenerator.OUTER_MIN_DISTANCE,
                DeliveryPointGenerator.OUTER_MAX_DISTANCE
            )
            
            lat, lon = DeliveryPointGenerator._calculate_offset(
                depot_lat, depot_lon, distance_km, angle
            )
            
            # 15% chance of drone-eligible, rest truck-only
            if random.random() < DeliveryPointGenerator.DRONE_ELIGIBLE_OUTER:
                # Drone-eligible
                weight = round(
                    random.uniform(0.5, DeliveryPointGenerator.DRONE_MAX_WEIGHT),
                    2
                )
                volume = random.randint(500, DeliveryPointGenerator.DRONE_MAX_VOLUME)
                node_data = {
                    "node_id": f"cust_{start_id + len(points) + 1}",
                    "type": "customer",
                    "weight": weight,
                    "volume": volume,
                    "lon": round(lon, 6),
                    "lat": round(lat, 6),
                    "coords": [round(lat, 6), round(lon, 6)]
                }
            else:
                # Truck-only (heavy/large packages)
                weight = round(random.uniform(100, 1000), 2)
                volume = random.randint(200000, 5400000)
                node_data = {
                    "node_id": f"cust_{start_id + len(points) + 1}",
                    "type": "customer",
                    "weight": weight,
                    "volume": volume,
                    "lon": round(lon, 6),
                    "lat": round(lat, 6),
                    "coords": [round(lat, 6), round(lon, 6)],
                    "eligible": "truck"
                }
            
            points.append(node_data)
        
        return points
    
    @staticmethod
    def _calculate_offset(depot_lat, depot_lon, distance_km, angle_deg):
        """
        Calculate lat/lon offset from depot
        
        Args:
            depot_lat: Depot latitude
            depot_lon: Depot longitude
            distance_km: Distance in kilometers
            angle_deg: Angle in degrees
            
        Returns:
            tuple: (new_lat, new_lon)
        """
        # Convert angle to radians
        angle_rad = math.radians(angle_deg)
        
        # Calculate offsets
        # 1 degree latitude ≈ 111.32 km
        lat_offset = (distance_km / 111.32) * math.cos(angle_rad)
        
        # Longitude offset depends on latitude
        lon_offset = (distance_km / (111.32 * math.cos(math.radians(depot_lat)))) * math.sin(angle_rad)
        
        new_lat = depot_lat + lat_offset
        new_lon = depot_lon + lon_offset
        
        return new_lat, new_lon