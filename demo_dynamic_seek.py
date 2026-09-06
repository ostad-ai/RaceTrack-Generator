import pygame
import math
from track_tools import RaceTrack

# --- Setup Pygame ---
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racetrack Demo - Dynamic Seek")
clock = pygame.time.Clock()

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (0, 100, 255)
ASPHALT = (90, 90, 90)     # Dark gray for the road
GREEN = (150, 255, 150)

# --- Load the Track ---
try:
    track = RaceTrack("racetrack.json")
    print(f"Track loaded! Total length: {track.length:.2f} units")
except FileNotFoundError:
    print("Error: 'racetrack.json' not found. Export a track first!")
    pygame.quit()
    exit()

# --- AUTO-CAMERA: Calculate Bounding Box to center the track perfectly ---
all_points = track.center_line + track.inner_line + track.outer_line
min_x = min(p[0] for p in all_points)
max_x = max(p[0] for p in all_points)
min_y = min(p[1] for p in all_points)
max_y = max(p[1] for p in all_points)

track_w = max_x - min_x
track_h = max_y - min_y
# Scale to fit screen with a 10% margin
scale = min(WIDTH / track_w, HEIGHT / track_h) * 0.8
offset_x = WIDTH / 2 - (min_x + track_w / 2) * scale
offset_y = HEIGHT / 2 - (min_y + track_h / 2) * scale

def world_to_screen(x, y):
    return (int(x * scale + offset_x), int(y * scale + offset_y))

# --- Vehicle with Seek Behavior ---
class Vehicle:
    def __init__(self):
        self.pos = pygame.math.Vector2(track.center_line[0])
        self.vel = pygame.math.Vector2(0, 0)
        self.target_speed = 0.0
        self.max_speed = 400.0
        self.max_force = 800.0  
        self.direction = 1  
        
        # Push it slightly forward so it seeks the correct direction
        self.pos += pygame.math.Vector2(10, 0)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        
        # 1. User controls Target Speed only!
        if keys[pygame.K_UP]:
            self.target_speed = min(self.max_speed, self.target_speed + 200 * dt)
        elif keys[pygame.K_DOWN]:
            self.target_speed = max(-self.max_speed, self.target_speed - 400 * dt) # Now goes up to -400!
        else:
            # Natural friction
            self.target_speed *= 0.99
        
        # 2. Determine Gear (Direction)
        if self.target_speed > 5:
            self.direction = 1
        elif self.target_speed < -5:
            self.direction = -1
            
        # 3. AI Seek Behavior: Look ahead OR behind based on direction
        target_pos = pygame.math.Vector2(track.get_lookahead_point(self.pos.x, self.pos.y, look_ahead_count=3, direction=self.direction))
        
        # 4. Calculate Desired Velocity
        desired_vel = target_pos - self.pos
        if desired_vel.length() > 0:
            desired_vel = desired_vel.normalize() * abs(self.target_speed)
        
        # 5. Calculate Steering Force
        steering = desired_vel - self.vel
        if steering.length() > self.max_force * dt:
            steering.scale_to_length(self.max_force * dt)
            
        # 6. Apply steering
        self.vel += steering
        
        # Clamp velocity to the target speed
        if abs(self.target_speed) > 0 and self.vel.length() > abs(self.target_speed):
            self.vel.scale_to_length(abs(self.target_speed))
            
        self.pos += self.vel * dt
        
        return target_pos

    def draw(self, surface, target):
        # Draw the vehicle (Red Arrow)
        px, py = world_to_screen(self.pos.x, self.pos.y)
        
        # Draw line to the target point it is seeking (Debug visual)
        tx, ty = world_to_screen(target.x, target.y)
        pygame.draw.line(surface, GREEN, (px, py), (tx, ty), 2)
        pygame.draw.circle(surface, GREEN, (tx, ty), 5)
        
        # Draw Vehicle (Bigger now!)
        angle = math.atan2(self.vel.y, self.vel.x)
        # Scale 15 -> 22, 10 -> 15
        p1 = (px + math.cos(angle) * 22, py + math.sin(angle) * 22)
        p2 = (px + math.cos(angle + 2.5) * 15, py + math.sin(angle + 2.5) * 15)
        p3 = (px + math.cos(angle - 2.5) * 15, py + math.sin(angle - 2.5) * 15)
        
        pygame.draw.polygon(surface, RED, [p1, p2, p3])
        pygame.draw.circle(surface, BLACK, (px, py), 6)  # Bigger center dot

# --- Main Game Loop ---
vehicle = Vehicle()
font = pygame.font.SysFont("Arial", 18)

running = True
while running:
    dt = clock.tick(60) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    seek_target = vehicle.update(dt)
    
    # --- Drawing ---
    # 1. Grass background
    screen.fill((100, 200, 100)) 
    
    # 2. Draw the ROAD
    if len(track.outer_line) > 2:
        pts = [world_to_screen(x, y) for x, y in track.outer_line]
        pygame.draw.polygon(screen, ASPHALT, pts, 0) # Fill road area with asphalt
        
    if len(track.inner_line) > 2:
        pts = [world_to_screen(x, y) for x, y in track.inner_line]
        pygame.draw.polygon(screen, (100, 200, 100), pts, 0) # Fill inner area with grass
        
    # 3. Draw the lines on top of the road
    if len(track.inner_line) > 2:
        pts = [world_to_screen(x, y) for x, y in track.inner_line]
        pygame.draw.lines(screen, WHITE, True, pts, 2) # White inner curb
        
    if len(track.outer_line) > 2:
        pts = [world_to_screen(x, y) for x, y in track.outer_line]
        pygame.draw.lines(screen, WHITE, True, pts, 2) # White outer curb
        
    if len(track.center_line) > 2:
        pts = [world_to_screen(x, y) for x, y in track.center_line]
        pygame.draw.lines(screen, (200, 200, 200), True, pts, 1) # Dashed/solid center line (gray)

    # Draw vehicle
    vehicle.draw(screen, seek_target)
    
    # --- HUD ---
    idx, dist = track.get_nearest_point(vehicle.pos.x, vehicle.pos.y)
    progress = (idx / len(track.center_line)) * 100.0
    
    hud_text = f"Speed: {vehicle.target_speed:.1f} | Lap Progress: {progress:.1f}%"
    text_surface = font.render(hud_text, True, BLACK)
    # Add white background for text so it's readable on grass
    text_bg = pygame.Surface((text_surface.get_width() + 10, text_surface.get_height() + 4))
    text_bg.fill(WHITE)
    screen.blit(text_bg, (5, 5))
    screen.blit(text_surface, (10, 7))
    
    instr_text = "UP: Accelerate | DOWN: Brake/Reverse | ESC: Exit"
    instr_surface = font.render(instr_text, True, BLACK)
    instr_bg = pygame.Surface((instr_surface.get_width() + 10, instr_surface.get_height() + 4))
    instr_bg.fill(WHITE)
    screen.blit(instr_bg, (5, HEIGHT - 30))
    screen.blit(instr_surface, (10, HEIGHT - 28))

    pygame.display.flip()

pygame.quit()