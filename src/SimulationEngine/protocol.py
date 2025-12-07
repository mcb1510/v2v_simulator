import json
import hashlib
import time
from collections import deque
from queue import PriorityQueue, Empty
from typing import cast, Dict
from .config import CONFIG
from .message import V2VMessage, CollisionWarningMessage, AcknowledgementMessage, create_ack, MessageType
from .network_simulator import NetworkSimulator

class CWMConnection:
    def __init__(self, send_seq_num: int, recv_seq_num: int):
        self.cwms = deque()                     # All CWMs awaiting transmission to the vehicle.
        self.transmit_time: float = 0.0         # The time that a CWM was last transmitted.
        self.last_use: float = 0.0              # The time that this connection was last used.
        self.send_seq_num: int = send_seq_num   # The expected sequence number for acknowledgement
                                                # messages sent to the sender of the CWM.
        self.recv_seq_num: int = recv_seq_num   # The expected sequence number for CWM
                                                # messages sent to the receiver.

    def add_cwm(self, cwm: CollisionWarningMessage) -> None:
        self.cwms.append(cwm)

    def next_cwm(self) -> CollisionWarningMessage:
        return self.cwms.popleft()

    def inc_send_seq_num(self) -> None:
        self.send_seq_num += 1
    
    def inc_recv_seq_num(self) -> None:
        self.recv_seq_num += 1
    
# A class for representing the V2V protocol.
class Protocol:
    def __init__(self):
        # Map of Vehicle ID -> CWM Connection
        self.outgoing_cwms: Dict[str, CWMConnection] = {}   # All CWM connections.
        self.incoming_messages = PriorityQueue()            # All incoming messages,
                                                            # with higher priority 
                                                            # messages first.

    def get_seq_num(self, target_vehicle_id: str) -> int:
        cwm_connection: CWMConnection = self.outgoing_cwms.get(target_vehicle_id)
        if cwm_connection == None:
            return 0
        
        return cwm_connection.send_seq_num

    def send(self, network_sim: NetworkSimulator, vehicle, message: V2VMessage) -> None:
        message_hash = get_message_hash(message)

        # Put CWMs into a dictionary so that they can be
        # retransmitted if they aren't acknowledged.
        if message.message_type == MessageType.CWM:
            cwm = cast(CollisionWarningMessage, message)
            cwm_connection: CWMConnection = self.outgoing_cwms.get(cwm.target_vehicle_id)
            if cwm_connection == None:
                cwm_connection = CWMConnection(0, 0)
                self.outgoing_cwms[cwm.target_vehicle_id] = cwm_connection
            
            cwm_connection.last_use = time.time()
            cwm_connection.add_cwm(cwm)

            # There is already an outgoing CWM for this
            # vehicle. We need to just wait for that CWM
            # to be acknowledged before we send this one.
            if len(cwm_connection.cwms) > 1:
                return
            
            cwm_connection.transmit_time = cwm_connection.last_use

        message.timestamp = time.time()
        network_sim.broadcast_message(vehicle, message, message_hash)

    def receive(self, vehicle, message: V2VMessage, message_hash: bytes) -> None:

        # Check if we are the intended vehicle to
        # receive the message.
        if hasattr(message, 'target_vehicle_id'):
            if vehicle.vehicle_id != message.target_vehicle_id:
                return
    
        # Verify the messages generate the same
        # hash (they weren't modified). Note: In
        # a real situation, the hash itself could
        # also be modified to reflect the updates
        # if there were a malicious actor. Further
        # cryptographic measures would be needed for
        # better security, such as digital signing.
        second_message_hash = get_message_hash(message)
        if second_message_hash != message_hash:
            return
        
        self.incoming_messages.put(message)

    def process(self, network_sim: NetworkSimulator, vehicle) -> V2VMessage | None:

        # Processes all messages in the incoming message
        # queue until a processable message is found, or
        # until the queue is empty.

        try:
            while True:
                message = self.incoming_messages.get(False)

                if isinstance(message, CollisionWarningMessage):
                    cwm = cast(CollisionWarningMessage, message)

                    cwm_connection: CWMConnection = self.outgoing_cwms.get(cwm.vehicle_id)
                    if cwm_connection == None:
                        cwm_connection = CWMConnection(0, 0)
                        self.outgoing_cwms[cwm.vehicle_id] = cwm_connection
                    
                    cwm_connection.last_use = time.time()

                    # Discard CWMs that arrived out-of-order.
                    if cwm.sequence_number > cwm_connection.recv_seq_num:
                        continue

                    # All CWMs <= the expected sequence number are
                    # acknowledged. This effectively allows for ACKs
                    # to be retransmitted in case they were dropped.
                    self.send(network_sim, vehicle, create_ack(vehicle, cwm.sequence_number, cwm.vehicle_id))

                    # Only process CWMs that are what we expect to receive.
                    if cwm.sequence_number == cwm_connection.recv_seq_num:
                        cwm_connection.inc_recv_seq_num()
                        return cwm
                    
                elif isinstance(message, AcknowledgementMessage):
                    ack = cast(AcknowledgementMessage, message)
                    cwm_connection: CWMConnection = self.outgoing_cwms.get(ack.vehicle_id)
                    if cwm_connection != None:
                        cwm_connection.last_use = time.time()

                        # If the acknowledgement message is for the expected
                        # sequence number then we increment the sequence number
                        # and remove the CWM from queue.
                        if ack.sequence_number == cwm_connection.send_seq_num:
                            cwm_connection.inc_send_seq_num()
                            cwm_connection.next_cwm()

                            # Transmit the next CWM if there is one.
                            if len(cwm_connection.cwms) != 0:
                                next_cwm: CollisionWarningMessage = cwm_connection.cwms[0]
                                cwm_connection.transmit_time = time.time()
                                next_cwm.timestamp = time.time()
                                network_sim.broadcast_message(vehicle, next_cwm, get_message_hash(next_cwm))

                else:
                    return message
                
        except Empty:
            return None

    def manage(self, network_sim: NetworkSimulator, vehicle) -> None:

        for key, cwm_connection in list(self.outgoing_cwms.items()):



            # Prune connections that have no CWMs and the connection
            # hasn't been used since the configured connection time.
            if len(cwm_connection.cwms) == 0:
                if(time.time() - cwm_connection.last_use) > CONFIG.CONNECTION_TIME:
                    del self.outgoing_cwms[key]
                
                continue

            # Retransmit CWMs that haven't been acknowledged in the
            # configured retransmission time. Don't update the connection's
            # last used time because the vehicle may have gone out of range,
            # meaning we should eventually terminate the connection.
            if (time.time() - cwm_connection.transmit_time) > CONFIG.RETRANSMIT:
                cwm: CollisionWarningMessage = cwm_connection.cwms[0]
                cwm_connection.transmit_time = time.time()
                cwm.timestamp = time.time()
                network_sim.broadcast_message(vehicle, cwm, get_message_hash(cwm))

def get_message_hash(message: V2VMessage) -> bytes:
        json_bytes = json.dumps(message.to_json(), sort_keys=True).encode('utf-8')
        return hashlib.sha256(json_bytes).digest()
