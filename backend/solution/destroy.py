import numpy as np

def random_removal(state, rng: np.random.RandomState, **kwargs):
    """
    Randomly removes customers from routes. Correctly iterates over the 
    routes dictionary.
    """
    destroyed_state = state.copy()
    
    all_pairs = [(vehicle_id, customer)
                 for vehicle_id, route_state in destroyed_state.routes.items()
                 for customer in route_state.nodes if customer != 'depot']

    if not all_pairs:
        return destroyed_state

    percentage = 0.25 
    k = int(len(all_pairs) * percentage)
    k = max(1, k)

    indices = rng.choice(range(len(all_pairs)), size=k, replace=False)
    
    modified_vehicles = set()

    for idx in indices:
        vehicle_id, customer = all_pairs[idx]
        destroyed_state.routes[vehicle_id].nodes.remove(customer)
        destroyed_state.unassigned.append(customer)
        modified_vehicles.add(vehicle_id)
        
    for vehicle_id in modified_vehicles:
        destroyed_state.routes[vehicle_id].edges.clear()

    return destroyed_state

def cluster_removal(state, rng: np.random.RandomState, **kwargs):
    """
    Removes a cluster of customers based on geographic proximity.
    
    It works by:
    1. Selecting a random customer to act as the "center" of the cluster.
    2. Finding all other customers in the solution.
    3. Calculating the distance from the center to all other customers using the matrix.
    4. Removing the center customer plus a percentage of the closest customers.
    """
    destroyed_state = state.copy()
    
    # Create a flat list of all customers currently assigned to routes
    all_customers = [
        customer
        for route_state in destroyed_state.routes.values()
        for customer in route_state.nodes
    ]
    
    # If there are no customers to remove, return the current state
    if not all_customers:
        return destroyed_state

    # 1. Randomly select a customer to be the center of the cluster
    center_customer = rng.choice(all_customers)
    
    # 2. Calculate the distance from the center to all other customers
    # We create a list of (distance, customer_id) tuples
    customer_distances = []
    for customer in all_customers:
        if customer == center_customer:
            continue
        
        # We'll use the 'E' truck distance as a consistent proxy for road distance.
        # .get() is used for safe lookups in case a path or vehicle type doesn't exist.
        distance = state.matrix.get((center_customer, customer), {}).get('E', (float('inf'), 0, 0))[0]
        customer_distances.append((distance, customer))
        
    # 3. Sort customers by their distance to the center (closest first)
    customer_distances.sort()
    
    # 4. Determine how many customers to remove (β)
    # Using 25% to be consistent with your random_removal operator
    percentage = 0.25
    beta = max(1, int(len(all_customers) * percentage))
    
    # 5. Build the final list of customers to remove
    # This list includes the center customer and the (β-1) closest neighbors
    customers_to_remove = [center_customer]
    for dist, customer in customer_distances[:beta - 1]:
        customers_to_remove.append(customer)
        
    # 6. Perform the removal from the solution state
    # Create a quick lookup map to find which vehicle serves which customer
    customer_to_vehicle_map = {
        cust: veh_id
        for veh_id, route in destroyed_state.routes.items()
        for cust in route.nodes
    }
    
    modified_vehicles = set()
    for customer in customers_to_remove:
        vehicle_id = customer_to_vehicle_map.get(customer)
        if vehicle_id:
            # Remove from the route's node list
            destroyed_state.routes[vehicle_id].nodes.remove(customer)
            # Add to the list of unassigned customers
            destroyed_state.unassigned.append(customer)
            modified_vehicles.add(vehicle_id)

    # 7. Clear the edges of any routes that were changed (good practice)
    for vehicle_id in modified_vehicles:
        destroyed_state.routes[vehicle_id].edges.clear()
        
    return destroyed_state

def worst_removal(state, rng: np.random.RandomState, **kwargs):
    """
    Removes customers that contribute the most to the objective function.

    It works by:
    1. Calculating the cost savings for removing each customer from their current route.
       The savings is calculated as: (cost[A->C] + cost[C->B]) - cost[A->B].
    2. Sorting the customers in descending order based on this savings.
    3. Removing a percentage of the "worst" customers (those with the highest savings).
    """
    destroyed_state = state.copy()
    
    customer_savings = []

    # Step 1: Calculate the cost savings for removing each customer
    for vehicle_id, route_state in state.routes.items():
        # Determine the vehicle type for accurate cost lookup
        if 'Drone' in vehicle_id: v_type = 'D'
        elif 'F_Truck' in vehicle_id: v_type = 'F'
        else: v_type = 'E'

        # Pad the route with the depot to correctly calculate savings for the first and last customers
        full_route = ['depot'] + route_state.nodes + ['depot']

        for i in range(1, len(full_route) - 1):
            prev_node = full_route[i - 1]
            customer_id = full_route[i]
            next_node = full_route[i + 1]

            # Cost of the two legs including the customer
            cost_with_customer = (state.matrix.get((prev_node, customer_id), {}).get(v_type, (0,0,0))[2]
                                + state.matrix.get((customer_id, next_node), {}).get(v_type, (0,0,0))[2])

            # Cost of the single leg bypassing the customer
            cost_without_customer = state.matrix.get((prev_node, next_node), {}).get(v_type, (0,0,0))[2]
            
            savings = cost_with_customer - cost_without_customer
            customer_savings.append((savings, customer_id, vehicle_id))

    # Step 2: Sort customers by savings in descending order
    customer_savings.sort(reverse=True)
    
    # Step 3: Determine how many customers to remove
    percentage = 0.25
    num_to_remove = max(1, int(len(customer_savings) * percentage))

    # Step 4: Remove the top "worst" customers
    modified_vehicles = set()
    for savings, customer, vehicle_id in customer_savings[:num_to_remove]:
        # The customer is guaranteed to be in this vehicle's route
        if customer in destroyed_state.routes[vehicle_id].nodes:
            destroyed_state.routes[vehicle_id].nodes.remove(customer)
            destroyed_state.unassigned.append(customer)
            modified_vehicles.add(vehicle_id)

    # Step 5: Clear edges of any routes that were changed
    for vehicle_id in modified_vehicles:
        destroyed_state.routes[vehicle_id].edges.clear()
        
    return destroyed_state

