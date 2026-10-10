import pygame
import random
import sys
import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# --- 1. Web Server & WebSocket Setup ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

current_command = "IDLE"

# 🌊 Ocean-Themed Mobile Controller HTML 🌊
CONTROLLER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Deep Sea Fishing 🎣</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fredoka+One&display=swap');
        
        body { 
            margin: 0; padding: 0; 
            background: linear-gradient(180deg, #00B4DB 0%, #0083B0 100%);
            color: white; 
            font-family: 'Fredoka One', cursive; 
            touch-action: none; display: flex; flex-direction: column; height: 100vh; overflow: hidden;
        }
        .header {
            text-align: center; padding: 20px 10px; 
            background: rgba(0, 0, 0, 0.3); border-bottom: 4px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        .title { font-size: 2rem; margin: 0; letter-spacing: 2px; color: #FFF; text-shadow: 2px 2px 4px rgba(0,0,0,0.4); }
        .stat { font-size: 1.5rem; margin-top: 10px; color: #FFD700; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
        
        .controls { display: flex; flex-direction: column; flex: 1; padding: 25px; gap: 20px; }
        .row { display: flex; flex: 1; gap: 20px; }
        
        .btn {
            flex: 1; border-radius: 25px; border: 3px solid rgba(255,255,255,0.3);
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(5px);
            font-size: 1.2rem; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.3); 
            display: flex; flex-direction: column; justify-content: center; align-items: center; 
            user-select: none; transition: transform 0.1s, background 0.1s;
        }
        .btn span { font-size: 3.5rem; margin-bottom: 8px; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.3)); }
        .btn:active { 
            transform: translateY(6px); 
            background: rgba(255, 255, 255, 0.25); 
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); 
        }
        
        #btn-left, #btn-right { background: rgba(33, 150, 243, 0.4); border-color: #64B5F6; }
        #btn-left:active, #btn-right:active { background: rgba(33, 150, 243, 0.6); }
        
        #btn-drop { background: rgba(244, 67, 54, 0.4); border-color: #E57373; }
        #btn-drop:active { background: rgba(244, 67, 54, 0.6); }

        #btn-reel { background: rgba(76, 175, 80, 0.4); border-color: #81C784; }
        #btn-reel:active { background: rgba(76, 175, 80, 0.6); }
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">Deep Sea Fishing ⛵</h1>
        <div class="stat">Score: <span id="score">0</span></div>
    </div>
    
    <div class="controls">
        <div class="row">
            <div class="btn" id="btn-left" onpointerdown="sendCommand('LEFT')" onpointerup="sendCommand('IDLE')">
                <span>👈</span> STEER LEFT
            </div>
            <div class="btn" id="btn-right" onpointerdown="sendCommand('RIGHT')" onpointerup="sendCommand('IDLE')">
                <span>👉</span> STEER RIGHT
            </div>
        </div>
        <div class="row">
            <div class="btn" id="btn-drop" onpointerdown="sendCommand('DROP')" onpointerup="sendCommand('IDLE')">
                <span>⚓</span> DROP LINE
            </div>
            <div class="btn" id="btn-reel" onpointerdown="sendCommand('REEL')" onpointerup="sendCommand('IDLE')">
                <span>🎣</span> REEL IN
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        window.oncontextmenu = function(event) { event.preventDefault(); event.stopPropagation(); return false; };
        
        function sendCommand(action) {
            socket.emit('game_command', { command: action });
        }

        socket.on('update_dashboard', function(data) {
            document.getElementById('score').innerText = data.score;
        });
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# --- 2. Pygame & Game Variables ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mobile Deep Sea Fishing")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 40)

# Game Entities
boat_x = WIDTH // 2
boat_y = 100
boat_width, boat_height = 80, 40
boat_speed = 7

hook_y = 120
hook_speed = 6
hook_radius = 8
caught_fish = None 

fishes = []
score = 0
last_broadcasted_score = 0

