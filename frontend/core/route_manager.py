import math
import random
import threading
import time
import functools
import requests
import os
import shelve
import hashlib
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# tune for higher precision
OSRM_BASE = os.getenv("OSRM_BASE", "http://router.project-osrm.org")
RESAMPLE_SPACING_M = 2.0       # densify to ~2 meters
OSRM_TIMEOUT = 30
OSRM_RETRIES = 4
_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", ".cache_osrm")
os.makedirs(_CACHE_PATH, exist_ok=True)
_cache_lock = threading.Lock()

def _cache_key_for_points(points):
    # stable short key for a sequence of lat/lon points
    s = "|".join(f"{p[0]:.6f},{p[1]:.6f}" for p in points)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def _cache_get(key):
    with _cache_lock:
        with shelve.open(os.path.join(_CACHE_PATH, "osrm_cache"), writeback=False) as db:
            return db.get(key)

def _cache_set(key, value):
    with _cache_lock:
        with shelve.open(os.path.join(_CACHE_PATH, "osrm_cache"), writeback=False) as db:
            db[key] = value

# high-precision helpers (map-match + route + densify)
def _haversine_m(p1, p2):
    R = 6371000.0
    phi1, phi2 = math.radians(p1[0]), math.radians(p2[0])
    dphi = math.radians(p2[0] - p1[0])
    dlambda = math.radians(p2[1] - p1[1])
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def _resample_polyline(poly, target_m=RESAMPLE_SPACING_M):
    if not poly or target_m <= 0:
        return poly[:]
    out = [poly[0]]
    for a, b in zip(poly, poly[1:]):
        seg_dist = _haversine_m(a, b)
        if seg_dist <= 0:
            continue
        steps = max(1, int(math.ceil(seg_dist / target_m)))
        for i in range(1, steps + 1):
            t = i / steps
            lat = a[0] + (b[0] - a[0]) * t
            lon = a[1] + (b[1] - a[1]) * t
            out.append([lat, lon])
    # dedupe tiny duplicates
    dedup = [out[0]]
    for p in out[1:]:
        if _haversine_m(dedup[-1], p) > 0.3:
            dedup.append(p)
    return dedup

def _snap_to_road(point):
    # returns [lat,lon]
    key = _cache_key_for_points([point])  # one-point key
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        lon, lat = point[1], point[0]
        url = f"{OSRM_BASE}/nearest/v1/driving/{lon},{lat}"
        resp = requests.get(url, params={"number": 1}, timeout=6)
        if resp.status_code != 200:
            return point
        data = resp.json()
        w = data.get("waypoints") or []
        if not w:
            return point
        loc = w[0].get("location")
        if not loc or len(loc) < 2:
            return point
        res = [loc[1], loc[0]]
        _cache_set(key, res)
        return res
    except requests.RequestException:
        return point

def _osrm_match_trace(pts):
    if len(pts) < 2:
        return None
    key = _cache_key_for_points(pts)
    cached = _cache_get(key)
    if cached:
        return cached
    coords_str = ";".join(f"{p[1]},{p[0]}" for p in pts)
    url = f"{OSRM_BASE}/match/v1/driving/{coords_str}"
    params = {"geometries": "geojson", "overview": "full", "steps": "true", "tidy": "true"}
    for attempt in range(1, OSRM_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=OSRM_TIMEOUT)
            if resp.status_code != 200:
                if resp.status_code in (429,) or 500 <= resp.status_code < 600:
                    time.sleep(min(20, (2 ** (attempt - 1)) + random.random()))
                    continue
                return None
            data = resp.json()
            if data.get("code") != "Ok":
                return None
            matchings = data.get("matchings") or []
            if not matchings:
                return None
            coords = []
            for m in matchings:
                geom = m.get("geometry") or {}
                seg = geom.get("coordinates") or []
                if seg:
                    if not coords:
                        coords.extend([[c[1], c[0]] for c in seg])
                    else:
                        coords.extend([[c[1], c[0]] for c in seg[1:]])
            if coords and len(coords) > 2:
                out = _resample_polyline(coords, target_m=RESAMPLE_SPACING_M)
                _cache_set(key, out)
                return out
            return None
        except requests.RequestException:
            time.sleep(min(20, (2 ** (attempt - 1)) + random.random()))
            continue
    return None