def shaw_removal(state, rng: np.random.RandomState, **kwargs):
    """
    Removes customers that are 'similar' to a randomly selected customer.
    
    Similarity (or relatedness) is based on a weighted score of distance 
    and demand difference, as described by Shaw (1998).
    
    The correlation score is R(i, j) = χd * dij + χq * |qi - qj|.
    A smaller score means the customers are more related.
    """
    destroyed_state = state.copy()
    
    # Operator parameters for normalization (these can be tuned)
    CHI_D = 1.0  # Weight for the distance component
    CHI_Q = 0.5  # Weight for the demand component
    
    # Get a flat list of all customers currently in routes
    all_customers = [
        customer
        for route_state in destroyed_state.routes.values()
        for customer in route_state.nodes
    ]
    
    if not all_customers:
        return destroyed_state

    # 1. Randomly select a starting customer 'i'
    start_customer = rng.choice(all_customers)
    
    # 2. Calculate the relatedness score R(i, j) for all other customers 'j'
    relatedness_scores = []
    start_customer_demand = state.nodes_map[start_customer]['weight']

    for other_customer in all_customers:
        if other_customer == start_customer:
            continue
        
        # Get distance (dij) - using 'E' truck as a consistent proxy
        distance = state.matrix.get((start_customer, other_customer), {}).get('E', (float('inf'), 0, 0))[0]
        
        # Get demand difference |qi - qj|
        other_customer_demand = state.nodes_map[other_customer]['weight']
        demand_diff = abs(start_customer_demand - other_customer_demand)
        
        # Calculate the correlation score
        score = CHI_D * distance + CHI_Q * demand_diff
        relatedness_scores.append((score, other_customer))

    # 3. Sort by score in ascending order (most related first)
    relatedness_scores.sort()
    
    # 4. Determine how many customers to remove
    percentage = 0.25
    num_to_remove = max(1, int(len(all_customers) * percentage))
    
    # 5. Build the final list of customers to remove
    # Includes the start customer plus the (n-1) most related customers
    customers_to_remove = [start_customer]
    for score, customer in relatedness_scores[:num_to_remove - 1]:
        customers_to_remove.append(customer)

    # 6. Perform the removal from the solution state
    customer_to_vehicle_map = {
        cust: veh_id
        for veh_id, route in destroyed_state.routes.items()
        for cust in route.nodes
    }
    
    modified_vehicles = set()
    for customer in customers_to_remove:
        vehicle_id = customer_to_vehicle_map.get(customer)
        if vehicle_id and customer in destroyed_state.routes[vehicle_id].nodes:
            destroyed_state.routes[vehicle_id].nodes.remove(customer)
            destroyed_state.unassigned.append(customer)
            modified_vehicles.add(vehicle_id)

    for vehicle_id in modified_vehicles:
        destroyed_state.routes[vehicle_id].edges.clear()
        
    return destroyed_state

def worst_drone_removal(state, rng: np.random.RandomState, **kwargs):
    """
    Removes drone-served customers that contribute the most to the objective function.
    
    This is a targeted version of the worst_removal operator, focusing only on
    routes handled by drones.
    """
    destroyed_state = state.copy()
    
    customer_savings = []
    v_type = 'D'  # We are only concerned with drone costs

    # Step 1: Calculate savings for removing each customer from DRONE routes only
    for vehicle_id, route_state in state.routes.items():
        # This is the key change: only consider drone routes
        if 'Drone' not in vehicle_id:
            continue

        full_route = ['depot'] + route_state.nodes + ['depot']

        for i in range(1, len(full_route) - 1):
            prev_node = full_route[i - 1]
            customer_id = full_route[i]
            next_node = full_route[i + 1]

            # Cost of legs including the customer
            cost_with_customer = (state.matrix.get((prev_node, customer_id), {}).get(v_type, (0,0,0))[2]
                                + state.matrix.get((customer_id, next_node), {}).get(v_type, (0,0,0))[2])

            # Cost of the leg bypassing the customer
            cost_without_customer = state.matrix.get((prev_node, next_node), {}).get(v_type, (0,0,0))[2]
            
            savings = cost_with_customer - cost_without_customer
            customer_savings.append((savings, customer_id, vehicle_id))

    # If there are no drone customers to remove, return the state
    if not customer_savings:
        return destroyed_state

    # Step 2: Sort drone customers by savings in descending order
    customer_savings.sort(reverse=True)
    
    # Step 3: Determine how many drone customers to remove
    percentage = 0.25  # Remove 25% of the "worst" drone customers
    num_to_remove = max(1, int(len(customer_savings) * percentage))

    # Step 4: Remove the top "worst" drone customers
    for savings, customer, vehicle_id in customer_savings[:num_to_remove]:
        if customer in destroyed_state.routes[vehicle_id].nodes:
            destroyed_state.routes[vehicle_id].nodes.remove(customer)
            destroyed_state.unassigned.append(customer)
        
    return destroyed_state
