"""
Backend communication module
Handles all API calls to backend server
Place this file in: frontend/gui/backend_handler.py
"""
import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Optional


class BackendHandler:
    """Handles all backend API communication"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    @staticmethod
    async def insert_nodes(customer_nodes: List[Dict], 
                          depot_node: Dict, 
                          vehicle_config: Dict) -> bool:
        """
        Insert nodes to backend database via API
        
        Args:
            customer_nodes: List of customer node dictionaries
            depot_node: Depot node dictionary
            vehicle_config: Dictionary with fleet configuration
                {
                    "electric_trucks": int,
                    "fuel_trucks": int,
                    "drones": int
                }
        
        Returns:
            True if successful, False otherwise
        """
        try:
            nodes_list = []
            
            # Add customer nodes
            for node in customer_nodes:
                nodes_list.append({
                    "node_id": node["node_id"],
                    "weight": node["weight"],
                    "volume": node["volume"],
                    "lon": node["lon"],
                    "lat": node["lat"]
                })
            
            # Add depot node at the beginning
            if depot_node:
                nodes_list.insert(0, {
                    "node_id": depot_node["node_id"],
                    "weight": depot_node["weight"],
                    "volume": depot_node["volume"],
                    "lon": depot_node["lon"],
                    "lat": depot_node["lat"]
                })
            
            # Prepare request data
            nodes_data = {
                "nodes": nodes_list,
                "vehicle_config": vehicle_config
            }
            
            print(f"Inserting {len(nodes_list)} nodes to backend database...")
            
            # Send POST request to backend
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BackendHandler.BASE_URL}/api/nodes/insert",
                    json=nodes_data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=60)  # 60 second timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        nodes_inserted = result.get('nodes_inserted', 0)
                        print(f"✅ Successfully inserted {nodes_inserted} nodes to backend")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to insert nodes: {response.status} - {error_text}")
                        return False
                        
        except aiohttp.ClientError as e:
            print(f"❌ Network error inserting nodes: {e}")
            return False
        except asyncio.TimeoutError:
            print(f"❌ Timeout error inserting nodes")
            return False
        except Exception as e:
            print(f"❌ Error inserting nodes: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    async def fetch_nodes() -> List[Dict]:
        """
        Fetch nodes from backend database
        
        Returns:
            List of node dictionaries
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{BackendHandler.BASE_URL}/api/nodes",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        nodes_data = await response.json()
                        print(f"✅ Fetched {len(nodes_data)} nodes from backend")
                        return nodes_data
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to fetch nodes: {response.status} - {error_text}")
                        return []
        except Exception as e:
            print(f"❌ Error fetching nodes: {e}")
            return []
    
    @staticmethod
    async def trigger_distance_computation() -> bool:
        """
        Trigger distance matrix computation on backend
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Triggering backend distance matrix computation...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BackendHandler.BASE_URL}/api/compute/distances",
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        entries = result.get('entries', 0)
                        print(f"✅ Distance computation completed: {entries} entries")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Distance computation failed: {response.status} - {error_text}")
                        return False
        except aiohttp.ClientError as e:
            print(f"❌ Network error in distance computation: {e}")
            return False
        except asyncio.TimeoutError:
            print(f"❌ Timeout in distance computation")
            return False
        except Exception as e:
            print(f"❌ Error in distance computation: {e}")
            return False
    
    @staticmethod
    async def trigger_vehicle_matrix_computation() -> bool:
        """
        Trigger vehicle matrix computation on backend
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Triggering backend vehicle matrix computation...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BackendHandler.BASE_URL}/api/compute/vehicle_matrix",
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        entries = result.get('entries', 0)
                        print(f"✅ Vehicle matrix computation completed: {entries} entries")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Vehicle matrix computation failed: {response.status} - {error_text}")
                        return False
        except aiohttp.ClientError as e:
            print(f"❌ Network error in vehicle matrix computation: {e}")
            return False
        except asyncio.TimeoutError:
            print(f"❌ Timeout in vehicle matrix computation")
            return False
        except Exception as e:
            print(f"❌ Error in vehicle matrix computation: {e}")
            return False
    
    @staticmethod
    def load_initial_solution(backend_folder_path: str) -> Optional[Dict]:
        """
        Load initial_solution.json from backend folder
        
        Args:
            backend_folder_path: Path to backend folder containing initial_solution.json
        
        Returns:
            Dictionary with solution data or None if failed
        """
        try:
            solution_file = os.path.join(backend_folder_path, 'initial_solution.json')
            
            print(f"Looking for initial_solution.json at: {solution_file}")
            
            if not os.path.exists(solution_file):
                print(f"⚠️  Initial solution file not found at: {solution_file}")
                # Wait a bit longer in case backend is still writing
                import time
                time.sleep(2)
                if not os.path.exists(solution_file):
                    print("⚠️  File still not found after waiting")
                    return None
            
            # Read and parse JSON file
            with open(solution_file, 'r', encoding='utf-8') as f:
                solution = json.load(f)
            
            # Validate solution structure
            if not isinstance(solution, dict):
                print("❌ Invalid solution format: not a dictionary")
                return None
            
            wave_count = len([k for k in solution.keys() if k != 'summary'])
            print(f"✅ Successfully loaded initial solution with {wave_count} waves")
            
            return solution
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON in initial solution: {e}")
            return None
        except FileNotFoundError:
            print(f"❌ Initial solution file not found")
            return None
        except Exception as e:
            print(f"❌ Error loading initial solution file: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def parse_wave_information(initial_solution: Dict) -> List[Dict]:
        """
        Parse wave information from backend solution
        
        Args:
            initial_solution: Dictionary containing backend solution
        
        Returns:
            List of wave dictionaries with structure:
            [
                {
                    'wave_number': str,
                    'drones': List[Dict],
                    'trucks': List[Dict],
                    'total_drones': int,
                    'total_trucks': int
                },
                ...
            ]
        """
        try:
            waves_data = []
            
            # Filter out the 'summary' key - only process actual wave keys
            for wave_key, wave_data in initial_solution.items():
                # Skip the summary key
                if wave_key == 'summary':
                    continue
                
                # Validate wave data structure
                if not isinstance(wave_data, dict):
                    print(f"⚠️  Skipping invalid wave data for {wave_key}")
                    continue
                
                wave_info = {
                    'wave_number': wave_key,
                    'drones': wave_data.get('drones', []),
                    'trucks': wave_data.get('trucks', []),
                    'total_drones': len(wave_data.get('drones', [])),
                    'total_trucks': len(wave_data.get('trucks', []))
                }
                waves_data.append(wave_info)
            
            print(f"✅ Parsed {len(waves_data)} actual waves from backend solution")
            for wave in waves_data:
                print(f"  {wave['wave_number']}: "
                      f"{wave['total_drones']} drones, "
                      f"{wave['total_trucks']} trucks")
            
            return waves_data
            
        except Exception as e:
            print(f"❌ Error parsing wave information: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    async def process_all_computations(customer_nodes: List[Dict], 
                                      depot_node: Dict, 
                                      vehicle_config: Dict) -> Optional[bool]:
        """
        Complete backend processing pipeline
        
        This method:
        1. Inserts nodes to backend
        2. Backend automatically triggers distance and vehicle matrix computations
        3. Backend generates initial solution
        
        Args:
            customer_nodes: List of customer node dictionaries
            depot_node: Depot node dictionary
            vehicle_config: Fleet configuration dictionary
        
        Returns:
            True if successful, None if failed
        """
        try:
            print("\n=== STARTING BACKEND PROCESSING PIPELINE ===")
            
            # Insert nodes (this automatically triggers computations in backend)
            insert_success = await BackendHandler.insert_nodes(
                customer_nodes, 
                depot_node, 
                vehicle_config
            )
            
            if not insert_success:
                print("❌ Node insertion failed - aborting backend processing")
                return None
            
            print("✅ Backend processing completed successfully")
            print("⏳ Waiting for backend to write solution file...")
            
            # Wait for backend to finish writing the solution file
            await asyncio.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"❌ Error in backend processing pipeline: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_backend_status() -> Dict:
        """
        Get backend server status (synchronous check)
        
        Returns:
            Dictionary with status information
        """
        try:
            import requests
            response = requests.get(
                f"{BackendHandler.BASE_URL}/health",
                timeout=5
            )
            if response.status_code == 200:
                return {
                    "status": "online",
                    "message": "Backend server is running"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Backend returned status {response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "offline",
                "message": "Cannot connect to backend server"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error checking backend: {str(e)}"
            }
    
    @staticmethod
    def validate_backend_connection() -> bool:
        """
        Validate that backend is accessible
        
        Returns:
            True if backend is accessible, False otherwise
        """
        status = BackendHandler.get_backend_status()
        is_online = status["status"] == "online"
        
        if is_online:
            print("✅ Backend server is online and accessible")
        else:
            print(f"❌ Backend server issue: {status['message']}")
        
        return is_online
    
    @staticmethod
    async def clear_backend_data() -> bool:
        """
        Clear all data from backend database (useful for testing)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Clearing backend database...")
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{BackendHandler.BASE_URL}/api/nodes/clear",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Backend database cleared: {result.get('message', 'Success')}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to clear backend: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Error clearing backend data: {e}")
            return False
    
    @staticmethod
    async def get_computation_status() -> Dict:
        """
        Get status of backend computations
        
        Returns:
            Dictionary with computation status information
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{BackendHandler.BASE_URL}/api/compute/status",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        return status_data
                    else:
                        return {
                            "status": "error",
                            "message": f"Backend returned {response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def save_solution_locally(solution_data: Dict, output_path: str = "solution_backup.json") -> bool:
        """
        Save solution data to local file as backup
        
        Args:
            solution_data: Solution dictionary to save
            output_path: Path where to save the file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(solution_data, f, indent=2)
            print(f"✅ Solution saved to {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving solution: {e}")
            return False
    
    @staticmethod
    def get_wave_summary(waves_data: List[Dict]) -> Dict:
        """
        Get summary statistics from wave data
        
        Args:
            waves_data: List of wave dictionaries
        
        Returns:
            Dictionary with summary statistics
        """
        if not waves_data:
            return {
                "total_waves": 0,
                "total_vehicles": 0,
                "total_drones": 0,
                "total_trucks": 0
            }
        
        total_drones = sum(wave['total_drones'] for wave in waves_data)
        total_trucks = sum(wave['total_trucks'] for wave in waves_data)
        
        return {
            "total_waves": len(waves_data),
            "total_vehicles": total_drones + total_trucks,
            "total_drones": total_drones,
            "total_trucks": total_trucks,
            "vehicles_per_wave": (total_drones + total_trucks) / len(waves_data) if waves_data else 0
        }
    
    @staticmethod
    async def export_solution_to_backend(solution_data: Dict) -> bool:
        """
        Export solution data back to backend (for modifications)
        
        Args:
            solution_data: Modified solution dictionary
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Exporting solution to backend...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BackendHandler.BASE_URL}/api/solution/import",
                    json=solution_data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Solution exported: {result.get('message', 'Success')}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to export solution: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Error exporting solution: {e}")
            return False


# Helper functions for common operations
async def quick_backend_check() -> bool:
    """
    Quick check if backend is accessible
    
    Returns:
        True if backend is online, False otherwise
    """
    return BackendHandler.validate_backend_connection()


async def initialize_backend_with_data(customer_nodes: List[Dict], 
                                      depot_node: Dict,
                                      electric_trucks: int = 2,
                                      fuel_trucks: int = 1,
                                      drones: int = 3) -> Optional[Dict]:
    """
    Complete initialization: insert nodes and get solution
    
    Args:
        customer_nodes: List of customer nodes
        depot_node: Depot node
        electric_trucks: Number of electric trucks
        fuel_trucks: Number of fuel trucks
        drones: Number of drones
    
    Returns:
        Dictionary with solution data or None if failed
    """
    vehicle_config = {
        "electric_trucks": electric_trucks,
        "fuel_trucks": fuel_trucks,
        "drones": drones
    }
    
    # Process computations
    success = await BackendHandler.process_all_computations(
        customer_nodes,
        depot_node,
        vehicle_config
    )
    
    if not success:
        print("❌ Backend initialization failed")
        return None
    
    # Get backend folder path
    current_file = os.path.abspath(__file__)
    frontend_gui_dir = os.path.dirname(current_file)
    frontend_dir = os.path.dirname(frontend_gui_dir)
    project_root = os.path.dirname(frontend_dir)
    backend_folder = os.path.join(project_root, 'backend')
    
    # Load solution
    solution = BackendHandler.load_initial_solution(backend_folder)
    
    if solution:
        print("✅ Backend initialization complete with solution")
        return solution
    else:
        print("⚠️  Backend initialized but no solution available yet")
        return None


# Example usage functions
def example_usage():
    """
    Example usage of BackendHandler
    """
    import asyncio
    
    async def main():
        # Check backend status
        print("=== Checking Backend Status ===")
        status = BackendHandler.get_backend_status()
        print(f"Status: {status}")
        
        # Example customer nodes
        customer_nodes = [
            {
                "node_id": "cust_1",
                "weight": 2.5,
                "volume": 5000,
                "lon": 77.5946,
                "lat": 12.9716
            },
            {
                "node_id": "cust_2",
                "weight": 150.0,
                "volume": 300000,
                "lon": 77.6046,
                "lat": 12.9816
            }
        ]
        
        depot_node = {
            "node_id": "depot",
            "weight": 0,
            "volume": 0,
            "lon": 77.5846,
            "lat": 12.9616
        }
        
        vehicle_config = {
            "electric_trucks": 2,
            "fuel_trucks": 1,
            "drones": 3
        }
        
        # Process all computations
        print("\n=== Processing Backend Computations ===")
        success = await BackendHandler.process_all_computations(
            customer_nodes,
            depot_node,
            vehicle_config
        )
        
        if success:
            print("\n=== Loading Solution ===")
            # Assuming backend folder is at ../../backend
            backend_folder = "../backend"
            solution = BackendHandler.load_initial_solution(backend_folder)
            
            if solution:
                waves = BackendHandler.parse_wave_information(solution)
                summary = BackendHandler.get_wave_summary(waves)
                print(f"\nSummary: {summary}")
        else:
            print("Backend processing failed")
    
    # Run async main
    asyncio.run(main())


if __name__ == "__main__":
    print("Backend Handler Module")
    print("=" * 50)
    print("This module handles all backend API communication")
    print("\nAvailable functions:")
    print("  - insert_nodes()")
    print("  - fetch_nodes()")
    print("  - trigger_distance_computation()")
    print("  - trigger_vehicle_matrix_computation()")
    print("  - load_initial_solution()")
    print("  - parse_wave_information()")
    print("  - process_all_computations()")
    print("  - get_backend_status()")
    print("  - validate_backend_connection()")
    print("\nRun example_usage() for a demonstration")