def _request_route(points):
    coords_str = ";".join(f"{p[1]},{p[0]}" for p in points)
    url = f"{OSRM_BASE}/route/v1/driving/{coords_str}"
    params = {"overview": "full", "geometries": "geojson", "steps": "true"}
    last_text = None
    for attempt in range(1, OSRM_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=OSRM_TIMEOUT)
            last_text = resp.text
            if resp.status_code != 200:
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
                    time.sleep(min(30, (2 ** (attempt - 1)) + random.random()))
                    continue
                return None
            data = resp.json()
            if data.get("code") != "Ok":
                return None
            routes = data.get("routes") or []
            if not routes:
                return None
            return routes[0]
        except requests.RequestException:
            time.sleep(min(30, (2 ** (attempt - 1)) + random.random()))
            continue
    return None

def _assemble_from_route_obj(route_obj):
    if not route_obj:
        return None
    geom = route_obj.get("geometry") or {}
    coords = geom.get("coordinates") or []
    if coords and len(coords) > 3:
        poly = [[c[1], c[0]] for c in coords]
        return _resample_polyline(poly, target_m=RESAMPLE_SPACING_M)
    assembled = []
    legs = route_obj.get("legs") or []
    for leg in legs:
        steps = leg.get("steps") or []
        for step in steps:
            step_geom = step.get("geometry")
            if not step_geom:
                continue
            if isinstance(step_geom, dict) and "coordinates" in step_geom:
                seg_coords = step_geom["coordinates"]
            else:
                seg_coords = step_geom
            if not seg_coords:
                continue
            if not assembled:
                assembled.extend([[c[1], c[0]] for c in seg_coords])
            else:
                assembled.extend([[c[1], c[0]] for c in seg_coords[1:]])
    if assembled and len(assembled) > 3:
        return _resample_polyline(assembled, target_m=RESAMPLE_SPACING_M)
    return None

# new high-precision entry point
def get_high_precision_osrm_route(waypoints):
    if len(waypoints) < 2:
        return None
    # snap all points
    snapped = []
    for p in waypoints:
        snapped.append(_snap_to_road(p))
    # check cache
    key = _cache_key_for_points(snapped)
    cached = _cache_get(key)
    if cached:
        return cached
    # try multi-waypoint match (only when reasonably short)
    if len(snapped) <= 12:  # avoid huge match requests
        match_poly = _osrm_match_trace(snapped)
        if match_poly:
            _cache_set(key, match_poly)
            return match_poly
    # try multi-waypoint route
    route0 = _request_route(snapped)
    poly = _assemble_from_route_obj(route0)
    if poly:
        _cache_set(key, poly)
        return poly
    # per-leg: try match per leg -> route per leg -> straight fallback
    concatenated = []
    for i in range(len(snapped) - 1):
        a, b = snapped[i], snapped[i + 1]
        leg_key = _cache_key_for_points([a, b])
        leg_cached = _cache_get(leg_key)
        if leg_cached:
            leg_poly = leg_cached
        else:
            leg_poly = _osrm_match_trace([a, b])
            if not leg_poly:
                leg_obj = _request_route([a, b])
                leg_poly = _assemble_from_route_obj(leg_obj)
            if not leg_poly:
                # final fallback: direct snapped endpoints
                leg_poly = [a, b]
            _cache_set(leg_key, leg_poly)
        if not concatenated:
            concatenated.extend(leg_poly)
        else:
            concatenated.extend(leg_poly[1:])
    if concatenated and len(concatenated) > 2:
        out = _resample_polyline(concatenated, target_m=RESAMPLE_SPACING_M)
        _cache_set(key, out)
        return out
    return None

class BaseRouteManager:
    def __init__(self):
        self.route_cache: Dict = {}
        self.distance_cache: Dict = {}

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _create_drone_route_direct(self, depot: List[float], delivery: List[float]) -> List[List[float]]:
        return [depot[:], delivery[:], depot[:]]

    def _create_realistic_path(self, start: List[float], end: List[float]) -> List[List[float]]:
        path = [start[:]]
        count = 3
        for i in range(1, count + 1):
            t = i / (count + 1)
            lat = start[0] + (end[0] - start[0]) * t
            lon = start[1] + (end[1] - start[1]) * t
            deviation = 0.001 * math.sin(math.pi * t)
            lat += deviation * (1 if i % 2 == 0 else -1)
            lon += deviation * 0.5 * (1 if i % 2 == 1 else -1)
            path.append([lat, lon])
        path.append(end[:])
        return path


