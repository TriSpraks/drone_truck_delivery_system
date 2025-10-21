"""
Map builder that displays solution.json data with OSRM routing for trucks
Place this in: frontend/gui/map_builder.py
"""
import folium
from typing import Dict, List, Optional, Tuple
from .route_manager import RouteManager


def build_node_lookup(nodes: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    Convert list of node dicts to lookup: node_id -> {"lat":..., "lon":...}
    """
    lookup = {}
    for n in nodes:
        nid = n.get("node_id") or n.get("id") or n.get("name")
        if not nid:
            continue
        lookup[nid] = {"lat": float(n["lat"]), "lon": float(n["lon"])}
    return lookup


def coords_from_node_ids(node_ids: List[str], nodes_lookup: Dict) -> List[List[float]]:
    """
    Convert node IDs to [lat, lon] coordinates
    """
    coords = []
    for nid in node_ids:
        if nid not in nodes_lookup:
            raise KeyError(f"Missing node: {nid}")
        p = nodes_lookup[nid]
        coords.append([p["lat"], p["lon"]])
    return coords


def build_map_from_solution(
    solution: Dict,
    nodes_lookup: Dict[str, Dict[str, float]],
    backend_center: Optional[Tuple[float, float]] = None,
    tiles: str = "OpenStreetMap"
) -> folium.Map:
    """
    Build folium map from solution.json with:
    - OSRM routing for trucks (real road paths)
    - Straight lines for drones
    - All data from solution.json displayed
    
    Args:
        solution: Parsed solution.json dictionary
        nodes_lookup: node_id -> {lat, lon}
        backend_center: Center coordinates (lat, lon), defaults to depot
        tiles: Map tile type
    
    Returns:
        folium.Map object
    """
    
    # Get map center
    if backend_center:
        center = backend_center
    else:
        depot = nodes_lookup.get("depot") or next(iter(nodes_lookup.values()))
        center = (depot["lat"], depot["lon"])
    
    m = folium.Map(location=center, zoom_start=11, tiles=tiles)
    
    # Add all node markers
    print("Adding node markers...")
    for node_id, coords in nodes_lookup.items():
        if node_id == "depot":
            color = "darkblue"
            icon_symbol = "home"
            size = 10
        else:
            color = "purple"
            icon_symbol = "package"
            size = 6
        
        folium.CircleMarker(
            location=(coords["lat"], coords["lon"]),
            radius=size,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=f"<b>{node_id}</b>",
            tooltip=node_id
        ).add_to(m)
    
    # Process each wave in solution
    print("Processing solution waves...")
    for wave_key, wave_data in solution.items():
        if wave_key == 'summary':
            continue
        
        if not isinstance(wave_data, dict):
            continue
        
        print(f"\nProcessing {wave_key}...")
        
        # ==================== DRONES ====================
        # Drones get straight line routes (no OSRM)
        for drone in wave_data.get('drones', []):
            try:
                route_nodes = drone.get('route', [])
                route_coords = coords_from_node_ids(route_nodes, nodes_lookup)
            except KeyError as e:
                print(f"  Skipping drone {drone.get('vehicle_id')}: {e}")
                continue
            
            vehicle_id = drone.get('vehicle_id', 'Drone')
            distance = drone.get('distance', 0)
            cost = drone.get('cost', 0)
            weight = drone.get('total_weight', 0)
            volume = drone.get('total_volume', 0)
            
            # Create popup with all data
            popup_text = f"""
            <b>{vehicle_id}</b><br>
            Route: {' → '.join(route_nodes)}<br>
            Distance: {distance:.2f} km<br>
            Cost: ${cost:.2f}<br>
            Weight: {weight:.2f} kg<br>
            Volume: {volume:.0f} units
            """
            
            # Draw straight dashed line for drone
            folium.PolyLine(
                locations=route_coords,
                color="red",
                weight=2.5,
                opacity=0.8,
                dash_array="5, 5",
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=vehicle_id
            ).add_to(m)
            
            print(f"  Drone {vehicle_id}: {' → '.join(route_nodes)}")
        
        # ==================== TRUCKS ====================
        # Trucks get OSRM routing (real road paths)
        for truck in wave_data.get('trucks', []):
            try:
                route_nodes = truck.get('route', [])
                waypoint_coords = coords_from_node_ids(route_nodes, nodes_lookup)
            except KeyError as e:
                print(f"  Skipping truck {truck.get('vehicle_id')}: {e}")
                continue
            
            vehicle_id = truck.get('vehicle_id', 'Truck')
            distance = truck.get('distance', 0)
            cost = truck.get('cost', 0)
            weight = truck.get('total_weight', 0)
            volume = truck.get('total_volume', 0)
            capacity = truck.get('capacity_utilization', {})
            
            # Get OSRM route
            print(f"  Getting OSRM route for {vehicle_id}...")
            osrm_route = get_osrm_route_with_fallback(
                waypoint_coords, 
                vehicle_id,
                route_nodes
            )
            
            # Create detailed popup
            cap_weight = capacity.get('weight_percent', 0)
            cap_volume = capacity.get('volume_percent', 0)
            
            popup_text = f"""
            <b>{vehicle_id}</b><br>
            Assigned: {', '.join(route_nodes)}<br>
            Distance: {distance:.2f} km<br>
            Cost: ${cost:.2f}<br>
            Weight: {weight:.2f} kg<br>
            Volume: {volume:.0f} units<br>
            Capacity: {cap_weight:.1f}% weight, {cap_volume:.1f}% volume
            """
            
            # Determine color by truck type
            if 'E_Truck' in vehicle_id or 'Electric' in vehicle_id:
                color = "green"
            else:
                color = "orange"
            
            # Draw OSRM route (solid line)
            folium.PolyLine(
                locations=osrm_route,
                color=color,
                weight=3,
                opacity=0.85,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=vehicle_id
            ).add_to(m)
            
            print(f"  Truck {vehicle_id}: {' → '.join(route_nodes)}")
    
    return m


def get_osrm_route_with_fallback(
    waypoint_coords: List[List[float]], 
    vehicle_id: str,
    node_names: List[str]
) -> List[List[float]]:
    """
    Get OSRM route with fallback to direct segments if OSRM fails
    
    Args:
        waypoint_coords: List of [lat, lon] coordinates
        vehicle_id: Vehicle ID for logging
        node_names: Original node IDs for logging
    
    Returns:
        List of [lat, lon] coordinates representing the route
    """
    
    # Try full route first
    try:
        osrm_route = RouteManager._get_osrm_route_fast(waypoint_coords)
        if osrm_route and len(osrm_route) > 1:
            print(f"    OSRM route successful: {len(osrm_route)} points")
            return osrm_route
    except Exception as e:
        print(f"    OSRM full route failed: {e}")
    
    # Fall back to pairwise segments
    print(f"    Attempting pairwise OSRM segments...")
    concatenated = []
    
    for i in range(len(waypoint_coords) - 1):
        start = waypoint_coords[i]
        end = waypoint_coords[i + 1]
        
        try:
            segment = RouteManager._get_osrm_route_fast([start, end])
            
            if segment and len(segment) > 1:
                if not concatenated:
                    concatenated.extend(segment)
                else:
                    concatenated.extend(segment[1:])  # Skip duplicate start point
                print(f"      Segment {i}->{i+1}: OK")
            else:
                # OSRM failed, use direct line
                if not concatenated:
                    concatenated.append(start)
                concatenated.append(end)
                print(f"      Segment {i}->{i+1}: Direct line (OSRM failed)")
                
        except Exception as e:
            # Direct line fallback
            if not concatenated:
                concatenated.append(start)
            concatenated.append(end)
            print(f"      Segment {i}->{i+1}: Direct line (error: {str(e)[:50]})")
    
    if concatenated:
        print(f"    Concatenated route: {len(concatenated)} points")
        return concatenated
    
    # Last resort: return waypoints
    print(f"    Using waypoints as fallback")
    return waypoint_coords


def display_solution_on_map(
    solution: Dict,
    nodes_lookup: Dict[str, Dict[str, float]]
) -> folium.Map:
    """
    Complete workflow: load solution and display on map
    
    Args:
        solution: solution.json dictionary
        nodes_lookup: Node coordinates
        output_file: Output HTML file name
    
    Returns:
        folium.Map object
    """
    
    print("\n" + "="*70)
    print("BUILDING MAP FROM SOLUTION.JSON")
    print("="*70)
    
    # Build map
    m = build_map_from_solution(solution, nodes_lookup)
    
    # Save map
    try:
        m.save(output_file)
        print(f"\nMap saved to: {output_file}")
    except Exception as e:
        print(f"Error saving map: {e}")
    
    print("="*70 + "\n")
    
    return m