# vehicle.py
from utils import config

# ───────────────────────────────
# Base Vehicle Class
# ───────────────────────────────
class Vehicle:
    def __init__(self, id, capacity_kg, speed_kmph, capacity_m3=None):
        self.id = id
        self.capacity_kg = capacity_kg
        self.capacity_m3 = capacity_m3
        self.speed_kmph = speed_kmph
        self.route = []

    def add_stop(self, node):
        self.route.append(node)

    def travel_time_hours(self, distance_km):
        return distance_km / self.speed_kmph

    def can_carry(self, weight_kg, volume_m3, distance_km=None):
        """Check payload and volume feasibility. Optional distance check in subclasses."""
        if weight_kg > self.capacity_kg:
            return False
        if self.capacity_m3 and volume_m3 > self.capacity_m3:
            return False
        if hasattr(self, "can_complete_route") and distance_km is not None:
            return self.can_complete_route(distance_km)
        return True

    def metrics(self, distance_km):
        raise NotImplementedError("Subclasses must implement metrics method")

    def total_cost(self, distance_km, max_energy_kwh, max_emission_kg):
        """Weighted cost function: α*distance + β*normalized_energy + γ*normalized_emissions"""
        m = self.metrics(distance_km)
        norm_energy = (m["energy_kwh"] / max_energy_kwh) if m["energy_kwh"] is not None else 0
        norm_emission = (m["co2_kg"] / max_emission_kg) if m["co2_kg"] is not None else 0
        return (
            config.ALPHA * distance_km
            + config.BETA * norm_energy
            + config.GAMMA * norm_emission
        )


# ───────────────────────────────
# Truck Base Class
# ───────────────────────────────
class Truck(Vehicle):
    def __init__(self, id, capacity_kg, speed_kmph, capacity_m3):
        super().__init__(id, capacity_kg, speed_kmph, capacity_m3)


# ───────────────────────────────
# Fuel Truck (Diesel)
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
        return distance_km / self.KM_PER_LITER

    def travel_cost_rs(self, distance_km):
        return self.fuel_consumption_l(distance_km) * self.FUEL_PRICE

    def emission_kg(self, distance_km):
        return self.fuel_consumption_l(distance_km) * self.DIESEL_CO2

    def metrics(self, distance_km):
        fuel = self.fuel_consumption_l(distance_km)
        cost = self.travel_cost_rs(distance_km)
        co2 = self.emission_kg(distance_km)
        return {
            "time_h": self.travel_time_hours(distance_km),
            "fuel_l": fuel,
            "energy_kwh": None,
            "cost_rs": cost,
            "co2_kg": co2,
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
    CONSUMPTION_KWH_PER_KM = BATTERY_KWH / RANGE_KM

    def __init__(self, id):
        super().__init__(id, self.PAYLOAD_KG, self.AVG_SPEED_KMPH, self.PAYLOAD_CM3)

    def energy_consumption_kwh(self, distance_km):
        return distance_km * self.CONSUMPTION_KWH_PER_KM

    def can_complete_route(self, distance_km):
        """Check if round-trip is within battery range."""
        return self.energy_consumption_kwh(distance_km * 2) <= self.BATTERY_KWH

    def travel_cost_rs(self, distance_km):
        return self.energy_consumption_kwh(distance_km) * self.ELECTRICITY_PRICE

    def emission_kg(self, distance_km):
        return self.energy_consumption_kwh(distance_km) * self.GRID_CO2

    def metrics(self, distance_km):
        energy = self.energy_consumption_kwh(distance_km)
        cost = self.travel_cost_rs(distance_km)
        co2 = self.emission_kg(distance_km)
        return {
            "time_h": self.travel_time_hours(distance_km),
            "fuel_l": None,
            "energy_kwh": energy,
            "cost_rs": cost,
            "co2_kg": co2,
            "feasible": self.can_complete_route(distance_km),
        }


# ───────────────────────────────
# Drone
# ───────────────────────────────
class Drone(Vehicle):
    SPEED_KMPH = config.DRONE_SPEED
    MAX_RANGE_KM = config.DRONE_MAX_RANGE
    PAYLOAD_KG = config.DRONE_PAYLOAD_KG
    PAYLOAD_CM3 = config.DRONE_PAYLOAD_CM3
    ELECTRICITY_PRICE = config.ELECTRICITY_PRICE
    GRID_CO2 = config.GRID_CO2
    KWH_PER_KM = config.DRONE_KWH_PER_KM

    def __init__(self, id):
        super().__init__(id, self.PAYLOAD_KG, self.SPEED_KMPH, self.PAYLOAD_CM3)
        self.battery_life_min = (self.MAX_RANGE_KM / self.SPEED_KMPH) * 60.0

    def flight_time_minutes(self, distance_km):
        return (distance_km / self.SPEED_KMPH) * 60.0

    def energy_consumption_kwh(self, distance_km):
        return distance_km * self.KWH_PER_KM

    def can_complete_route(self, distance_km):
        return distance_km * 2 <= self.MAX_RANGE_KM and self.flight_time_minutes(distance_km * 2) <= self.battery_life_min

    def travel_cost_rs(self, distance_km):
        return self.energy_consumption_kwh(distance_km) * self.ELECTRICITY_PRICE

    def emission_kg(self, distance_km):
        return self.energy_consumption_kwh(distance_km) * self.GRID_CO2

    def metrics(self, distance_km):
        energy = self.energy_consumption_kwh(distance_km)
        cost = self.travel_cost_rs(distance_km)
        co2 = self.emission_kg(distance_km)
        return {
            "time_h": self.travel_time_hours(distance_km),
            "fuel_l": None,
            "energy_kwh": energy,
            "cost_rs": cost,
            "co2_kg": co2,
            "feasible": self.can_complete_route(distance_km),
        }
