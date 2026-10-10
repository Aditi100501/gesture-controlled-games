import pygame
import random
import sys
import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# --- 1. Web Server & WebSocket Setup ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# This variable replaces our MediaPipe gesture detection
current_command = "IDLE"

# The HTML/CSS/JS for the Mobile Controller (PWA style)
CONTROLLER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Game Controller</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { 
            margin: 0; padding: 0; background-color: #1a1a2e; color: white; 
            font-family: Arial, sans-serif; touch-action: none; /* Prevents pull-to-refresh */
            display: flex; flex-direction: column; height: 100vh; overflow: hidden;
        }
        .row { display: flex; flex: 1; width: 100%; }
        .btn {
            flex: 1; margin: 10px; border-radius: 20px; border: none;
            font-size: 2rem; font-weight: bold; color: white;
            box-shadow: 0 8px 15px rgba(0,0,0,0.5); active: background-color: #555;
            display: flex; justify-content: center; align-items: center; user-select: none;
        }
        #btn-run { background-color: #2ecc71; } /* Green */
        #btn-stop { background-color: #e74c3c; } /* Red */
        #btn-left { background-color: #3498db; } /* Blue */
        #btn-right { background-color: #9b59b6; } /* Purple */
        .btn:active { transform: scale(0.95); opacity: 0.8; }
    </style>
