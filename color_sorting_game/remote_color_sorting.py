import pygame
import sys
import random
import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# --- 1. Web Server & WebSocket Setup ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

current_command = "IDLE"
moves_count = 0

# 🍬 Vibrant Candy Mobile Controller HTML 🍬
CONTROLLER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Candy Color Sort 🍭</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap');
        
        body { 
            margin: 0; padding: 0; 
            background: #FFF5EB; /* Bright warm cream */
            font-family: 'Nunito', sans-serif; 
            touch-action: none; display: flex; flex-direction: column; height: 100vh; overflow: hidden;
        }
        .header {
            text-align: center; padding: 20px 10px; 
            background: white; border-bottom: 6px solid #FFD166;
            box-shadow: 0 6px 15px rgba(255, 150, 0, 0.15);
            border-bottom-left-radius: 35px; border-bottom-right-radius: 35px;
        }
        .title { font-size: 2rem; margin: 0; letter-spacing: 1px; color: #FF6392; text-transform: uppercase; }
        .stat { font-size: 1.3rem; margin-top: 5px; color: #FFAA00; font-weight: bold; }
        
        .controls { display: flex; flex-direction: column; flex: 1; padding: 25px; gap: 20px; }
        .row { display: flex; flex: 1; gap: 20px; }
        
        .btn {
            flex: 1; border-radius: 30px; 
            background: white;
            font-size: 1.5rem; font-weight: bold; 
            box-shadow: 0 8px 0px rgba(0,0,0,0.1); 
            display: flex; flex-direction: column; justify-content: center; align-items: center; 
            user-select: none; transition: transform 0.1s, box-shadow 0.1s;
        }
        .btn span { font-size: 3.5rem; margin-bottom: 8px; }
        .btn:active { 
            transform: translateY(8px); 
            box-shadow: 0 0px 0px rgba(0,0,0,0); 
        }
        
        /* Vibrant borders and text for each button */
        #btn-left { color: #4DC3FF; border: 5px solid #4DC3FF; }
        #btn-right { color: #4DC3FF; border: 5px solid #4DC3FF; }
        #btn-pick { color: #FFAA00; border: 5px solid #FFD166; }
        #btn-drop { color: #FF6392; border: 5px solid #FF6392; }
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">Candy Sort 🍭</h1>
        <div class="stat">Moves: <span id="moves">0</span></div>
    </div>
    
    <div class="controls">
        <div class="row">
            <div class="btn" id="btn-left" onpointerdown="sendCommand('LEFT')" onpointerup="sendCommand('IDLE')">
                <span>👈</span> LEFT
            </div>
            <div class="btn" id="btn-right" onpointerdown="sendCommand('RIGHT')" onpointerup="sendCommand('IDLE')">
                <span>👉</span> RIGHT
            </div>
        </div>
        <div class="row">
            <div class="btn" id="btn-pick" onpointerdown="sendCommand('PICK')" onpointerup="sendCommand('IDLE')">
                <span>🤌</span> PICK
            </div>
            <div class="btn" id="btn-drop" onpointerdown="sendCommand('DROP')" onpointerup="sendCommand('IDLE')">
                <span>🫳</span> DROP
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
            document.getElementById('moves').innerText = data.moves;
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

# --- 2. Pygame & Vibrant Setup ---
pygame.init()
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Candy Color Sort")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 36, bold=True)
title_font = pygame.font.SysFont("arial", 52, bold=True)

# 🍬 Saturated, Vibrant Colors 🍬
CANDY_PINK = (255, 99, 146)   # Punchy Pink
CANDY_BLUE = (77, 195, 255)   # Electric Cyan
CANDY_YELLOW = (255, 209, 102) # Bright Mango
BG_COLOR = (255, 245, 235)     # Warm Bright Cream
TUBE_OUTLINE = (255, 255, 255) # Pure white
TEXT_COLOR = (255, 99, 146)    

TUBE_W, TUBE_H = 70, 240
BLOCK_H = TUBE_H // 4
spacing = (WIDTH - (4 * TUBE_W)) // 5
tube_rects = [pygame.Rect(spacing * (i+1) + TUBE_W * i, HEIGHT // 2 - 50, TUBE_W, TUBE_H) for i in range(4)]

def generate_level():
    colors = [CANDY_PINK]*4 + [CANDY_BLUE]*4 + [CANDY_YELLOW]*4
    random.shuffle(colors)
    return [colors[0:4], colors[4:8], colors[8:12], []]

tubes = generate_level()
selected_tube_idx = 0
held_color = None
source_tube_idx = None

turn_locked = False
action_locked = False
last_action_time = 0

def check_win(tubes):
    for t in tubes:
        if len(t) > 0:
            if len(t) != 4 or len(set(t)) != 1:
                return False
    return True

print("\n" + "🍬"*25)
print("SERVER STARTED! Go to: http://<YOUR_IP>:5000 on your phone.")
print("🍬"*25 + "\n")

# --- 3. Main Game Loop ---
while True:
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # --- Game Logic ---
    if current_command in ["LEFT", "RIGHT"]:
        if not turn_locked:
            if current_command == "LEFT":
                selected_tube_idx = max(0, selected_tube_idx - 1)
            elif current_command == "RIGHT":
                selected_tube_idx = min(3, selected_tube_idx + 1)
            turn_locked = True
    else:
        turn_locked = False

    if current_command == "PICK":
        if not action_locked and held_color is None:
            target_tube = tubes[selected_tube_idx]
            if len(target_tube) > 0:
                held_color = target_tube.pop() 
                source_tube_idx = selected_tube_idx 
                last_action_time = current_time     
                action_locked = True
                
                moves_count += 1
                socketio.emit('update_dashboard', {'moves': moves_count})

    elif current_command == "DROP":
        if not action_locked and held_color is not None:
            if current_time - last_action_time > 300:
                target_tube = tubes[selected_tube_idx]
                if len(target_tube) < 4:
                    if len(target_tube) == 0 or target_tube[-1] == held_color or selected_tube_idx == source_tube_idx:
                        target_tube.append(held_color)
                        held_color = None 
                        source_tube_idx = None
                        last_action_time = current_time
                action_locked = True
    else:
        if current_command == "IDLE":
            action_locked = False

    won = check_win(tubes)

    # --- Drawing the Screen ---
    screen.fill(BG_COLOR)
    
    title = title_font.render("CANDY SORT 🍭", True, TEXT_COLOR)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

    for i, rect in enumerate(tube_rects):
        # Draw thick white tube background/outline with a slight drop shadow
        pygame.draw.rect(screen, (230, 220, 210), rect.inflate(20, 20).move(0, 5), border_radius=22) # Shadow
        pygame.draw.rect(screen, TUBE_OUTLINE, rect.inflate(20, 20), border_radius=22) # Outline
        pygame.draw.rect(screen, BG_COLOR, rect, border_radius=12) # Inner hollow
        
        for j, color in enumerate(tubes[i]):
            block_y = rect.bottom - ((j + 1) * BLOCK_H)
            block_rect = pygame.Rect(rect.x + 4, block_y, TUBE_W - 8, BLOCK_H)
            
            if j == 0:
                pygame.draw.rect(screen, color, block_rect, border_bottom_left_radius=8, border_bottom_right_radius=8)
            else:
                pygame.draw.rect(screen, color, block_rect)
            
            # Bright inner shine for the candy effect
            shine = pygame.Rect(rect.x + 12, block_y + 8, 14, BLOCK_H - 16)
            pygame.draw.rect(screen, (255, 255, 255, 150), shine, border_radius=6)

        if i == selected_tube_idx:
            sel_rect = rect.inflate(45, 45)
            pygame.draw.rect(screen, (255, 170, 0), sel_rect, 6, border_radius=35) # Bright orange selector

    if held_color:
        sel_rect = tube_rects[selected_tube_idx]
        held_rect = pygame.Rect(sel_rect.x + 4, sel_rect.top - BLOCK_H - 35, TUBE_W - 8, BLOCK_H)
        pygame.draw.rect(screen, held_color, held_rect, border_radius=8)
        
        shine = pygame.Rect(sel_rect.x + 12, sel_rect.top - BLOCK_H - 27, 14, BLOCK_H - 16)
        pygame.draw.rect(screen, (255, 255, 255, 150), shine, border_radius=6)

    status_str = "Status: Holding Candy 🍬" if held_color else "Status: Ready ✌️"
    status_text = font.render(status_str, True, (255, 170, 0))
    screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, HEIGHT - 100))

    if won:
        win_bg = pygame.Surface((WIDTH, HEIGHT))
        win_bg.set_alpha(220)
        win_bg.fill(BG_COLOR)
        screen.blit(win_bg, (0, 0))
        
        win_text = title_font.render("🎉 YOU WIN! 🎉", True, TEXT_COLOR)
        screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT // 2 - 50))
        pygame.display.flip()
        
        pygame.time.wait(3000)
        tubes = generate_level()
        held_color = None
        source_tube_idx = None
        selected_tube_idx = 0
        moves_count = 0
        socketio.emit('update_dashboard', {'moves': moves_count})
    else:
        pygame.display.flip()
        
    clock.tick(30)