import numpy as np
import time
from typing import cast, Dict
from .config import CONFIG
from .message import create_bsm, create_cwm, MessageType, V2VMessage, BasicSafetyMessage, CollisionWarningMessage
from .protocol import Protocol

class VehicleState:
    def __init__(self, position: tuple, velocity: float, acceleration: float, heading: 
                 float, length: int, width: int):
        self.timestamp: float = time.time()

        self.position = np.array(position, dtype=float)
        self.velocity: float = velocity
        self.acceleration: float = acceleration
        self.heading = heading

        self.length = length
        self.width = width

class Vehicle:    
    def __init__(self, vehicle_id: str, initial_position: tuple, initial_velocity: float):
        # ID
        self.vehicle_id = vehicle_id
        
        # Physical state
        self.position = np.array(initial_position, dtype=float)  # [x, y] meters
        self.velocity = float(initial_velocity)                   # m/s
        self.acceleration = 0.0                                   # m/s²
        self.heading = 0.0                                        # radians (0 = east)

        # Protocol for sending and receiving messages.
        self.protocol = Protocol()

        # Map of Vehicle ID to Vehicle State
        self.vehicle_map: Dict[str, VehicleState] = {}
        
        # Vehicle properties
        self.length = CONFIG.VEHICLE_LENGTH
        self.width = CONFIG.VEHICLE_WIDTH
        
        # Control state
        self.target_velocity = initial_velocity

        # Emergency state
        self.emergency_braking = False
        
        # Message timing
        self.last_bsm_time = 0.0
        
        # Simple path: straight line movement
        self.direction = np.array([1.0, 0.0])  # Moving east (positive x)
    
    #Update vehicle physics
    def update_physics(self, dt: float):
        if self.emergency_braking:
            # In emergency mode, always brake as hard as possible
            self.acceleration = -CONFIG.MAX_DECELERATION
        else:
            # Simple cruise control - maintain target velocity
            velocity_error = self.target_velocity - self.velocity
            desired_acceleration = velocity_error * 2.0  # Proportional control

            # Apply acceleration limits
            self.acceleration = np.clip(
                desired_acceleration,
                -CONFIG.MAX_DECELERATION,
                CONFIG.MAX_ACCELERATION
            )

        # Update velocity
        self.velocity += self.acceleration * dt
        self.velocity = max(0.0, self.velocity)  # Cannot go backwards

        # Update position (straight line motion)
        velocity_vector = self.direction * self.velocity
        self.position += velocity_vector * dt

    
    #Check if vehicle should send BSM (every 100ms)
    def should_send_bsm(self, current_time: float) -> bool:
        return (current_time - self.last_bsm_time) >= CONFIG.BSM_INTERVAL
    
    #Generate Basic Safety Message
    def generate_bsm(self, current_time: float):
        self.last_bsm_time = current_time
        return create_bsm(self)
    
    def send_message(self, network_sim, message: V2VMessage):
        self.protocol.send(network_sim, self, message)

    def receive_message(self, message: V2VMessage, message_hash: bytes):
        self.protocol.receive(self, message, message_hash)

    def process_messages(self, network_sim):
        message: V2VMessage = self.protocol.process(network_sim, self)
        while message != None:
            if message.message_type == MessageType.BSM:
                bsm = cast(BasicSafetyMessage, message)
                self.vehicle_map[bsm.vehicle_id] = VehicleState((bsm.position_x, bsm.position_y), 
                                                                bsm.velocity, bsm.acceleration, 
                                                                bsm.heading, bsm.length, bsm.width)
            elif message.message_type == MessageType.CWM:
                cwm = cast(CollisionWarningMessage, message)
                # There are many things that can be done if a CWM
                # is received. For now we assume that the sender
                # actually tries to prevent the collision.

            message = self.protocol.process(network_sim, self)
    
    def manage(self, network_sim):

        # Manage vehicle state/data. 

        self.protocol.manage(network_sim, self)

        # Prune vehicles in the map that we haven't received
        # a message from for a while.
        for vehicle_id, vehicle_state in list(self.vehicle_map.items()):
            if (time.time() - vehicle_state.timestamp) > CONFIG.CONNECTION_TIME:
                del self.vehicle_map[vehicle_id]


    def get_vehicle_map(self) -> Dict[str, VehicleState]:
        return self.vehicle_map

    #Set target velocity for cruise control
    def set_target_velocity(self, velocity: float):
        self.target_velocity = max(0.0, velocity)
    
    #Get vehicle state as dictionary for logging/display
    def get_state_dict(self) -> dict:
        return {
            'id': self.vehicle_id,
            'position': f"({self.position[0]:.1f}, {self.position[1]:.1f})",
            'velocity': f"{self.velocity:.1f}",
            'acceleration': f"{self.acceleration:.1f}",
            'target_vel': f"{self.target_velocity:.1f}"
        }
    
    #Activate emergency braking for this vehicle
    def activate_emergency_braking(self):
        """
        Put the vehicle into emergency braking mode.
        It will try to slow down as fast as allowed.
        """
        self.emergency_braking = True
        # In an emergency, we want to stop as soon as possible
        self.target_velocity = 0.0
        
    def compute_ttc(self, front_vehicle: "VehicleState") -> float | None:
        """
        Compute Time-To-Collision (TTC) with a vehicle in front.
        Assumes straight-line motion along +x direction.
        Returns:
            TTC in seconds if a collision is possible,
            None if no collision is expected.
        """

        # Compute TTC of two vehicles, factoring in acceleration,
        # velocity, and current positions. Solves for t in the 
        # kinematic equation: x + vt + 0.5at^2.
        # x: position
        # v: velocity
        # a: acceleration
        # t: time

        # Compute distance from the front bumper of the rear vehicle
        # to the rear bumper of the front vehicle.
        bumper_to_bumper_distance = (front_vehicle.position[0] - (front_vehicle.length / 2)) - (self.position[0] + (self.length / 2))

        coeff = [(front_vehicle.acceleration - self.acceleration) / 2, 
               (front_vehicle.velocity - self.velocity), 
               bumper_to_bumper_distance]
        
        roots = np.roots(coeff)

        # Filter for roots that are positive and finite.
        time = roots[(roots > 0) & np.isfinite(roots)]
        if (len(time) == 0):
            return None

        return time[0]


    def __str__(self):
        return f"Vehicle({self.vehicle_id}) pos=({self.position[0]:.1f},{self.position[1]:.1f}) vel={self.velocity:.1f}m/s"

