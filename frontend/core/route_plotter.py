import requests
from typing import Dict, List, Any, Optional, Tuple
import folium

# reuse your RouteManager (the OSRM-based manager you added earlier)
from .route_manager import RouteManager

def build_node_lookup(nodes: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Convert list of node dicts to lookup: node_id -> {"lat":..., "lon":...}
    Expect node dicts to include at least 'node_id', 'lat', 'lon'.
    """
    lookup = {}
    for n in nodes:
        nid = n.get("node_id") or n.get("id") or n.get("name")
        if not nid:
            continue
        lookup[nid] = {"lat": float(n["lat"]), "lon": float(n["lon"])}
    return lookup

def coords_from_node_ids(node_ids: List[str], nodes_lookup: Dict[str, Dict[str, float]]) -> List[List[float]]:
    """
    Convert list of node ids (['depot','cust_1',...]) to list of [lat, lon].
    Raises KeyError if a node id is missing.
    """
    coords = []
    for nid in node_ids:
        if nid not in nodes_lookup:
            raise KeyError(f"Missing node coordinates for id: {nid}")
        p = nodes_lookup[nid]
        coords.append([p["lat"], p["lon"]])
    return coords

def build_map_from_solution(
    solution: Dict[str, Any],
    nodes_lookup: Dict[str, Dict[str, float]],
    backend_center: Optional[Tuple[float, float]] = None,
    tiles: str = "OpenStreetMap"
) -> folium.Map:
    """
    Build a folium.Map with:
      - truck routes as road-following polylines (OSRM)
      - drone routes as straight/fast lines (depot->cust->depot)
      - markers for depot / customer nodes

    solution: parsed JSON (initial_solution.json structure)
    nodes_lookup: node_id -> {"lat":..., "lon":...}
    returns folium.Map
    """
    # map center fallback
    if backend_center:
        center = backend_center
    else:
        # try depot coords
        depot = nodes_lookup.get("depot") or next(iter(nodes_lookup.values()))
        center = (depot["lat"], depot["lon"])

    m = folium.Map(location=center, zoom_start=10, tiles=tiles)

    # add markers for nodes
    for nid, p in nodes_lookup.items():
        folium.CircleMarker(
            location=(p["lat"], p["lon"]),
            radius=5,
            color="purple" if nid.startswith("cust") else "blue",
            fill=True,
            fill_opacity=0.8,
            popup=f"{nid}"
        ).add_to(m)

    # Pull wave(s)
    waves = {k: v for k, v in solution.items() if k.startswith("wave_")} if "wave_1" not in solution else {"wave_1": solution.get("wave_1")}
    # if solution already top-level 'wave_1', handle that
    if "wave_1" in solution:
        waves = {"wave_1": solution["wave_1"]}

    # process each wave
    for wave_name, wave in waves.items():
        # drones
        for d in wave.get("drones", []):
            try:
                route_node_ids = d.get("route", [])
                route_coords = coords_from_node_ids(route_node_ids, nodes_lookup)
            except KeyError as e:
                # skip missing nodes
                continue
            # draw straight polyline (distinct style)
            folium.PolyLine(locations=route_coords, color="red", weight=2.5, dash_array="5, 5", popup=d.get("vehicle_id")).add_to(m)

        # trucks
        for t in wave.get("trucks", []):
            try:
                node_ids = t.get("route", [])
                # convert node ids to lat/lon list
                waypoint_coords = coords_from_node_ids(node_ids, nodes_lookup)
            except KeyError:
                continue

            # Try OSRM via RouteManager (returns list of [lat, lon] polyline or None)
            try:
                osrm_poly = RouteManager._get_osrm_route_fast(waypoint_coords)  # uses [lat,lon] input
            except Exception:
                osrm_poly = None

            # If OSRM returned degenerate/None, attempt pairwise OSRM and join segments
            if not osrm_poly:
                concatenated = []
                for i in range(len(waypoint_coords) - 1):
                    seg = RouteManager._get_osrm_route_fast([waypoint_coords[i], waypoint_coords[i + 1]])
                    if seg and len(seg) > 1:
                        if not concatenated:
                            concatenated.extend(seg)
                        else:
                            concatenated.extend(seg[1:])  # avoid duplicate join point
                    else:
                        # OSRM failed for this pair -> log and add direct segment (last resort)
                        print(f"⚠️ OSRM missing segment {i}->{i+1} for truck {t.get('vehicle_id')}, using straight connection")
                        # include both endpoints to preserve route order
                        if not concatenated:
                            concatenated.append(waypoint_coords[i])
                        concatenated.append(waypoint_coords[i + 1])
                osrm_poly = concatenated if concatenated else waypoint_coords

            # draw truck polyline (solid, different color)
            folium.PolyLine(locations=osrm_poly, color="green", weight=3, opacity=0.9, popup=t.get("vehicle_id")).add_to(m)

    return m

# Example usage:
# nodes = requests.get(f"{BACKEND_BASE}/api/nodes").json()
# nodes_lookup = build_node_lookup(nodes)
# solution = requests.get(f"{BACKEND_BASE}/api/initial_solution").json()
# m = build_map_from_solution(solution, nodes_lookup)
# m.save("routes_map.html")