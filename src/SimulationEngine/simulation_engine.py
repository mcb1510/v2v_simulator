import simpy
import time
from typing import List, Callable
from .config import CONFIG
from .vehicle import VehicleManager
from .network_simulator import NetworkSimulator

#SimPy for discrete event simulation
class SimulationEngine:
    def __init__(self):
        # SimPy environment
        self.env = simpy.Environment()
        
        # Core components
        self.vehicle_manager = VehicleManager()
        
        self.network_sim: NetworkSimulator = NetworkSimulator()

        # Simulation state
        self.is_running = False
        self.total_bsm_count = 0
        self.total_cwm_count = 0          
        self.collisions_prevented = 0     
        self.simulation_start_time = 0


        
        # Callbacks for external components (Phase 2+)
        self.message_callbacks = []  # Called when messages are generated
        self.update_callbacks = []   # Called each simulation step
    
    # Initialize simulation
    def initialize(self):
        print("Initializing V2V Network Simulator")
        print(f"Timestep: {CONFIG.SIMULATION_TIMESTEP}s")
        print(f"BSM Interval: {CONFIG.BSM_INTERVAL}s")
        
        self.simulation_start_time = time.time()
        
        # Start main simulation process
        self.env.process(self.simulation_loop())
    
    # Main simulation loop - runs continuously
    def simulation_loop(self):
        # Updates all vehicles, handles CWMs and BSMs
        while True:
            current_time = self.env.now
            
            # 1) Update all vehicle physics
            self.vehicle_manager.update_all_vehicles(CONFIG.SIMULATION_TIMESTEP)
            
            # 2) Deliver all messages from the previous
            #    round of broadcasting.
            self.network_sim.deliver_messages(self.vehicle_manager.get_all_vehicles())

            # 3) Process delivered messages and manage
            #    vehicle states/data.
            for vehicle in self.vehicle_manager.get_all_vehicles():
                vehicle.process_messages(self.network_sim)
                vehicle.manage(self.network_sim)

                cwm = self.vehicle_manager.detect_potential_collisions(vehicle)
                if cwm != None:
                    self.total_cwm_count += 1
                    self.collisions_prevented += 1

                    vehicle.send_message(self.network_sim, cwm)
                    # Notify message callbacks
                    for callback in self.message_callbacks:
                        try:
                            callback(vehicle, cwm)
                        except Exception as e:
                            print(f"Error in CWM message callback: {e}")

                if vehicle.should_send_bsm(current_time):
                    bsm = vehicle.generate_bsm(current_time)
                    self.total_bsm_count += 1
                    vehicle.send_message(self.network_sim, bsm)

                    # Notify message callbacks
                    for callback in self.message_callbacks:
                        try:
                            callback(vehicle, bsm)
                        except Exception as e:
                            print(f"Error in message callback: {e}")
         
            # 4) Call external update callbacks (visualization etc.)
            for callback in self.update_callbacks:
                try:
                    callback(current_time)
                except Exception as e:
                    print(f"Error in update callback: {e}")
            
            # 5) Wait for next simulation tick
            yield self.env.timeout(CONFIG.SIMULATION_TIMESTEP)
    
    # Process BSM broadcasts from all vehicles
    def _process_bsm_broadcasts(self, current_time: float):
        # Process Basic Safety Message broadcasts
        for vehicle in self.vehicle_manager.get_all_vehicles():
            if vehicle.should_send_bsm(current_time):
                bsm = vehicle.generate_bsm(current_time)
                self.total_bsm_count += 1
                
                # Notify message callbacks
                for callback in self.message_callbacks:
                    try:
                        callback(vehicle, bsm)
                    except Exception as e:
                        print(f"Error in message callback: {e}")

        # NEW: Process CWM (collision warning) messages based on TTC
       
    def _process_collision_warnings(self, current_time: float):
        """
        Ask VehicleManager to detect dangerous TTC situations
        and send CollisionWarningMessages (CWM) via callbacks.
        """
        warnings = self.vehicle_manager.detect_potential_collisions(current_time)

        for vehicle, cwm in warnings:
            self.total_cwm_count += 1

            # Notify message callbacks (e.g., network simulator, logger, etc.)
            for callback in self.message_callbacks:
                try:
                    callback(vehicle, cwm)
                except Exception as e:
                    print(f"Error in CWM message callback: {e}")


    
    # Spawn new vehicle
    def spawn_vehicle(self, position: tuple, velocity: float = None) -> str:
        if velocity is None:
            velocity = CONFIG.HIGHWAY_SPEED  # Default speed
        vehicle_id = self.vehicle_manager.create_vehicle(position, velocity)
        print(f"Spawned vehicle {vehicle_id} at {position} with velocity {velocity:.1f}m/s")
        return vehicle_id
    
    # Get vehicle by ID
    def get_vehicle(self, vehicle_id: str):
        return self.vehicle_manager.get_vehicle(vehicle_id)
    
    # Get all vehicles
    def get_all_vehicles(self):
        return self.vehicle_manager.get_all_vehicles()
    
    # Add callback for message events
    def add_message_callback(self, callback: Callable):
        self.message_callbacks.append(callback)
    
    # Add callback for simulation updates
    def add_update_callback(self, callback: Callable):
        self.update_callbacks.append(callback)
    
    # Run simulation for specified duration
    def run(self, duration: float):
        print(f"Running simulation for {duration} seconds...")
        self.is_running = True
        
        try:
            self.env.run(until=duration)
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
        finally:
            self.is_running = False
            print("Simulation stopped")
    
    # Get basic simulation statistics
    def get_simulation_stats(self) -> dict:
        return {
            'simulation_time': self.env.now,
            'vehicle_count': self.vehicle_manager.get_vehicle_count(),
            'total_bsm_sent': self.total_bsm_count,
            'bsm_rate': self.total_bsm_count / max(self.env.now, 1),
            'total_cwm_sent': self.total_cwm_count,
            'collisions_prevented': self.collisions_prevented,
            'average_latency': self.network_sim.get_average_latency(),
            'packet_loss': self.network_sim.get_packet_loss()
        }


# Global simulation instance
simulation_engine = SimulationEngine()

