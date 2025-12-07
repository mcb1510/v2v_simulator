import time
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

class MessageType(Enum):
    ACK = "acknowledge_message"
    BSM = "basic_safety_message"
    CWM = "collision_warning_message"

# Message priority levels
class Priority(Enum):
    NORMAL = 1      # ACK/BSM messages
    EMERGENCY = 0   # CWM messages (higher priority)

# Vehicle-to-Vehicle Message (V2V) - Base for other messages
@dataclass
class V2VMessage:
    message_type: MessageType
    priority: Priority
    vehicle_id: str
    timestamp: float

    def __lt__(self, other: "V2VMessage"):
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp

    def to_json(self) -> str:
        """
        Converts the dataclass instance to a JSON string.
        Handles nested Enums by converting them to their values.
        """
        return json.dumps(
            asdict(self), 
            default=lambda o: o.value if isinstance(o, Enum) else str(o)
        )

# Basic Safety Message (BSM) - broadcast every 100ms
@dataclass
class BasicSafetyMessage(V2VMessage):
    position_x: float
    position_y: float
    velocity: float
    heading: float
    acceleration: float

    length: int 
    width: int

    message_type: MessageType = field(init=False)
    priority: Priority = field(init=False)
    
    def __post_init__(self):
        self.message_type = MessageType.BSM
        self.priority = Priority.NORMAL

@dataclass  
class CollisionWarningMessage(V2VMessage):
    """
    Collision Warning Message (CWM) - emergency messages
    Phase 1: Structure only, implementation in Phase 3
    """
    sequence_number: int
    warning_type: str
    target_vehicle_id: str
    time_to_collision: float
    
    message_type: MessageType = field(init=False)
    priority: Priority = field(init=False)

    def __post_init__(self):
        self.message_type = MessageType.CWM
        self.priority = Priority.EMERGENCY

@dataclass
class AcknowledgementMessage(V2VMessage):
    sequence_number: int
    target_vehicle_id: str

    message_type: MessageType = field(init=False)
    priority: Priority = field(init=False)

    def __post_init__(self):
        self.message_type = MessageType.ACK
        self.priority = Priority.NORMAL

def create_bsm(vehicle) -> BasicSafetyMessage:
    """Factory function to create BSM from vehicle state"""
    return BasicSafetyMessage(
        vehicle_id=vehicle.vehicle_id,
        timestamp=time.time(),
        position_x=vehicle.position[0],
        position_y=vehicle.position[1], 
        velocity=vehicle.velocity,
        heading=vehicle.heading,
        acceleration=vehicle.acceleration,
        length=vehicle.length,
        width=vehicle.width
    )


def create_cwm(vehicle, sequence_number: int, warning_type: str, target_vehicle_id: str, time_to_collision: float) -> CollisionWarningMessage:
    """Function to create a Collision Warning Message (CWM).

    Args:
        vehicle: source vehicle object (must have `vehicle_id`).
        warning_type: short string describing the warning (e.g., 'rear_collision').
        target_vehicle_id: id of the target vehicle involved.
        time_to_collision: estimated time (seconds) until collision.

    Returns:
        CollisionWarningMessage populated with current timestamp and provided fields.
    """
    return CollisionWarningMessage(
        vehicle_id=vehicle.vehicle_id,
        timestamp=time.time(),
        sequence_number=sequence_number,
        warning_type=warning_type,
        target_vehicle_id=target_vehicle_id,
        time_to_collision=time_to_collision,
    )

def create_ack(vehicle, sequence_number: int, target_vehicle_id: str):
    """Function to create an Acknowledgement Message (ACK).

    Args:
        vehicle: source vehicle object (must have `vehicle_id`).
        target_vehicle_id: id of the target vehicle involved.

    Returns:
        AcknowledgementMessage populated with current timestamp and provided fields.
    """

    return AcknowledgementMessage(
        vehicle_id=vehicle.vehicle_id,
        timestamp=time.time(),
        sequence_number=sequence_number,
        target_vehicle_id=target_vehicle_id,
    )
