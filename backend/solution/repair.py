import numpy as np
from ..solver import preprocess as sp

depot_id = 'depot'

def greedy_truck_first_repair(state, rng: np.random.RandomState, **kwargs):
    """
    Repairs a solution by inserting unassigned customers with a specific priority logic:
    - For truck-only customers, it only considers inserting them into truck routes.
    - For drone-eligible customers, it finds the best possible truck insertion AND the
      best possible drone insertion, and chooses the one with the lower cost.
    """
    nodes_map = state.nodes_map
    vehicles_map = state.vehicles_map
    matrix = state.matrix

    # Shuffle the list to process customers in a random order
    rng.shuffle(state.unassigned)
    
    # Use a while loop to safely remove items while iterating
    customers_to_insert = state.unassigned[:]
    
    for customer_id in customers_to_insert:
        customer_node = nodes_map[customer_id]
        
        best_insertion = None
        min_cost_increase = float('inf')

        # Determine if the customer is drone-eligible
        is_drone_eligible = "D" in matrix.get((depot_id, customer_id), {})

        # Find the single best insertion point across all allowed vehicles
        for vehicle_id, route_state in state.routes.items():
            vehicle = vehicles_map[vehicle_id]
            if 'Drone' in vehicle_id: v_type = 'D'
            elif 'F_Truck' in vehicle_id: v_type = 'F'
            else: v_type = 'E'

            # LOGIC: If customer is NOT drone eligible, SKIP all drone routes
            if not is_drone_eligible and v_type == 'D':
                continue

            # --- Feasibility Constraints ---
            # 1. Vehicle Capacity
            current_weight = sum(nodes_map[node_id]['weight'] for node_id in route_state.nodes)
            current_volume = sum(nodes_map[node_id]['volume'] for node_id in route_state.nodes)
            if (current_weight + customer_node['weight'] > vehicle['capacity_kg'] or
                current_volume + customer_node['volume'] > vehicle['capacity_cm3']):
                continue

            # --- Find best insertion point within this specific route ---
            full_route = [depot_id] + route_state.nodes + [depot_id]
            for i in range(len(full_route) - 1):
                prev_node, next_node = full_route[i], full_route[i+1]

                cost_increase = (matrix.get((prev_node, customer_id), {}).get(v_type, (0,0,float('inf')))[2]
                               + matrix.get((customer_id, next_node), {}).get(v_type, (0,0,float('inf')))[2]
                               - matrix.get((prev_node, next_node), {}).get(v_type, (0,0,float('inf')))[2])

                # Check vehicle range constraint
                new_route = full_route[:i+1] + [customer_id] + full_route[i+1:]
                new_total_dist = sum(matrix.get((new_route[j], new_route[j+1]), {}).get(v_type, (0,0,0))[0] for j in range(len(new_route)-1))
                if 'range_km' in vehicle and new_total_dist > vehicle['range_km']:
                    continue

                if cost_increase < min_cost_increase:
                    min_cost_increase = cost_increase
                    best_insertion = (vehicle_id, i)
        
        # --- Perform the single best insertion found for this customer ---
        if best_insertion:
            best_vehicle_id, best_insert_idx = best_insertion
            state.routes[best_vehicle_id].nodes.insert(best_insert_idx, customer_id)
            state.unassigned.remove(customer_id)
            
    return state

