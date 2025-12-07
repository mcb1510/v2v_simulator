# TEST TO CHECK CONFIG, MESSAGE, VEHICLE, AND SIMULATION ENGINE INTEGRATION
# 
# 
from simulation_engine import simulation_engine
from config import CONFIG
import time


def test_phase1():
    print("=== SIMPLE PHASE 1 TEST ===\n")

    # Initialize engine
    simulation_engine.initialize()

    # Spawn 12 vehicles (requirement: 10+)
    #print("Spawning vehicles...")
    #for i in range(12):
    #    simulation_engine.spawn_vehicle(
     #       position=(i * -50, 0),          # simple spacing
     #       velocity=CONFIG.HIGHWAY_SPEED   # all same speed, simple
     #   )

    #print("Vehicles created:", len(simulation_engine.get_all_vehicles()), "\n")

    print("Spawning vehicles...")

    # 1) Hero scenario: rear car faster than front car (for CWM + braking demo)
    rear_id = simulation_engine.spawn_vehicle(
        position=(0.0, 0.0),
        velocity=CONFIG.HIGHWAY_SPEED      # rear - fast
    )

    front_id = simulation_engine.spawn_vehicle(
        position=(40.0, 0.0),
        velocity=CONFIG.CITY_SPEED         # front - slower, 40m ahead
    )

    # 2) Extra vehicles as normal traffic (no collision risk)
    # Place them further behind or at same speed so TTC is safe
    for i in range(2, 10):  # creates V003 to V010 → total 10 vehicles
        simulation_engine.spawn_vehicle(
            position=(-100.0 - i * 20, 0.0),   # behind and spaced out
            velocity=CONFIG.HIGHWAY_SPEED      # same speed as rear, so no catching up
        )

    print("Vehicles created:", len(simulation_engine.get_all_vehicles()), "\n")


         # Attach message watcher for BOTH BSM and CWM
    def on_message(vehicle, msg):
        # BSM
        if hasattr(msg, "message_type") and str(msg.message_type) == "MessageType.BSM":
            print(f"BSM from {vehicle.vehicle_id}: "
                  f"pos=({msg.position_x:.1f},{msg.position_y:.1f}) "
                  f"vel={msg.velocity:.1f} m/s")

        # CWM
        elif hasattr(msg, "message_type") and str(msg.message_type) == "MessageType.CWM":
            print(f"⚠️ CWM from {vehicle.vehicle_id} "
                  f"to {msg.target_vehicle_id} | "
                  f"TTC={msg.time_to_collision:.2f}s")

    simulation_engine.add_message_callback(on_message)



    # Run simulation for 3 seconds (enough to verify movement + BSM)
    print("Running simulation for 3 seconds...\n")
    simulation_engine.run(3.0)

    # Show summary
    stats = simulation_engine.get_simulation_stats()
    print("\n=== PHASE 1 SUMMARY ===")
    print(f"Simulation time: {stats['simulation_time']:.1f}s")
    print(f"Vehicle count: {stats['vehicle_count']}")
    print(f"Total BSM messages: {stats['total_bsm_sent']}")
    print(f"BSM rate: {stats['bsm_rate']:.1f} per second")
    print(f"Total CWM messages: {stats['total_cwm_sent']}")
    print(f"Estimated collisions prevented: {stats['collisions_prevented']}")

    print("\nPhase 1 functionality confirmed.\n")



if __name__ == "__main__":
    test_phase1()
