from utils import config  # project-specific configuration constants

# ───────────────────────────────
# Base Vehicle Class
# ───────────────────────────────
class Vehicle:
    """Abstract base class for all vehicles (trucks, drones, etc.)."""

    def __init__(self, id, capacity_kg, speed_kmph, capacity_cm3=None):
        self.id = id
        self.capacity_kg = capacity_kg
        self.capacity_cm3 = capacity_cm3  # optional volume capacity in cm³
        self.speed_kmph = speed_kmph
        self.route = []  # list of stops (nodes)

    def add_stop(self, node):
        self.route.append(node)

    def travel_time_hours(self, distance_km):
        return distance_km / self.speed_kmph if distance_km else 0

    def can_carry(self, weight_kg, volume_cm3, distance_km=None):
        if weight_kg > self.capacity_kg:
            return False
        if self.capacity_cm3 and volume_cm3 > self.capacity_cm3:
            return False
        if hasattr(self, "can_complete_route") and distance_km is not None:
            return self.can_complete_route(distance_km)
        return True

    def metrics(self, distance_km: float) -> dict:
        """Return metrics for round-trip distance."""
        round_trip_distance = distance_km * 2
        energy = self.energy_consumption_kwh(round_trip_distance)
        return {
            "time_h": self.travel_time_hours(round_trip_distance),
            "fuel_l": None,
            "energy_kwh": energy,
            "cost_rs": self.travel_cost_rs(round_trip_distance),
            "co2_kg": self.emission_kg(round_trip_distance),
            "feasible": self.can_complete_route(distance_km),
        }
    
    def total_cost(self, distance_km, max_emission_kg):
        # Get CO2 emission for this distance
        m = self.metrics(distance_km)
        co2_kg = m.get("co2_kg", 0)
        norm_emission = co2_kg / max_emission_kg if max_emission_kg else 0

        # Get noise level from config
        vehicle_type_name = type(self).__name__  # 'FuelTruck', 'ElectricTruck', 'Drone'
        noise_level = config.NOISE_LEVELS.get(vehicle_type_name, 0)

        # Cost function
        return (
            config.ALPHA * distance_km
            + config.BETA * noise_level
            + config.GAMMA * norm_emission
        )


# ───────────────────────────────
# Truck Base Class
# ───────────────────────────────
class Truck(Vehicle):
    def __init__(self, id, capacity_kg, speed_kmph, capacity_cm3):
        super().__init__(id, capacity_kg, speed_kmph, capacity_cm3)


# ───────────────────────────────
# Fuel Truck
# ───────────────────────────────
class FuelTruck(Truck):
    KM_PER_LITER = config.FUEL_TRUCK_KM_PER_LITER
    PAYLOAD_KG = config.FUEL_TRUCK_PAYLOAD_KG
    PAYLOAD_CM3 = config.FUEL_TRUCK_PAYLOAD_CM3
    AVG_SPEED_KMPH = config.FUEL_TRUCK_SPEED
    FUEL_PRICE = config.FUEL_PRICE
    DIESEL_CO2 = config.DIESEL_CO2

    def __init__(self, id):
        super().__init__(id, self.PAYLOAD_KG, self.AVG_SPEED_KMPH, self.PAYLOAD_CM3)

    def fuel_consumption_l(self, distance_km):
        return distance_km / self.KM_PER_LITER if distance_km else 0

    def travel_cost_rs(self, distance_km):
        return self.fuel_consumption_l(distance_km) * self.FUEL_PRICE

    def emission_kg(self, distance_km):
        return self.fuel_consumption_l(distance_km) * self.DIESEL_CO2

    def metrics(self, distance_km):
        fuel = self.fuel_consumption_l(distance_km)
        return {
            "time_h": self.travel_time_hours(distance_km),
            "fuel_l": fuel,
            "energy_kwh": None,
            "cost_rs": self.travel_cost_rs(distance_km),
            "co2_kg": self.emission_kg(distance_km),
            "feasible": True,
        }


