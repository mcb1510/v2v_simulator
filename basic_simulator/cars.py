import math
import random
import draw

WIDTH = 1200
HEIGHT = 700

# Car colors by type
BLUE = (80, 180, 255)        # Autonomous cars
BLUE_DARK = (50, 120, 200)   # Autonomous accent
ORANGE = (255, 180, 80)      # Semi-autonomous cars
ORANGE_DARK = (200, 140, 50) # Semi-autonomous accent
GRAY = (180, 180, 180)       # Legacy cars
GRAY_DARK = (120, 120, 120)  # Legacy accent

# Important distances (in pixels)
COMM_RANGE = 300      # How far cars can talk to each other
SAFE_DISTANCE = 80    # Minimum safe distance between cars
# ==============================================================================
# Car class defines what a car is and what it does
# ==============================================================================

class Car:
    """
    A car that can drive around and avoid other cars
    
    Each car has:
    - Position (x, y)
    - Speed and direction
    - A type (autonomous, semi-autonomous, or legacy)
    - The ability to see other cars and react
    """
    
    def __init__(self, x, y, car_type="autonomous"):
        """
        Create a new car
        Parameters:
        - x, y: Starting position
        - car_type: "autonomous", "semi", or "legacy"
        """
        
        # location of car
        self.x = x
        self.y = y
        
        # movement
        self.speed = random.randint(80, 120)        # Start with random speed
        self.direction = random.randint(0, 360)     # Direction (0 = right, 90 = down)
        self.target_speed = random.randint(100, 150) # Speed we want to reach
        
        # type of car
        self.car_type = car_type
        if car_type == "autonomous":
            self.color = BLUE
            self.accent = BLUE_DARK
            self.size = 28  # Medium size
        elif car_type == "semi":
            self.color = ORANGE
            self.accent = ORANGE_DARK
            self.size = 30  # Bigger
        else:  # legacy
            self.color = GRAY
            self.accent = GRAY_DARK
            self.size = 24  # Smaller 
        
        # car status flags 
        self.is_braking = False
        self.emergency_stop = False  # Flag for emergency brake
        self.has_sensor = (car_type == "autonomous")  # Only autonomous cars have sensors
        
        # AI behavior timer
        self.behavior_timer = 0
        self.lane_change_cooldown = 0
    
    
    # --------------------------------------------------------------------------
    # main update- This runs 60 times per second
    # --------------------------------------------------------------------------
    
    def update_car(self, all_cars, dt):
        """
        Update the car for one frame
        
        Steps:
        1. Check if emergency stopped
        2. Look for cars ahead
        3. Decide what to do (speed up, slow down, change lanes)
        4. Move forward
        5. Handle walls
        
        Parameters:
        - all_cars: List of all other cars
        - dt: Time since last frame (1/60 second)
        """
        
        self.behavior_timer += dt
        self.lane_change_cooldown -= dt
        
        # EMERGENCY STOP: Car is stopped, don't move
        if self.emergency_stop:
            self.speed = max(0, self.speed - 200 * dt)  # Quickly decelerate to 0
            if self.speed < 1:
                self.speed = 0
                self.is_braking = True
            return  # Don't do anything else
        
        # STEP 1: Find the car directly in front of us
        car_ahead = self._find_car_ahead(all_cars)
        
        # STEP 2: Make decisions based on what we see
        if car_ahead:
            distance = self._distance_to(car_ahead)
            
            # TOO CLOSE! Slow down!
            if distance < SAFE_DISTANCE:
                self.target_speed = max(60, car_ahead.speed * 0.9)  # Match their speed but keep moving
                self.is_braking = True
                
            # Safe distance, go normal speed
            else:
                self.target_speed = random.randint(100, 150)
                self.is_braking = False
                
                # Maybe change lanes? (only if we haven't recently)
                if self.lane_change_cooldown <= 0 and random.random() < 0.01:
                    self.direction += random.randint(-10, 10)  # Slight turn
                    self.lane_change_cooldown = 3.0  # Wait 3 seconds before next lane change
        
        else:
            # No car ahead, cruise at normal speed
            self.is_braking = False
            self.target_speed = random.randint(100, 150)
        
        # STEP 3: Smoothly change speed (not instant)
        if self.speed < self.target_speed:
            self.speed += 80 * dt  # Accelerate
        elif self.speed > self.target_speed:
            self.speed -= 100 * dt  # Brake
        
        # Keep speed in valid range (minimum 50 unless emergency stopped)
        self.speed = max(50, min(200, self.speed))
        
        # STEP 4: Move the car forward
        angle_rad = math.radians(self.direction)
        self.x += self.speed * math.cos(angle_rad) * dt
        self.y += self.speed * math.sin(angle_rad) * dt
        
        # STEP 5: Bounce off walls
        margin = 40
        if self.x < margin or self.x > WIDTH - margin:
            self.direction = 180 - self.direction  # Reflect horizontally
            self.speed *= 0.8  # Lose some speed but keep moving
            self.x = max(margin, min(WIDTH - margin, self.x))  # Keep in bounds
        
        if self.y < margin or self.y > HEIGHT - margin:
            self.direction = -self.direction  # Reflect vertically
            self.speed *= 0.8
            self.y = max(margin, min(HEIGHT - margin, self.y))
        
        # Keep direction in 0-360 range
        self.direction = self.direction % 360
    
    
    # --------------------------------------------------------------------------
    # HELPER FUNCTIONS - Used by update()
    # --------------------------------------------------------------------------
    
    def _distance_to(self, other_car):
        """Calculate distance to another car (Pythagorean theorem)"""
        dx = self.x - other_car.x
        dy = self.y - other_car.y
        return math.sqrt(dx*dx + dy*dy)
    
    
    def _find_car_ahead(self, all_cars):
        """
        Find the closest car directly in front of us
        
        How it works:
        1. Look at all cars
        2. Check if they're ahead (using dot product math)
        3. Return the closest one
        """
        closest_car = None
        closest_distance = 9999
        
        # Calculate which direction we're facing
        angle_rad = math.radians(self.direction)
        forward_x = math.cos(angle_rad)
        forward_y = math.sin(angle_rad)
        
        for other_car in all_cars:
            if other_car == self:
                continue  # Don't look at ourselves!
            
            # Vector to other car
            dx = other_car.x - self.x
            dy = other_car.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 10:
                continue  # Too close, probably overlapping
            
            # Is this car ahead of us? (dot product tells us)
            direction_match = (dx * forward_x + dy * forward_y) / distance
            
            if direction_match > 0.7:  # Car is in front (within ~45 degree cone)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_car = other_car
        
        return closest_car
    
    
    def emergency_brake(self):
        """EMERGENCY STOP - Car will come to a complete stop"""
        self.emergency_stop = True
        self.target_speed = 0
        self.is_braking = True
        print(f"  EMERGENCY BRAKE: {self.car_type} car at ({int(self.x)}, {int(self.y)})")
    
    
    def resume_driving(self):
        """Resume driving after emergency stop"""
        self.emergency_stop = False
        self.target_speed = random.randint(80, 120)
        self.is_braking = False
    
    def draw(self, surface, show_range=False):
        draw.draw(self, surface, show_range)