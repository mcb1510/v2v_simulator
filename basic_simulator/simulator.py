"""
Easy to understand with lots of comments!
Author: mcb1510
Date: 2025-10-09

What this does:
- Simulates 20+ cars driving around
- Cars avoid each other (adaptive cruise control)
- Shows realistic car shapes (sedan, SUV, compact)
- Displays communication ranges and network connections
- Has pause, add cars, emergency brake features
"""

import pygame
import random
import cars
import draw

# ==============================================================================
# Basic pygame setup and constants
# ==============================================================================

pygame.init()

# Window size
WIDTH = 1200
HEIGHT = 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("V2V Simulator")
clock = pygame.time.Clock()


# ==============================================================================
# Main program
# ==============================================================================

def main():
    """Main program - creates cars and runs the simulation"""
    
    print("=" * 60)
    print("V2V MULTI-VEHICLE SIMULATOR")
    print("=" * 60)
    print("\nInitializing...")
    
    # Create 20 cars with different types
    cars_list= []
    
    print("\nSpawning vehicles:")
    for i in range(5):
        x = random.randint(60, WIDTH - 60)
        y = random.randint(60, HEIGHT - 60)
        
        # Distribute types: 60% autonomous, 25% semi, 15% legacy
        if i < 12:
            car_type = "autonomous"
        elif i < 17:
            car_type = "semi"
        else:
            car_type = "legacy"

        # create car and add to list
        new_car = cars.Car(x, y, car_type)
        cars_list.append(new_car)
        print(f"  Car {i+1}: {car_type}")

    print(f"\n{len(cars_list)} vehicles ready!")
    print("\nControls:")
    print("  SPACE = Pause    R = Ranges    L = Links")
    print("  N = Add Car      E = Emergency Brake")
    print("  G = Resume All   C = Clear")
    print("  Q = Quit")
    print("\nStarting simulation...\n")
    
    # Simulation settings
    running = True
    paused = False
    show_ranges = False
    show_links = False
    
    # Main game loop
    while running:
        dt = clock.tick(60) / 1000.0  # Run at 60 FPS
        fps = clock.get_fps()
        
        # Handle events (keyboard, mouse, etc)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                # Quit
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                
                # Pause/Resume
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    print(f"{'PAUSED' if paused else 'RESUMED'}")
                
                # Toggle communication ranges
                elif event.key == pygame.K_r:
                    show_ranges = not show_ranges
                    print(f"Communication ranges: {'ON' if show_ranges else 'OFF'}")
                
                # Toggle network links
                elif event.key == pygame.K_l:
                    show_links = not show_links
                    print(f"Network links: {'ON' if show_links else 'OFF'}")
                
                # Add new car
                elif event.key == pygame.K_n:
                    x = random.randint(60, WIDTH - 60)
                    y = random.randint(60, HEIGHT - 60)
                    car_type = random.choice(["autonomous", "semi", "legacy"])
                    cars_list.append(cars.Car(x, y, car_type))
                    print(f"Added {car_type} car (Total: {len(cars_list)})")
                
                # Clear all
                elif event.key == pygame.K_c:
                    count = len(cars_list)
                    cars_list.clear()
                    print(f"Cleared {count} cars")
                
                # Emergency brake - STOPS a random car
                elif event.key == pygame.K_e:
                    if cars_list:
                        # Find a car that's not already stopped
                        moving_cars = [c for c in cars_list if not c.emergency_stop]
                        if moving_cars:
                            car = random.choice(moving_cars)
                            car.emergency_brake()
                        else:
                            print("  All cars already stopped!")
                
                # Resume all stopped cars
                elif event.key == pygame.K_g:
                    stopped_count = sum(1 for c in cars_list if c.emergency_stop)
                    for car in cars_list:
                        if car.emergency_stop:
                            car.resume_driving()
                    if stopped_count > 0:
                        print(f"Resumed {stopped_count} stopped cars")
        
        # Update all cars (if not paused)
        if not paused:
            for car in cars_list:
                car.update_car(cars_list, dt)

        # === drawing ===
        screen.fill(draw.BLACK)
        
        # Draw road grid
        for x in range(0, cars.WIDTH, 100):
            pygame.draw.line(screen, draw.DARK_GRAY, (x, 0), (x, cars.HEIGHT), 1)
        for y in range(0, cars.HEIGHT, 100):
            pygame.draw.line(screen, draw.DARK_GRAY, (0, y), (cars.WIDTH, y), 1)

        # Draw network connections (if enabled)
        if show_links:
            for i, car1 in enumerate(cars_list):
                if car1.car_type != "autonomous":
                    continue  # Only autonomous cars can communicate
                for car2 in cars_list[i+1:]:
                    if car2.car_type != "autonomous":
                        continue
                    distance = car1._distance_to(car2)
                    if distance <= cars.COMM_RANGE:
                        draw.draw_connection(screen, car1, car2)

        # Draw all cars
        for car in cars_list:
            car.draw(screen, show_range=show_ranges)
        
        # Draw UI
        draw.draw_info_panel(screen, cars_list, fps, paused)
        draw.draw_controls_panel(screen)
        draw.draw_legend(screen)

        # Update display
        pygame.display.flip()
    
    # Cleanup
    pygame.quit()
    print("\nThanks for using V2V Simulator!")
    print("=" * 60)


# ==============================================================================
# Run the program
# ==============================================================================

if __name__ == "__main__":
    main()