</head>
<body>
    <div class="row">
        <div class="btn" id="btn-run" onpointerdown="sendCommand('RUN')" onpointerup="sendCommand('IDLE')">RUN</div>
        <div class="btn" id="btn-stop" onpointerdown="sendCommand('STOP')" onpointerup="sendCommand('IDLE')">STOP</div>
    </div>
    <div class="row">
        <div class="btn" id="btn-left" onpointerdown="sendCommand('LEFT')" onpointerup="sendCommand('IDLE')">LEFT</div>
        <div class="btn" id="btn-right" onpointerdown="sendCommand('RIGHT')" onpointerup="sendCommand('IDLE')">RIGHT</div>
    </div>

    <script>
        const socket = io();
        
        // Prevent default context menus and zooming on mobile long-press
        window.oncontextmenu = function(event) { event.preventDefault(); event.stopPropagation(); return false; };
        
        function sendCommand(action) {
            socket.emit('game_command', { command: action });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(CONTROLLER_HTML)

@socketio.on('game_command')
def handle_command(data):
    global current_command
    current_command = data['command']

def run_server():
    # Runs the web server on all network interfaces (0.0.0.0) at port 5000
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# Start the web server in a background thread so it doesn't block Pygame
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# --- 2. Pygame Setup ---
pygame.init()
WIDTH, HEIGHT = 600, 800
ROAD_WIDTH = 420
CAR_WIDTH, CAR_HEIGHT = 60, 100

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mobile Controlled Racing Game")
clock = pygame.time.Clock()

# --- LOAD GRAPHICS ---
try:
    player_img = pygame.image.load("car.png").convert_alpha()
    player_img = pygame.transform.scale(player_img, (CAR_WIDTH, CAR_HEIGHT))
except FileNotFoundError:
    player_img = pygame.Surface((CAR_WIDTH, CAR_HEIGHT))
    player_img.fill((255, 50, 50))

obstacle_img = pygame.Surface((CAR_WIDTH, CAR_WIDTH))
obstacle_img.fill((34, 139, 34)) 

# --- PROGRAMMATIC ROAD SETUP ---
COLOR_ROAD_GREY = (51, 51, 62)
COLOR_DASH_WHITE = (220, 220, 220)
COLOR_YELLOW_LINE = (212, 175, 55)
COLOR_PLAIN_GREEN = (90, 150, 60)
road_surface = pygame.Surface((WIDTH, HEIGHT))

def generate_road_surface(offset_y=0):
    road_surface.fill(COLOR_PLAIN_GREEN) 
    road_x_start = (WIDTH - ROAD_WIDTH) // 2
    pygame.draw.rect(road_surface, COLOR_ROAD_GREY, (road_x_start, 0, ROAD_WIDTH, HEIGHT))
    
    center_y_x = WIDTH // 2
    pygame.draw.rect(road_surface, COLOR_YELLOW_LINE, (center_y_x - 4, 0, 3, HEIGHT))
    pygame.draw.rect(road_surface, COLOR_YELLOW_LINE, (center_y_x + 4, 0, 3, HEIGHT))
    
    pygame.draw.rect(road_surface, COLOR_DASH_WHITE, (road_x_start, 0, 5, HEIGHT))
    pygame.draw.rect(road_surface, COLOR_DASH_WHITE, (road_x_start + ROAD_WIDTH - 5, 0, 5, HEIGHT))
    
    lane_dividers = [center_y_x - ROAD_WIDTH // 4, center_y_x + ROAD_WIDTH // 4]
    dash_length, gap_length = 40, 40
    total_segment_length = dash_length + gap_length
    current_offset = int(offset_y) % total_segment_length

    for divider_x in lane_dividers:
        for y in range(-total_segment_length, HEIGHT + total_segment_length, total_segment_length):
            pygame.draw.rect(road_surface, COLOR_DASH_WHITE, (divider_x - 2, y + current_offset, 4, dash_length))

# Game Variables
player = pygame.Rect(WIDTH // 2 - CAR_WIDTH // 2, HEIGHT - 180, CAR_WIDTH, CAR_HEIGHT)
player_speed = 12
obstacles = []
obstacle_speed = 8
score = 0
road_offset = 0
font = pygame.font.SysFont(None, 48)

print("\n" + "="*50)
print("SERVER STARTED! To play, connect your phone to the same WiFi.")
print("Look for your computer's local IP address and go to: http://<YOUR_IP>:5000")
print("="*50 + "\n")

# --- 3. Main Game Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # --- Game Logic ---
    is_paused = (current_command == "STOP")

    if not is_paused:
        score += 1
        road_scroll_speed = obstacle_speed * 1.5
        road_offset += road_scroll_speed

        road_min_x = (WIDTH - ROAD_WIDTH) // 2
        road_max_x = road_min_x + ROAD_WIDTH - CAR_WIDTH

        # Map commands to movement
        if current_command == "LEFT" and player.left > road_min_x:
            player.x -= player_speed
        elif current_command == "RIGHT" and player.right < road_max_x:
            player.x += player_speed

        if random.randint(1, 35) == 1: 
            obs_x = random.randint(road_min_x + 10, road_max_x - 10)
            obstacles.append(pygame.Rect(obs_x, -100, CAR_WIDTH, CAR_WIDTH))

        for obs in obstacles[:]:
            obs.y += obstacle_speed
            if obs.top > HEIGHT:
                obstacles.remove(obs)
            
            if player.colliderect(obs):
                print(f"CRASH! Final Score: {score}")
                score = 0
                obstacles.clear()
                player.x = WIDTH // 2 - CAR_WIDTH // 2

    # --- Drawing the Screen ---
    generate_road_surface(road_offset)
    screen.blit(road_surface, (0, 0))

    for obs in obstacles:
        screen.blit(obstacle_img, (obs.x, obs.y))

    screen.blit(player_img, (player.x, player.y))

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    cmd_text = font.render(f"Command: {current_command}", True, (0, 255, 0))
    
    txt_bg = pygame.Surface((300, 100))
    txt_bg.set_alpha(150)
    txt_bg.fill((0, 0, 0))
    screen.blit(txt_bg, (10, 10))
    screen.blit(score_text, (20, 20))
    screen.blit(cmd_text, (20, 60))

    if is_paused:
        pause_text = font.render("PAUSED - Press RUN on Mobile", True, (255, 200, 0))
        txt_bg_pause = pygame.Surface((480, 60))
        txt_bg_pause.set_alpha(200)
        txt_bg_pause.fill((0, 0, 0))
        screen.blit(txt_bg_pause, (WIDTH//2 - 240, HEIGHT//2 - 30))
        screen.blit(pause_text, (WIDTH//2 - 230, HEIGHT//2 - 20))

    pygame.display.flip()
    clock.tick(30)