class CONFIG:
    # =========================
    # Network Requirements
    # =========================
    COMMUNICATION_RANGE = 300     # meters
    MAX_LATENCY = 0.010           # 10 ms requirement
    BSM_INTERVAL = 0.1            # 100 ms
    CWM_MAX_DELAY = 0.005         # 5 ms
    RETRANSMIT = 0.0005           # 0.5 ms
    CONNECTION_TIME = 0.5         # 500 ms
    PACKET_LOSS = 0.05            # 5% packet loss (0% - 10%)

    # =========================
    # Vehicle Requirements
    # =========================
    MIN_VEHICLES = 10             # minimum 10 vehicles
    HIGHWAY_SPEED = 27.8          # m/s (60+ mph)
    CITY_SPEED = 11.1             # m/s (25 mph)
    COLLISION_TIME_THRESHOLD = 3.0

    VEHICLE_LENGTH = 4.5          # meters
    VEHICLE_WIDTH = 2.0           # meters

    # =========================
    # Physics Parameters
    # =========================
    MAX_DECELERATION = 8.0        # m/s² braking
    MAX_ACCELERATION = 3.0        # m/s² cruising accel

    # =========================
    # Simulation Parameters
    # =========================
    TIMESTEP = 0.00025               # 0.25 ms
    SIMULATION_TIMESTEP = 0.01    # required by simulation_engine

    # =========================
    # Performance / Display
    # =========================
    TARGET_FPS = 10
    SIM_DURATION = 30.0