def best_insertion_repair(state, rng: np.random.RandomState, **kwargs):
    """
    Repairs a solution by inserting unassigned customers using one of three
    probabilistic strategies, as described in the "Best Insertion" algorithm.

    - Variant 1: Inserts customers in a purely random order.
    - Variant 2: Prioritizes inserting truck-only customers first.
    - Variant 3: Prioritizes inserting drone-eligible customers first.
    """
    # --- Probabilistic Strategy Selection ---
    # Weights for each variant (g1, g2, g3), must sum to 1.0
    G1_RANDOM = 0.4
    G2_TRUCK_FIRST = 0.3
    # G3_DRONE_FIRST = 0.3 (implicitly the rest)

    # --- Step 1: Classify unassigned customers ---
    drone_eligible = []
    truck_only = []
    for cust_id in state.unassigned:
        # Check if a drone can fly from the depot to the customer
        if "D" in state.matrix.get(('depot', cust_id), {}):
            drone_eligible.append(cust_id)
        else:
            truck_only.append(cust_id)
            
    # --- Step 2: Build the prioritized insertion list based on the chosen strategy ---
    rand = rng.random()
    
    if rand < G1_RANDOM:
        # VARIANT 1: Randomly shuffle all unassigned customers
        ordered_customers_to_insert = state.unassigned[:]
        rng.shuffle(ordered_customers_to_insert)
    elif rand < G1_RANDOM + G2_TRUCK_FIRST:
        # VARIANT 2: Insert truck-only customers first
        rng.shuffle(truck_only)
        rng.shuffle(drone_eligible)
        ordered_customers_to_insert = truck_only + drone_eligible
    else:
        # VARIANT 3: Insert drone-eligible customers first
        rng.shuffle(drone_eligible)
        rng.shuffle(truck_only)
        ordered_customers_to_insert = drone_eligible + truck_only

    # --- Step 3: Iteratively insert customers using the generated order ---
    # This logic is the same as your original constrained_greedy_repair
    for customer_id in ordered_customers_to_insert:
        customer_node = state.nodes_map[customer_id]
        best_insertion = None
        min_cost_increase = float('inf')

        for vehicle_id, route_state in state.routes.items():
            vehicle = state.vehicles_map[vehicle_id]
            if 'Drone' in vehicle_id: v_type = 'D'
            elif 'F_Truck' in vehicle_id: v_type = 'F'
            else: v_type = 'E'

            # CONSTRAINT 1: Vehicle-Node Compatibility
            if v_type == 'D' and customer_id not in drone_eligible:
                continue

            # CONSTRAINT 2: Vehicle Capacity
            current_weight = sum(state.nodes_map[node_id]['weight'] for node_id in route_state.nodes)
            current_volume = sum(state.nodes_map[node_id]['volume'] for node_id in route_state.nodes)
            if (current_weight + customer_node['weight'] > vehicle['capacity_kg'] or
                current_volume + customer_node['volume'] > vehicle['capacity_cm3']):
                continue

            # FIND BEST INSERTION POINT (if all constraints pass)
            full_route = [depot_id] + route_state.nodes + [depot_id]
            for i in range(len(full_route) - 1):
                prev_node, next_node = full_route[i], full_route[i+1]

                cost_increase = (state.matrix.get((prev_node, customer_id), {}).get(v_type, (0,0,float('inf')))[2]
                               + state.matrix.get((customer_id, next_node), {}).get(v_type, (0,0,float('inf')))[2]
                               - state.matrix.get((prev_node, next_node), {}).get(v_type, (0,0,float('inf')))[2])

                # Check vehicle range constraint
                new_route = full_route[:i+1] + [customer_id] + full_route[i+1:]
                new_total_dist = sum(state.matrix.get((new_route[j], new_route[j+1]), {}).get(v_type, (0,0,0))[0] for j in range(len(new_route)-1))
                if 'range_km' in vehicle and new_total_dist > vehicle['range_km']:
                    continue

                if cost_increase < min_cost_increase:
                    min_cost_increase = cost_increase
                    best_insertion = (vehicle_id, i)

        # PERFORM BEST INSERTION for this customer
        if best_insertion:
            vehicle_id, insert_idx = best_insertion
            state.routes[vehicle_id].nodes.insert(insert_idx, customer_id)
            state.unassigned.remove(customer_id)

    # Rebuild edges for any routes that were modified (good practice)
    for route_state in state.routes.values():
        full_route = [depot_id] + route_state.nodes + [depot_id]
        route_state.edges = {start: end for start, end in zip(full_route, full_route[1:])}

    return state

