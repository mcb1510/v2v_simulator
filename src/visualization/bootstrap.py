from src import SimulationEngine
from src.SimulationEngine.config import CONFIG as SIMULATION_CONFIG


def spawn_vehicles(simulation_engine: SimulationEngine, num_vehicles: int):
    """
    Spawn vehicles for the simulation.

    Args:
        simulation_engine: The simulation engine instance
        num_vehicles: Number of vehicles to create
    """
    import random

    # Vehicle spawn configuration
    ROAD_LENGTH = 1000  # meters
    LANE_WIDTH = 3.5    # meters
    NUM_LANES = 3

    for i in range(num_vehicles):
        # Random position along road
        x_position = random.uniform(0, ROAD_LENGTH)

        # Random lane
        lane = random.randint(0, NUM_LANES - 1)
        y_position = lane * LANE_WIDTH + LANE_WIDTH / 2

        # Random velocity (mix of highway and city speeds)
        if random.random() < 0.7:  # 70% highway speed
            velocity = random.uniform(SIMULATION_CONFIG.HIGHWAY_SPEED * 0.9, SIMULATION_CONFIG.HIGHWAY_SPEED * 1.1)
        else:  # 30% city speed
            velocity = random.uniform(SIMULATION_CONFIG.CITY_SPEED * 0.8, SIMULATION_CONFIG.CITY_SPEED * 1.2)

        # Spawn vehicle (VehicleManager.create_vehicle returns vehicle_id)
        vehicle_id = simulation_engine.vehicle_manager.create_vehicle(
            position=(x_position, y_position),
            velocity=velocity
        )