#Manages multiple vehicles in simulation
class VehicleManager:
    def __init__(self):
        self.vehicles = {}  # vehicle_id -> Vehicle
        self.next_id = 1
    
    #Create new vehicle and return its ID
    def create_vehicle(self, position: tuple, velocity: float) -> str: 
        vehicle_id = f"V{self.next_id:03d}"
        self.next_id += 1
        vehicle = Vehicle(vehicle_id, position, velocity)
        self.vehicles[vehicle_id] = vehicle
        return vehicle_id
    
    #Get vehicle by ID
    def get_vehicle(self, vehicle_id: str) -> Vehicle:
        return self.vehicles.get(vehicle_id)
   
    #Get list of all vehicles
    def get_all_vehicles(self) -> list:
        return list(self.vehicles.values())
    
    #Update physics for all vehicles
    def update_all_vehicles(self, dt: float):
        for vehicle in self.vehicles.values():
            vehicle.update_physics(dt)

    #Get total number of vehicles
    def get_vehicle_count(self) -> int:
        return len(self.vehicles)
    
    # NEW: Detect potential rear-end collisions and generate CWMs
    def detect_potential_collisions(self, vehicle: "Vehicle") -> CollisionWarningMessage | None:
        vehicle_map_sorted = sorted(vehicle.get_vehicle_map().items(), key=lambda v: v[1].position[0])

        for vehicle_id, vehicle_state in vehicle_map_sorted:

            # Only check vehicles in front for our simulation.
            if vehicle_state.position[0] <= vehicle.position[0]:
                continue

            # Check if the vehicle in front is in the same lane.
            rear_right = (vehicle.position[1] - (vehicle.width / 2))
            rear_left = (vehicle.position[1] + (vehicle.width / 2))
            
            front_right = (vehicle_state.position[1] - (vehicle_state.width / 2))
            front_left = (vehicle_state.position[1] + (vehicle_state.width / 2))
            if (rear_right > front_left) or (rear_left < front_right):
                continue

            ttc = vehicle.compute_ttc(vehicle_state)

            if ttc == None:
                continue

            # If TTC is below our safety threshold, we create a CWM
            if ttc < CONFIG.COLLISION_TIME_THRESHOLD:
                # Activate emergency braking for the rear vehicle
                vehicle.activate_emergency_braking()

                return create_cwm(vehicle, 
                                  vehicle.protocol.get_seq_num(vehicle_id), 
                                  "rear_end_risk", vehicle_id, ttc)
            
        return None