class OptimizedRouteManager(BaseRouteManager):
    _route_cache: Dict = {}
    _cache_lock = threading.Lock()
    MAX_WORKERS = 4

    def __init__(self):
        super().__init__()

    @classmethod
    def build_delivery_routes_batch(cls, depot: List[float], delivery_assignments: Dict) -> Dict:
        drone_requests = []
        truck_requests = []
        for vehicle_name, assignment in delivery_assignments.items():
            req = {
                "vehicle_name": vehicle_name,
                "depot": depot,
                "all_deliveries": assignment.get("all_deliveries", [assignment.get("primary_delivery")]),
                "type": assignment.get("type", "Truck"),
            }
            if req["type"] == "Drone":
                drone_requests.append(req)
            else:
                truck_requests.append(req)

        manager = cls()
        results: Dict[str, Dict] = {}

        for req in drone_requests:
            route = manager._create_drone_route_direct(req["depot"], req["all_deliveries"][0])
            results[req["vehicle_name"]] = {"route": route, "all_deliveries": req["all_deliveries"]}

        if truck_requests:
            truck_results = cls._process_truck_routes_parallel(truck_requests, manager)
            results.update(truck_results)

        return results

    @classmethod
    def _process_truck_routes_parallel(cls, truck_routes: List[Dict], manager) -> Dict:
        results: Dict[str, Dict] = {}
        with ThreadPoolExecutor(max_workers=cls.MAX_WORKERS) as ex:
            futures = {
                ex.submit(cls._build_single_truck_route, req["depot"], req["all_deliveries"], manager): req
                for req in truck_routes
            }
            for fut in as_completed(futures):
                req = futures[fut]
                try:
                    route = fut.result()
                    if route:
                        results[req["vehicle_name"]] = {"route": route, "all_deliveries": req["all_deliveries"]}
                except Exception:
                    waypoints = [req["depot"]] + req["all_deliveries"] + [req["depot"]]
                    fallback_route = [waypoints[0]]
                    for i in range(len(waypoints) - 1):
                        seg = manager._create_realistic_path(waypoints[i], waypoints[i + 1])
                        fallback_route.extend(seg[1:])
                    results[req["vehicle_name"]] = {"route": fallback_route, "all_deliveries": req["all_deliveries"]}
        return results

    @classmethod
    def _build_single_truck_route(cls, depot: List[float], deliveries: List[List[float]], manager) -> List[List[float]]:
        full_trip = [depot] + deliveries + [depot]
        return cls._get_truck_route_with_fallback(full_trip, manager)

    @classmethod
    def _get_truck_route_with_fallback(cls, waypoints: List[List[float]], manager) -> List[List[float]]:
        cache_key = tuple(tuple(round(c, 6) for c in p) for p in waypoints)
        with cls._cache_lock:
            if cache_key in cls._route_cache:
                return cls._route_cache[cache_key][:]

        route = cls._get_osrm_route_fast(waypoints)
        if route:
            with cls._cache_lock:
                cls._route_cache[cache_key] = route[:]
            return route

        fallback = [waypoints[0]]
        for i in range(len(waypoints) - 1):
            seg = manager._create_realistic_path(waypoints[i], waypoints[i + 1])
            fallback.extend(seg[1:])
        with cls._cache_lock:
            cls._route_cache[cache_key] = fallback[:]
        return fallback

    @staticmethod
    def _haversine_m(p1: List[float], p2: List[float]) -> float:
        """Haversine distance in meters; p = [lat, lon]"""
        R = 6371000.0
        phi1, phi2 = math.radians(p1[0]), math.radians(p2[0])
        dphi = math.radians(p2[0] - p1[0])
        dlambda = math.radians(p2[1] - p1[1])
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    @classmethod
    def _resample_polyline(cls, poly: List[List[float]], target_m: float = RESAMPLE_SPACING_M) -> List[List[float]]:
        """Densify a [lat,lon] polyline so consecutive points are about target_m apart."""
        if not poly or target_m <= 0:
            return poly[:]
        out = [poly[0]]
        for a, b in zip(poly, poly[1:]):
            seg_dist = cls._haversine_m(a, b)
            if seg_dist <= 0:
                continue
            steps = max(1, int(math.ceil(seg_dist / target_m)))
            for i in range(1, steps + 1):
                t = i / steps
                lat = a[0] + (b[0] - a[0]) * t
                lon = a[1] + (b[1] - a[1]) * t
                out.append([lat, lon])
        # remove possible duplicates
        dedup = [out[0]]
        for p in out[1:]:
            if cls._haversine_m(dedup[-1], p) > 0.5:  # >0.5m
                dedup.append(p)
        return dedup

    @classmethod
    def _snap_to_road(cls, point: List[float]) -> List[float]:
        """OSRM nearest endpoint to snap a lat/lon -> [lat, lon]."""
        try:
            lon, lat = point[1], point[0]
            url = f"{OSRM_BASE}/nearest/v1/driving/{lon},{lat}"
            resp = requests.get(url, params={"number": 1}, timeout=6)
            if resp.status_code != 200:
                return point
            data = resp.json()
            waypoints = data.get("waypoints") or []
            if not waypoints:
                return point
            loc = waypoints[0].get("location")
            if not loc or len(loc) < 2:
                return point
            return [loc[1], loc[0]]
        except requests.RequestException:
            return point

    @classmethod
    def _get_precise_osrm_route(cls, waypoints: List[List[float]]) -> Optional[List[List[float]]]:
        """
        High-precision OSRM route:
         - snap stops
         - request full geometry + steps
         - if result coarse, assemble from steps
         - if multi-waypoint still poor, do per-leg and concatenate
         - densify polyline to RESAMPLE_SPACING_M
        """
        if len(waypoints) < 2:
            return None

        # Snap all waypoints first (gives better routing fidelity)
        snapped = []
        for p in waypoints:
            snapped.append(cls._snap_to_road(p))

        def request_route(points: List[List[float]]):
            coords_str = ";".join(f"{p[1]},{p[0]}" for p in points)  # lon,lat
            url = f"{OSRM_BASE}/route/v1/driving/{coords_str}"
            params = {"overview": "full", "geometries": "geojson", "steps": "true"}
            last_text = None
            for attempt in range(1, OSRM_RETRIES + 1):
                try:
                    resp = requests.get(url, params=params, timeout=OSRM_TIMEOUT)
                    last_text = resp.text
                    if resp.status_code != 200:
                        # backoff on 429/5xx
                        if resp.status_code == 429 or 500 <= resp.status_code < 600:
                            wait = min(30, (2 ** (attempt - 1)) + random.random())
                            time.sleep(wait)
                            continue
                        return None
                    data = resp.json()
                    if data.get("code") != "Ok":
                        return None
                    routes = data.get("routes") or []
                    if not routes:
                        return None
                    return routes[0]
                except requests.RequestException:
                    wait = min(30, (2 ** (attempt - 1)) + random.random())
                    time.sleep(wait)
                    continue
            return None

        # Try full multi-waypoint request first
        route0 = request_route(snapped)
        def assemble_from_route(route_obj) -> Optional[List[List[float]]]:
            if not route_obj:
                return None
            # try top-level geometry first
            geom = route_obj.get("geometry") or {}
            coords = geom.get("coordinates") or []
            if coords and len(coords) > 3:
                poly = [[c[1], c[0]] for c in coords]
                return cls._resample_polyline(poly)
            # otherwise assemble from steps for higher density
            assembled = []
            legs = route_obj.get("legs") or []
            for leg in legs:
                steps = leg.get("steps") or []
                for step in steps:
                    step_geom = step.get("geometry")
                    if not step_geom:
                        continue
                    if isinstance(step_geom, dict) and "coordinates" in step_geom:
                        seg_coords = step_geom["coordinates"]
                    else:
                        seg_coords = step_geom
                    if not seg_coords:
                        continue
                    if not assembled:
                        assembled.extend([[c[1], c[0]] for c in seg_coords])
                    else:
                        assembled.extend([[c[1], c[0]] for c in seg_coords[1:]])
            if assembled and len(assembled) > 3:
                return cls._resample_polyline(assembled)
            return None

        poly = assemble_from_route(route0)
        if poly:
            return poly

        # If multi-waypoint returned poor geometry, fall back to per-leg and concatenate
        concatenated = []
        for i in range(len(snapped) - 1):
            leg_obj = request_route([snapped[i], snapped[i + 1]])
            leg_poly = assemble_from_route(leg_obj)
            if leg_poly and len(leg_poly) > 1:
                if not concatenated:
                    concatenated.extend(leg_poly)
                else:
                    concatenated.extend(leg_poly[1:])
            else:
                # OSRM failed for this pair — use straight snap fallback (very last resort)
                print(f"⚠️ OSRM leg failed {i}->{i+1}, using straight segment between snapped points")
                if not concatenated:
                    concatenated.append(snapped[i])
                concatenated.append(snapped[i + 1])

        if concatenated and len(concatenated) > 2:
            return cls._resample_polyline(concatenated)

        return None

    @classmethod
    def _osrm_match_trace(cls, pts: List[List[float]]) -> Optional[List[List[float]]]:
        """Use OSRM /match to get a high-fidelity road geometry for a small trace (pts = [lat,lon])."""
        if len(pts) < 2:
            return None
        coords_str = ";".join(f"{p[1]},{p[0]}" for p in pts)
        url = f"{OSRM_BASE}/match/v1/driving/{coords_str}"
        params = {"geometries": "geojson", "overview": "full", "steps": "true", "tidy": "true"}
        for attempt in range(1, OSRM_RETRIES + 1):
            try:
                resp = requests.get(url, params=params, timeout=OSRM_TIMEOUT)
                if resp.status_code != 200:
                    # backoff on transient server issues
                    if resp.status_code in (429,) or 500 <= resp.status_code < 600:
                        time.sleep(min(20, (2 ** (attempt - 1)) + random.random()))
                        continue
                    return None
                data = resp.json()
                if data.get("code") != "Ok":
                    return None
                matchings = data.get("matchings") or []
                if not matchings:
                    return None
                # assemble all matchings (usually one) into a polyline
                coords = []
                for m in matchings:
                    geom = m.get("geometry") or {}
                    seg = geom.get("coordinates") or []
                    if seg:
                        # convert [lon,lat] -> [lat,lon]
                        if not coords:
                            coords.extend([[c[1], c[0]] for c in seg])
                        else:
                            coords.extend([[c[1], c[0]] for c in seg[1:]])
                if coords and len(coords) > 2:
                    return cls._resample_polyline(coords, target_m=RESAMPLE_SPACING_M)
                return None
            except requests.RequestException:
                time.sleep(min(20, (2 ** (attempt - 1)) + random.random()))
                continue
        return None

    # In _get_precise_osrm_route: try match first for each leg when top-level geometry is poor
    # (inside your existing implementation replace the per-leg request route section with:)
        # try top-level multi-waypoint route (existing code) -> poly
        # if poly is None:
        #    # attempt per-leg map-matching first
        concatenated = []
        for i in range(len(snapped) - 1):
            # try match on a short trace containing the two snapped endpoints and a tiny midpoint
            a, b = snapped[i], snapped[i+1]
            mid = [(a[0]+b[0])/2 + 1e-6, (a[1]+b[1])/2 + 1e-6]  # tiny perturbation to make a trace
            leg_match = cls._osrm_match_trace([a, mid, b])
            if leg_match and len(leg_match) > 1:
                if not concatenated:
                    concatenated.extend(leg_match)
                else:
                    concatenated.extend(leg_match[1:])
                continue
            # fallback to normal route for this leg (existing request_route usage)
            leg_obj = request_route([a, b])
            leg_poly = assemble_from_route(leg_obj)
            if leg_poly and len(leg_poly) > 1:
                if not concatenated:
                    concatenated.extend(leg_poly)
                else:
                    concatenated.extend(leg_poly[1:])
            else:
                # final fallback: straight snapped segment
                if not concatenated:
                    concatenated.append(a)
                concatenated.append(b)
        if concatenated and len(concatenated) > 2:
            return cls._resample_polyline(concatenated, target_m=RESAMPLE_SPACING_M)

        return None

    # keep old name for backward compatibility
    @classmethod
    def _get_osrm_route_fast(cls, waypoints: List[List[float]]) -> Optional[List[List[float]]]:
        return cls._get_precise_osrm_route(waypoints)


class RouteManager(OptimizedRouteManager):
    pass