def regret_insertion_repair(state, rng: np.random.RandomState, **kwargs):
    """
    Repairs a solution using a 2-regret heuristic.
    
    In each step, it evaluates all unassigned customers and inserts the one with the
    highest "regret." Regret is the cost difference between the customer's second-best
    insertion and its absolute best insertion. This prioritizes customers that have
    few good insertion options.
    """
    while state.unassigned:
        # This list will hold the best and second-best options for each customer
        customer_options = []

        # Step 1: For each unassigned customer, find all its possible insertion costs
        for customer_id in state.unassigned:
            customer_node = state.nodes_map[customer_id]
            insertion_costs = []

            for vehicle_id, route_state in state.routes.items():
                vehicle = state.vehicles_map[vehicle_id]
                if 'Drone' in vehicle_id: v_type = 'D'
                elif 'F_Truck' in vehicle_id: v_type = 'F'
                else: v_type = 'E'

                # --- Feasibility Constraints ---
                is_drone_eligible = "D" in state.matrix.get(('depot', customer_id), {})
                if v_type == 'D' and not is_drone_eligible:
                    continue

                current_weight = sum(state.nodes_map[node_id]['weight'] for node_id in route_state.nodes)
                current_volume = sum(state.nodes_map[node_id]['volume'] for node_id in route_state.nodes)
                if (current_weight + customer_node['weight'] > vehicle['capacity_kg'] or
                    current_volume + customer_node['volume'] > vehicle['capacity_cm3']):
                    continue

                # --- Calculate cost for every possible insertion point in this route ---
                full_route = [depot_id] + route_state.nodes + [depot_id]
                for i in range(len(full_route) - 1):
                    prev_node, next_node = full_route[i], full_route[i+1]

                    cost_increase = (state.matrix.get((prev_node, customer_id), {}).get(v_type, (0,0,float('inf')))[2]
                                   + state.matrix.get((customer_id, next_node), {}).get(v_type, (0,0,float('inf')))[2]
                                   - state.matrix.get((prev_node, next_node), {}).get(v_type, (0,0,float('inf')))[2])

                    # Check vehicle range constraint
                    new_route = full_route[:i+1] + [customer_id] + full_route[i+1:]
                    new_total_dist = sum(state.matrix.get((new_route[j], new_route[j+1]), {}).get(v_type, (0,0,0))[0] for j in range(len(new_route)-1))
                    if 'range_km' in vehicle and new_total_dist > vehicle['range_km']:
                        continue

                    # Store all valid options for this customer
                    insertion_costs.append({'cost': cost_increase, 'vehicle_id': vehicle_id, 'idx': i})
            
            # --- After checking all routes, calculate regret for this customer ---
            if not insertion_costs:
                continue

            insertion_costs.sort(key=lambda x: x['cost'])
            best_insertion = insertion_costs[0]
            
            # Calculate regret: difference between 2nd best and best cost
            if len(insertion_costs) > 1:
                second_best_insertion = insertion_costs[1]
                regret = second_best_insertion['cost'] - best_insertion['cost']
            else:
                # If there's only one option, the regret is very high
                regret = float('inf') 

            customer_options.append({'regret': regret, 'customer_id': customer_id, 'best_insertion': best_insertion})

        # Step 2: If no customers can be inserted, stop
        if not customer_options:
            break

        # Step 3: Choose the customer with the highest regret to insert next
        customer_options.sort(key=lambda x: x['regret'], reverse=True)
        to_insert = customer_options[0]
        
        # Step 4: Perform the insertion for the chosen customer
        customer_id_to_insert = to_insert['customer_id']
        best_insertion_details = to_insert['best_insertion']
        
        vehicle_id = best_insertion_details['vehicle_id']
        insert_idx = best_insertion_details['idx']
        
        state.routes[vehicle_id].nodes.insert(insert_idx, customer_id_to_insert)
        state.unassigned.remove(customer_id_to_insert)
        
    return state
