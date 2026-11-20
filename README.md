# Optimizing Hybrid Drone–Truck Delivery Using Adaptive Large Neighborhood Search (ALNS)

## Overview

The **Hybrid Drone–Truck Delivery Optimization System** is a multi-objective logistics optimization platform designed to improve the efficiency and sustainability of last-mile delivery operations.

The system integrates a heterogeneous fleet consisting of conventional fuel trucks, electric trucks, and autonomous delivery drones. It employs the **Adaptive Large Neighborhood Search (ALNS)** metaheuristic algorithm, combined with Simulated Annealing, to generate optimized delivery routes while considering operational, environmental, and social factors.

Unlike conventional routing approaches that primarily focus on distance or delivery time, this system incorporates energy consumption, carbon emissions, operational costs, noise pollution, vehicle capacity, and real-world geographical constraints into the optimization process.

## Problem Statement

Traditional last-mile delivery systems face challenges related to increasing operational costs, traffic congestion, fuel consumption, and environmental pollution.

Existing drone-assisted delivery models often overlook practical constraints such as volumetric payload capacity, restricted airspace, diverse road conditions, and noise pollution.

This project addresses these limitations by developing an intelligent hybrid delivery optimization framework that combines multiple transportation modes to achieve efficient, cost-effective, and environmentally sustainable delivery operations.

## Key Features

- **Hybrid Fleet Management:** Integrates fuel trucks, electric trucks, and delivery drones within a unified routing framework.
- **ALNS-Based Route Optimization:** Implements Adaptive Large Neighborhood Search to improve delivery route assignments.
- **Multi-Objective Optimization:** Considers travel time, operational cost, energy consumption, carbon emissions, and acoustic impact.
- **Simulated Annealing:** Uses probabilistic acceptance to escape local optima and explore better solutions.
- **Capacity-Aware Routing:** Considers both weight and volumetric payload constraints.
- **Geographical Route Planning:** Uses OpenStreetMap and routing services for road-distance calculations.
- **No-Fly Zone Management:** Incorporates restricted airspace constraints into drone route planning.
- **Life Cycle Assessment (LCA):** Evaluates environmental impact using vehicle and energy-related emission factors.
- **Noise Impact Analysis:** Considers acoustic footprints when evaluating delivery operations.
- **Multi-Wave Scheduling:** Assigns delivery tasks across available vehicles and successive operational waves.
- **Interactive Route Visualization:** Displays optimized routes and delivery assignments through interactive maps.
- **Performance Analytics:** Provides comparative analysis of optimization performance and environmental impact.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.8+ |
| GUI Framework | PyQt5 |
| Web Rendering | QWebEngineView |
| Map Visualization | Leaflet.js |
| Geospatial Data | OpenStreetMap (OSM) |
| Routing Services | OpenRouteService (ORS) API |
| Database | Turso |
| Optimization Algorithm | Adaptive Large Neighborhood Search (ALNS) |
| Optimization Strategy | Simulated Annealing |
| Development Environment | Windows, VS Code |

## Optimization Methodology

The system implements an ALNS-based optimization approach consisting of the following stages:

### 1. Problem Initialization

- Loads delivery locations, depot information, and fleet specifications.
- Initializes vehicle capacities, speeds, operational ranges, and cost parameters.
- Generates distance and travel-time matrices.

### 2. Initial Solution Generation

Creates an initial feasible delivery assignment by distributing delivery locations among available drones and trucks while respecting operational constraints.

### 3. Destroy Phase

Removes selected delivery assignments from the current solution using specialized destroy operators to explore alternative routing configurations.

### 4. Repair Phase

Reinserts removed delivery locations into feasible routes using repair operators while considering vehicle compatibility and operational constraints.

### 5. Solution Acceptance

Uses Simulated Annealing to determine whether a newly generated solution should replace the current solution. This allows exploration beyond local optima.

### 6. Adaptive Operator Selection

Adjusts operator selection based on their performance during optimization, improving the search process over successive iterations.

### 7. Final Route Generation

Generates optimized vehicle assignments, delivery schedules, route summaries, and performance metrics.

## Fleet Configuration

The optimization framework supports three transportation categories:

| Vehicle Type | Primary Function |
|---|---|
| Fuel Trucks | Conventional road-based deliveries |
| Electric Trucks | Lower-emission road transportation |
| Delivery Drones | Eligible short-distance aerial deliveries |

Each vehicle is evaluated using its operational specifications, including payload capacity, volume capacity, speed, range, energy consumption, and operating cost.

## Objective Functions and Constraints

The optimization framework considers multiple objectives:

- Minimize total delivery time.
- Minimize operational and transportation costs.
- Reduce energy consumption.
- Minimize carbon dioxide emissions.
- Reduce noise pollution.

**Operational constraints include:**

- Vehicle weight and volumetric capacity.
- Drone flight range and payload limitations.
- Vehicle speed and operational range.
- Restricted flying zones.
- Delivery location accessibility.
- Fleet availability and scheduling.
- Road-distance and travel-time variations.

## Performance Evaluation

The proposed framework was evaluated through simulation experiments involving delivery instances of up to 500 customers.

Key reported findings include:

- **21.1% mean optimization improvement** across the evaluated experiments.
- Reduction in carbon emissions and operational costs compared with the initial delivery solutions.
- Evaluation of noise-related environmental impact.
- **87% public acceptance**, based on the supplementary survey, regarding drones as a viable alternative to conventional delivery methods.

The evaluation also examines scalability, route quality, and the performance of the optimization algorithm across different delivery scenarios.

## System Architecture

The platform follows a modular architecture consisting of:

1. **Input Management:** Handles delivery locations, vehicle configurations, and operational parameters.
2. **Geospatial Processing:** Calculates road distances and geographical information.
3. **Optimization Engine:** Executes ALNS with destroy and repair operators.
4. **Constraint Management:** Validates vehicle capacities, operational ranges, and restricted zones.
5. **Environmental Assessment:** Calculates emissions, energy consumption, and noise impact.
6. **Database Layer:** Stores delivery information, vehicle configurations, and optimization results.
7. **Visualization Layer:** Presents route maps, vehicle assignments, and optimization analytics.

## Applications

- Sustainable last-mile delivery planning.
- E-commerce logistics optimization.
- Urban and rural delivery management.
- Hybrid transportation fleet management.
- Environmentally conscious logistics planning.
- Transportation research and simulation.

## Future Enhancements

- Integration with real-time traffic information.
- Dynamic route re-optimization.
- Weather-aware drone scheduling.
- Real-world fleet integration.
- Advanced predictive delivery demand analysis.
- Improved scalability for larger delivery networks.

## Project Team

| Team Member | USN |
|---|---|
| Durgesh A P | 4JK23CS035 |
| Keerthana | 4JK23CS051 |
| Neekshith | 4JK23CS068 |

**Department:** Computer Science and Engineering  
**Institution:** A J Institute of Engineering and Technology, Mangaluru  
**Academic Year:** 2025–2026

**Project Guide:** Mrs. Snitha Shetty

---

*An optimization-driven approach towards intelligent, efficient, and sustainable last-mile delivery.*
