from typing import Dict, Tuple
from .config import CONFIG
from .message import V2VMessage
import math
import random
import time

class NetworkSimulator:
    def __init__(self):
        self.all_messages: Dict[bytes, tuple] = {}
        self.lost_packets: int = 0
        self.total_packets: int = 0
        self.total_latency: float = 0.0

    def get_average_latency(self) -> float:
        if self.total_packets == 0:
            return 0.0
        return self.total_latency / self.total_packets
    
    def get_packet_loss(self) -> float:
        if self.total_packets == 0:
            return 0.0
        return self.lost_packets / self.total_packets

    def broadcast_message(self, send_vehicle, message: V2VMessage, message_hash: bytes) -> None:
        self.total_packets += 1

        # Randomly drop packets based on the configured %
        # in the config to simulate real packet loss.
        if (random.randint(1, 100) / 100) <= CONFIG.PACKET_LOSS:
            self.lost_packets += 1
            return
        
        self.all_messages[message_hash] = (send_vehicle, message)

    def deliver_messages(self, all_vehicles: list) -> None:
        
        # Deliber each message.
        for message_hash, value in list(self.all_messages.items()):
            send_vehicle = value[0]
            message: V2VMessage = value[1]

            # Model latency by taking in to account the time it
            # took to process (i.e., actually deliver the message).
            # I'm not sure if we should add additional latency logic.
            self.total_latency += (time.time() - message.timestamp)

            for vehicle in all_vehicles:
                if vehicle is send_vehicle:
                    continue

                # Only vehicles in range should receive
                # the message broadcast.
                if not in_range(vehicle, send_vehicle):
                    continue

                vehicle.receive_message(message, message_hash)

            # Remove the message as it has been delivered.
            del self.all_messages[message_hash]

def in_range(source_vehicle, dest_vehicle) -> bool:

    # Uses Pythagorean's Theorem to calculate
    # the distance from the source vehicle to
    # the destination vehicle and checks if the
    # destination vehicle is within the range.

    x_dist = dest_vehicle.position[0] - source_vehicle.position[0]
    y_dist = dest_vehicle.position[1] - source_vehicle.position[1]
    distance = math.sqrt(x_dist**2 + y_dist**2)
    if distance > CONFIG.COMMUNICATION_RANGE:
        return False
    
    return True
