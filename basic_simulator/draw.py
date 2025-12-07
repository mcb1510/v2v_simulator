import pygame
import cars
import math

# Colors
BLACK = (18, 18, 24)
WHITE = (255, 255, 255)
DARK_GRAY = (40, 40, 45)

# Other colors
GREEN = (100, 255, 100)      # Speed indicator
RED = (255, 50, 50)          # Brake lights
YELLOW = (255, 255, 150)     # Headlights

# --------------------------------------------------------------------------
# DRAWING FUNCTIONS - Make the car visible
# --------------------------------------------------------------------------

def draw(car, surface, show_range=False):
    """Draw a car on screen"""

    if show_range and car.car_type == "autonomous":
        draw_comm_range(car, surface)

    draw_simple_car(car, surface)

    if car.speed > 5:
        draw_speed_line(car, surface)

    if car.is_braking or car.emergency_stop:
        draw_brake_lights(car, surface)

    if car.emergency_stop:
        font = pygame.font.SysFont('arial', 10, bold=True)
        text = font.render("STOP", True, RED)
        surface.blit(text, (int(car.x) - 15, int(car.y) - 25))


def draw_comm_range(car, surface):
    range_surface = pygame.Surface((cars.COMM_RANGE*2, cars.COMM_RANGE*2), pygame.SRCALPHA)
    pygame.draw.circle(
        range_surface,
        (*car.color, 20),
        (cars.COMM_RANGE, cars.COMM_RANGE),
        cars.COMM_RANGE,
        1
    )
    surface.blit(range_surface, (int(car.x - cars.COMM_RANGE), int(car.y - cars.COMM_RANGE)))


def draw_simple_car(car, surface):
    angle_rad = math.radians(car.direction)

    nose_x = car.x + car.size * 0.7 * math.cos(angle_rad)
    nose_y = car.y + car.size * 0.7 * math.sin(angle_rad)

    left_angle = angle_rad + 2.5
    left_x = car.x + car.size * 0.5 * math.cos(left_angle)
    left_y = car.y + car.size * 0.5 * math.sin(left_angle)

    right_angle = angle_rad - 2.5
    right_x = car.x + car.size * 0.5 * math.cos(right_angle)
    right_y = car.y + car.size * 0.5 * math.sin(right_angle)

    color = RED if car.emergency_stop else car.color
    points = [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, WHITE, points, 2)

    if car.car_type == "autonomous":
        pygame.draw.circle(surface, car.accent, (int(car.x), int(car.y)), 4)
        pygame.draw.circle(surface, (200, 200, 255), (int(car.x), int(car.y)), 2)


def draw_speed_line(car, surface):
    angle_rad = math.radians(car.direction)
    line_length = min(car.speed * 0.4, 60)
    end_x = car.x + line_length * math.cos(angle_rad)
    end_y = car.y + line_length * math.sin(angle_rad)
    pygame.draw.line(surface, GREEN, (int(car.x), int(car.y)),
                     (int(end_x), int(end_y)), 2)


def draw_brake_lights(car, surface):
    angle_rad = math.radians(car.direction)
    brake_x = car.x - 15 * math.cos(angle_rad)
    brake_y = car.y - 15 * math.sin(angle_rad)

    for radius in [8, 6, 4]:
        alpha = int(150 - radius * 15)
        brake_surface = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
        pygame.draw.circle(brake_surface, (255, 50, 50, alpha),
                           (radius*2, radius*2), radius)
        surface.blit(brake_surface,
                     (int(brake_x) - radius*2, int(brake_y) - radius*2))


# =====================================================================
# DRAW CONNECTIONS (V2V Links)
# =====================================================================

def draw_connection(surface, car1, car2):
    distance = car1._distance_to(car2)

    if distance <= cars.COMM_RANGE:
        strength = 1.0 - (distance / cars.COMM_RANGE)

        color = (
            int(255 * (1 - strength)),
            int(255 * strength),
            50
        )

        pygame.draw.line(surface, color,
                         (int(car1.x), int(car1.y)),
                         (int(car2.x), int(car2.y)), 1)


# =====================================================================
# UI PANELS
# =====================================================================

def draw_info_panel(surface, car_list, fps, paused):
    font = pygame.font.SysFont('consolas', 16)
    font_small = pygame.font.SysFont('consolas', 14)

    panel = pygame.Surface((280, 220), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 180))
    surface.blit(panel, (10, 10))

    y = 20
    title = font.render("V2V SIMULATOR - mcb1510", True, (100, 200, 255))
    surface.blit(title, (20, y))
    y += 30

    autonomous = sum(1 for c in car_list if c.car_type == "autonomous")
    semi = sum(1 for c in car_list if c.car_type == "semi")
    legacy = sum(1 for c in car_list if c.car_type == "legacy")
    stopped = sum(1 for c in car_list if c.emergency_stop)
    avg_speed = sum(c.speed for c in car_list) / len(car_list) if car_list else 0

    lines = [
        f"Total Cars: {len(car_list)}",
        f"Emergency Stopped: {stopped}",
        f"FPS: {int(fps)}",
        f"Status: {'PAUSED' if paused else 'RUNNING'}",
        "",
        "Vehicle Types:",
        f"  Autonomous: {autonomous}",
        f"  Semi-Auto: {semi}",
        f"  Legacy: {legacy}",
        "",
        f"Avg Speed: {avg_speed:.0f} px/s",
    ]

    for line in lines:
        text = font_small.render(line, True, (230, 230, 230))
        surface.blit(text, (20, y))
        y += 18


def draw_controls_panel(surface):
    font = pygame.font.SysFont('consolas', 14)

    panel = pygame.Surface((300, 170), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 180))
    surface.blit(panel, (10, cars.HEIGHT - 180))

    controls = [
        "CONTROLS:",
        "SPACE - Pause/Resume",
        "R - Show/Hide Comm Ranges",
        "L - Show/Hide Network Links",
        "N - Add Random Car",
        "E - Emergency Brake (STOP car)",
        "G - Resume All Stopped Cars",
        "C - Clear All Cars",
        "ESC/Q - Quit",
    ]

    y = cars.HEIGHT - 170
    for line in controls:
        text = font.render(line, True, (200, 200, 200))
        surface.blit(text, (20, y))
        y += 16


def draw_legend(surface):
    font = pygame.font.SysFont('consolas', 14)

    panel = pygame.Surface((280, 140), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 180))
    surface.blit(panel, (cars.WIDTH - 290, 10))

    title = font.render("VEHICLE TYPES", True, (200, 200, 200))
    surface.blit(title, (cars.WIDTH - 280, 20))

    y_start = 50

    pygame.draw.rect(surface, cars.BLUE, (cars.WIDTH - 270, y_start, 20, 20))
    surface.blit(font.render("Autonomous (Full V2V)", True, (230, 230, 230)),
                 (cars.WIDTH - 240, y_start + 2))

    pygame.draw.rect(surface, cars.ORANGE, (cars.WIDTH - 270, y_start + 40, 20, 20))
    surface.blit(font.render("Semi-Auto (Receive Only)", True, (230, 230, 230)),
                 (cars.WIDTH - 240, y_start + 42))

    pygame.draw.rect(surface, cars.GRAY, (cars.WIDTH - 270, y_start + 80, 20, 20))
    surface.blit(font.render("Legacy (No V2V)", True, (230, 230, 230)),
                 (cars.WIDTH - 240, y_start + 82))
