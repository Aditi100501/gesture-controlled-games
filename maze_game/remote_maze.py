import pygame
import sys
import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# --- 1. Web Server & WebSocket Setup ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

current_command = "IDLE"

# 🎮 4-Way Joypad HTML Controller 🎮
CONTROLLER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>4-Way Joypad</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        /* Block text selection and magnifying glass on mobile */
        * {
            -webkit-touch-callout: none; 
            -webkit-user-select: none; 
            user-select: none; 
            outline: none;
        }

        body { 
            margin: 0; padding: 0; 
            background: #cbd5e1; 
            font-family: 'Courier New', Courier, monospace; 
            touch-action: none; display: flex; flex-direction: column; height: 100vh; overflow: hidden;
        }
        
        .screen-area {
            background: #1e293b; color: #10b981; text-align: center; padding: 15px; 
            border-bottom: 4px solid #94a3b8; font-weight: bold; font-size: 1.2rem;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }

        .joypad-container {
            display: flex; flex: 1; align-items: center; justify-content: space-between; padding: 0 40px;
        }

        /* 4-WAY D-PAD (Left Side) */
        .d-pad {
            display: grid; grid-template-columns: 60px 60px 60px; grid-template-rows: 60px 60px 60px; gap: 4px;
        }
        .d-btn {
            background: #334155; border: 2px solid #0f172a;
            box-shadow: 0 6px 0 #0f172a, inset 0 2px 5px rgba(255,255,255,0.1);
            display: flex; justify-content: center; align-items: center;
            font-size: 1.8rem; color: #94a3b8; transition: transform 0.05s, box-shadow 0.05s;
        }
        .d-btn:active {
            transform: translateY(6px); box-shadow: 0 0px 0 #0f172a, inset 0 2px 5px rgba(0,0,0,0.5);
        }
        
        #btn-up { grid-column: 2; grid-row: 1; border-top-left-radius: 15px; border-top-right-radius: 15px; }
        #btn-left { grid-column: 1; grid-row: 2; border-top-left-radius: 15px; border-bottom-left-radius: 15px; }
        .d-center { grid-column: 2; grid-row: 2; background: #1e293b; border: 2px solid #0f172a; }
        #btn-right { grid-column: 3; grid-row: 2; border-top-right-radius: 15px; border-bottom-right-radius: 15px; }
        #btn-down { grid-column: 2; grid-row: 3; border-bottom-left-radius: 15px; border-bottom-right-radius: 15px; }

        /* ACTION BUTTONS (Right Side) */
        .action-pad {
            display: flex; gap: 25px; transform: rotate(-10deg);
        }
        .a-btn-container {
            display: flex; flex-direction: column; align-items: center; gap: 10px;
        }
        .a-btn {
            width: 70px; height: 70px; border-radius: 50%; border: 2px solid #000;
            display: flex; justify-content: center; align-items: center; font-size: 1.5rem;
            transition: transform 0.05s, box-shadow 0.05s;
        }
        
        /* Red Brake Button */
        #btn-brake { 
            background: #ef4444; 
            box-shadow: 0 6px 0 #7f1d1d, inset 0 2px 5px rgba(255,255,255,0.3); 
            margin-top: 20px;
        }
        #btn-brake:active { transform: translateY(6px); box-shadow: 0 0px 0 #7f1d1d; }
        
        /* Yellow Pause Button */
        #btn-pause { 
            background: #facc15; 
            box-shadow: 0 6px 0 #854d0e, inset 0 2px 5px rgba(255,255,255,0.3); 
            margin-top: -20px;
        }
        #btn-pause:active { transform: translateY(6px); box-shadow: 0 0px 0 #854d0e; }
        
        .a-btn-label { font-size: 1.1rem; color: #334155; font-weight: bold; transform: rotate(10deg); }
    </style>
</head>
<body>
    <div class="screen-area" id="status-screen">SYSTEM READY</div>
    
    <div class="joypad-container">
        <!-- 4-Way D-Pad -->
        <div class="d-pad">
            <div class="d-btn" id="btn-up" onpointerdown="sendCommand('UP')" onpointerup="sendCommand('IDLE')">▲</div>
            <div class="d-btn" id="btn-left" onpointerdown="sendCommand('LEFT')" onpointerup="sendCommand('IDLE')">◀</div>
            <div class="d-center"></div>
            <div class="d-btn" id="btn-right" onpointerdown="sendCommand('RIGHT')" onpointerup="sendCommand('IDLE')">▶</div>
            <div class="d-btn" id="btn-down" onpointerdown="sendCommand('DOWN')" onpointerup="sendCommand('IDLE')">▼</div>
        </div>

        <!-- Action Buttons -->
        <div class="action-pad">
            <div class="a-btn-container">
                <div class="a-btn" id="btn-brake" onpointerdown="sendCommand('BRAKE')" onpointerup="sendCommand('IDLE')"></div>
                <div class="a-btn-label">BRAKE</div>
            </div>
            <div class="a-btn-container">
                <div class="a-btn" id="btn-pause" onpointerdown="sendCommand('PAUSE')" onpointerup="sendCommand('IDLE')"></div>
                <div class="a-btn-label">PAUSE</div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        window.oncontextmenu = function(e) { e.preventDefault(); return false; };
        
        function sendCommand(action) {
            socket.emit('game_command', { command: action });
            document.getElementById('status-screen').innerText = "CMD: " + action;
            if(action === 'IDLE') document.getElementById('status-screen').innerText = "SYSTEM READY";
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# --- 2. Pygame & Game Variables ---
pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mobile Joypad Maze")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

try:
    maze_img = pygame.image.load("maze.jpg").convert()
    maze_img = pygame.transform.scale(maze_img, (WIDTH, HEIGHT))
except FileNotFoundError:
    print("Error: Could not find 'maze.jpg'. Please ensure it's in the same folder.")
    sys.exit()

player_pos = [80, 520] 
player_radius = 5  
player_speed = 3   

is_paused = False
pause_locked = False 

print("\n" + "🎮"*25)
print("JOYPAD SERVER STARTED! Go to: http://<YOUR_IP>:5000 on your phone.")
print("Rotate phone sideways (Landscape) for the 4-way Joypad!")
print("🎮"*25 + "\n")

# --- 3. Main Game Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # --- Pause Toggle Logic ---
    if current_command == "PAUSE":
        if not pause_locked:
            is_paused = not is_paused
            pause_locked = True
    else:
        pause_locked = False

    # --- Movement Logic ---
    dx, dy = 0, 0
    if not is_paused:
        if current_command == "UP": dy = -1
        elif current_command == "DOWN": dy = 1
        elif current_command == "LEFT": dx = -1
        elif current_command == "RIGHT": dx = 1
        elif current_command == "BRAKE": 
            dx, dy = 0, 0 # Explicit brake stops movement immediately
        
        if dx != 0 or dy != 0:
            check_x = int(player_pos[0] + dx * (player_speed + 2))
            check_y = int(player_pos[1] + dy * (player_speed + 2))
            
            # Boundary and Color Collision
            if 0 <= check_x < WIDTH and 0 <= check_y < HEIGHT:
                target_color = maze_img.get_at((check_x, check_y))
                if target_color.r > 130 and target_color.g > 130 and target_color.b > 130:
                    player_pos[0] += dx * player_speed
                    player_pos[1] += dy * player_speed

    # --- Drawing the Screen ---
    screen.blit(maze_img, (0, 0))

    # Draw the dot
    pygame.draw.circle(screen, (255, 0, 0), (int(player_pos[0]), int(player_pos[1])), player_radius)

    # UI Text
    cmd_text = font.render(f"Command: {current_command}", True, (0, 255, 0))
    txt_bg = pygame.Surface((300, 50))
    txt_bg.set_alpha(180)
    txt_bg.fill((0, 0, 0))
    screen.blit(txt_bg, (10, 10))
    screen.blit(cmd_text, (20, 20))

    if is_paused:
        pause_text = font.render("PAUSED - Press YELLOW to Resume", True, (255, 200, 0))
        pause_bg = pygame.Surface((450, 50))
        pause_bg.set_alpha(200)
        pause_bg.fill((0, 0, 0))
        screen.blit(pause_bg, (WIDTH//2 - 225, HEIGHT//2 - 25))
        screen.blit(pause_text, (WIDTH//2 - 210, HEIGHT//2 - 10))

    pygame.display.flip()
    clock.tick(30)