def spawn_fish():
    is_jelly = random.randint(1, 4) == 1 
    start_x = -50 if random.choice([True, False]) else WIDTH + 50
    depth_y = random.randint(200, HEIGHT - 50)
    speed = random.randint(3, 7)
    if start_x > 0: speed = -speed 
    
    if is_jelly:
        fishes.append([start_x, depth_y, speed, -1, (255, 100, 150)]) # Pink Jellyfish
    else:
        fishes.append([start_x, depth_y, speed, 1, (50, 200, 255)]) # Blue Fish

for _ in range(5): spawn_fish()

print("\n" + "🌊"*25)
print("SERVER STARTED! Go to: http://<YOUR_IP>:5000 on your phone.")
print("🌊"*25 + "\n")

# --- 3. Main Game Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # --- Game Logic ---
    # Boat Movement
    if current_command == "LEFT" and boat_x > boat_width // 2:
        boat_x -= boat_speed
    elif current_command == "RIGHT" and boat_x < WIDTH - boat_width // 2:
        boat_x += boat_speed

    # Hook Movement
    if current_command == "DROP" and hook_y < HEIGHT - 20:
        hook_y += hook_speed
    elif current_command == "REEL" and hook_y > boat_y + 20:
        hook_y -= hook_speed

    # Update Fish
    if random.randint(1, 40) == 1: spawn_fish() 

    hook_rect = pygame.Rect(boat_x - hook_radius, hook_y - hook_radius, hook_radius*2, hook_radius*2)

    for f in fishes[:]:
        f[0] += f[2] 
        
        if f[0] < -100 or f[0] > WIDTH + 100:
            fishes.remove(f)
            continue
            
        if caught_fish is None:
            fish_rect = pygame.Rect(f[0] - 20, f[1] - 15, 40, 30)
            if hook_rect.colliderect(fish_rect):
                caught_fish = f
                fishes.remove(f)

    # Process Caught Fish
    if caught_fish:
        caught_fish[0] = boat_x 
        caught_fish[1] = hook_y 
        
        # If reeled all the way up to the boat
        if hook_y <= boat_y + 30:
            if caught_fish[3] == 1:
                score += 10 # Good fish
            else:
                score -= 10 # Bad jellyfish
            caught_fish = None

    # Broadcast score to phone only when it changes to save bandwidth
    if score != last_broadcasted_score:
        socketio.emit('update_dashboard', {'score': score})
        last_broadcasted_score = score

    # --- Drawing the Screen ---
    pygame.draw.rect(screen, (135, 206, 235), (0, 0, WIDTH, 120)) # Sky
    pygame.draw.rect(screen, (10, 50, 100), (0, 120, WIDTH, HEIGHT - 120)) # Deep Water

    pygame.draw.line(screen, (200, 200, 200), (boat_x, boat_y), (boat_x, hook_y), 2)
    pygame.draw.circle(screen, (220, 220, 220), (boat_x, int(hook_y)), hook_radius)

    for f in fishes:
        color = f[4]
        pygame.draw.ellipse(screen, color, (int(f[0]) - 20, int(f[1]) - 15, 40, 30))
        tail_x = int(f[0]) + 20 if f[2] < 0 else int(f[0]) - 20
        pygame.draw.polygon(screen, color, [(tail_x, int(f[1])), (tail_x + (10 if f[2] < 0 else -10), int(f[1]) - 10), (tail_x + (10 if f[2] < 0 else -10), int(f[1]) + 10)])

    if caught_fish:
        color = caught_fish[4]
        pygame.draw.ellipse(screen, color, (int(caught_fish[0]) - 15, int(caught_fish[1]) - 10, 30, 20))

    pygame.draw.rect(screen, (139, 69, 19), (boat_x - boat_width//2, boat_y - boat_height//2, boat_width, boat_height), border_radius=5)

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    cmd_text = font.render(f"Action: {current_command}", True, (0, 255, 0))
    
    screen.blit(score_text, (20, 20))
    screen.blit(cmd_text, (20, 60))

    pygame.display.flip()
    clock.tick(30)