# ───────────────────────────────
# Electric Truck
# ───────────────────────────────
class ElectricTruck(Truck):
    BATTERY_KWH = config.ELECTRIC_TRUCK_BATTERY_KWH
    RANGE_KM = config.ELECTRIC_TRUCK_RANGE_KM
    PAYLOAD_KG = config.ELECTRIC_TRUCK_PAYLOAD_KG
    PAYLOAD_CM3 = config.ELECTRIC_TRUCK_PAYLOAD_CM3
    AVG_SPEED_KMPH = config.ELECTRIC_TRUCK_SPEED
    ELECTRICITY_PRICE = config.ELECTRICITY_PRICE
    GRID_CO2 = config.GRID_CO2
    CONSUMPTION_KWH_PER_KM = config.ELECTRIC_TRUCK_KWH_PER_KM

    def __init__(self, id):
        super().__init__(id, self.PAYLOAD_KG, self.AVG_SPEED_KMPH, self.PAYLOAD_CM3)

    def energy_consumption_kwh(self, distance_km):
        return distance_km * self.CONSUMPTION_KWH_PER_KM if distance_km else 0

    def can_complete_route(self, distance_km):
        return self.energy_consumption_kwh(distance_km * 2) <= self.BATTERY_KWH

    def travel_cost_rs(self, distance_km):
        return self.energy_consumption_kwh(distance_km) * self.ELECTRICITY_PRICE

    def emission_kg(self, distance_km):
        return self.energy_consumption_kwh(distance_km) * self.GRID_CO2

    def metrics(self, distance_km):
        energy = self.energy_consumption_kwh(distance_km)
        return {
            "time_h": self.travel_time_hours(distance_km),
            "fuel_l": None,
            "energy_kwh": energy,
            "cost_rs": self.travel_cost_rs(distance_km),
            "co2_kg": self.emission_kg(distance_km),
            "feasible": self.can_complete_route(distance_km),
        }


# ───────────────────────────────
# Drone
# ───────────────────────────────
class Drone(Vehicle):
    SPEED_KMPH = config.DRONE_SPEED
    MAX_RANGE_KM = config.DRONE_MAX_RANGE        # total round-trip range
    PAYLOAD_KG = config.DRONE_PAYLOAD_KG
    PAYLOAD_CM3 = config.DRONE_PAYLOAD_CM3
    ELECTRICITY_PRICE = config.ELECTRICITY_PRICE
    GRID_CO2 = config.GRID_CO2
    KWH_PER_KM = config.DRONE_KWH_PER_KM

    def __init__(self, id):
        super().__init__(id, self.PAYLOAD_KG, self.SPEED_KMPH, self.PAYLOAD_CM3)
        # battery life in minutes based on max range
        self.battery_life_min = (self.MAX_RANGE_KM / self.SPEED_KMPH) * 60.0

    def flight_time_minutes(self, distance_km: float) -> float:
        """Time in minutes for a one-way distance."""
        return (distance_km / self.SPEED_KMPH) * 60.0

    def energy_consumption_kwh(self, distance_km: float) -> float:
        """Energy consumed for a one-way distance."""
        return distance_km * self.KWH_PER_KM if distance_km else 0

    def can_complete_route(self, distance_km):
        """Check if drone can do a round-trip distance."""
        return distance_km * 2 <= self.MAX_RANGE_KM

    def can_carry(self, weight_kg, volume_cm3, distance_km=None):
        """Check payload first, then distance."""
        if weight_kg > self.PAYLOAD_KG or volume_cm3 > self.PAYLOAD_CM3:
            return False
        if distance_km is not None:
            return self.can_complete_route(distance_km)
        return True
    
    def travel_cost_rs(self, distance_km: float) -> float:
        """Cost in Rs based on electricity consumption."""
        return self.energy_consumption_kwh(distance_km) * self.ELECTRICITY_PRICE

    def emission_kg(self, distance_km: float) -> float:
        """CO2 emissions for given distance."""
        return self.energy_consumption_kwh(distance_km) * self.GRID_CO2

    def metrics(self, distance_km: float) -> dict:
        """Return metrics for a given one-way distance."""
        energy = self.energy_consumption_kwh(distance_km)
        return {
            "time_h": self.travel_time_hours(distance_km),
            "fuel_l": None,
            "energy_kwh": energy,
            "cost_rs": self.travel_cost_rs(distance_km),
            "co2_kg": self.emission_kg(distance_km),
            "feasible": self.can_complete_route(distance_km),
        }

# ───────────────────────────────
# Fleet Factory
# ───────────────────────────────
def create_fleet_vehicles(fleet_config=None):
    vehicles = []

    if fleet_config:
        electric_trucks = fleet_config.get("electric_trucks", 2)
        fuel_trucks = fleet_config.get("fuel_trucks", 1)
        drones = fleet_config.get("drones", 3)

        print(f"Creating fleet: {electric_trucks}E + {fuel_trucks}F + {drones}D")

        for i in range(electric_trucks):
            vehicles.append(ElectricTruck(id=f"E_Truck_{i+1}"))
        for i in range(fuel_trucks):
            vehicles.append(FuelTruck(id=f"F_Truck_{i+1}"))
        for i in range(drones):
            vehicles.append(Drone(id=f"Drone_{i+1}"))
    else:
        print("No fleet config provided, using defaults: 2E + 1F + 3D")
        for i in range(2):
            vehicles.append(ElectricTruck(id=f"E_Truck_{i+1}"))
        for i in range(1):
            vehicles.append(FuelTruck(id=f"F_Truck_{i+1}"))
        for i in range(3):
            vehicles.append(Drone(id=f"Drone_{i+1}"))

    return vehicles
