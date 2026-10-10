import pygame
import sys
import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# --- 1. Web Server & WebSocket Setup ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

current_command = "IDLE"

# 🚀 Neon Cyberpunk Controller HTML 🚀
CONTROLLER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Neon Tracker Link</title>
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
            background: #090a0f; 
            font-family: 'Courier New', Courier, monospace; 
            touch-action: none; display: flex; flex-direction: column; height: 100vh; overflow: hidden;
            color: #fff;
        }
        
        .header {
            text-align: center; padding: 15px; 
            background: #11131a; border-bottom: 2px solid #00ffcc;
            box-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
            text-transform: uppercase; font-weight: bold; letter-spacing: 3px;
        }

        .status { color: #00ffcc; font-size: 0.9rem; margin-top: 5px; }

        .controls { display: flex; flex-direction: column; flex: 1; padding: 30px; gap: 30px; justify-content: center;}
        .row { display: flex; flex: 1; gap: 30px; }
        
        .btn {
            flex: 1; border-radius: 12px; background: #11131a;
            border: 2px solid #333;
            font-size: 1.2rem; font-weight: bold; letter-spacing: 2px;
            display: flex; flex-direction: column; justify-content: center; align-items: center; 
            transition: all 0.1s; text-transform: uppercase;
        }
        
        .btn span { font-size: 2.5rem; margin-bottom: 10px; }
        
        /* Neon Glow Effects */
        #btn-left { color: #ff00ff; border-color: #ff00ff; box-shadow: 0 0 10px rgba(255,0,255,0.2); }
        #btn-left:active { background: rgba(255,0,255,0.2); box-shadow: 0 0 20px rgba(255,0,255,0.6); transform: scale(0.95); }
        
        #btn-right { color: #00ffff; border-color: #00ffff; box-shadow: 0 0 10px rgba(0,255,255,0.2); }
        #btn-right:active { background: rgba(0,255,255,0.2); box-shadow: 0 0 20px rgba(0,255,255,0.6); transform: scale(0.95); }
        
        #btn-stop { color: #ff0055; border-color: #ff0055; box-shadow: 0 0 10px rgba(255,0,85,0.2); }
        #btn-stop:active { background: rgba(255,0,85,0.2); box-shadow: 0 0 20px rgba(255,0,85,0.6); transform: scale(0.95); }
        
        #btn-run { color: #00ff55; border-color: #00ff55; box-shadow: 0 0 10px rgba(0,255,85,0.2); }
        #btn-run:active { background: rgba(0,255,85,0.2); box-shadow: 0 0 20px rgba(0,255,85,0.6); transform: scale(0.95); }
    </style>
</head>
<body>
    <div class="header">
        <div>TRACKER UPLINK</div>
        <div class="status" id="status-screen">LINK ESTABLISHED</div>
    </div>
    
    <div class="controls">
        <div class="row">
            <div class="btn" id="btn-left" onpointerdown="sendCommand('LEFT')" onpointerup="sendCommand('IDLE')">
                <span>⚡</span> LEFT
            </div>
            <div class="btn" id="btn-right" onpointerdown="sendCommand('RIGHT')" onpointerup="sendCommand('IDLE')">
                <span>⚡</span> RIGHT
            </div>
        </div>
        <div class="row">
            <div class="btn" id="btn-stop" onpointerdown="sendCommand('STOP')" onpointerup="sendCommand('IDLE')">
                <span>⛔</span> STOP
            </div>
            <div class="btn" id="btn-run" onpointerdown="sendCommand('RUN')" onpointerup="sendCommand('IDLE')">
                <span>🚀</span> RUN
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        window.oncontextmenu = function(e) { e.preventDefault(); return false; };
        
        function sendCommand(action) {
            socket.emit('game_command', { command: action });
            if(action === 'IDLE') {
                document.getElementById('status-screen').innerText = "AWAITING INPUT...";
            } else {
                document.getElementById('status-screen').innerText = "TRANSMITTING: " + action;
            }
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

# --- 2. Pygame HUD Setup ---
pygame.init()
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Command Dashboard")
clock = pygame.time.Clock()

font_large = pygame.font.SysFont("courier", 72, bold=True)
font_small = pygame.font.SysFont("courier", 24)

# Color mapping for the HUD
colors = {
    "IDLE": (100, 100, 100),
    "RUN": (0, 255, 85),
    "STOP": (255, 0, 85),
    "LEFT": (255, 0, 255),
    "RIGHT": (0, 255, 255)
}

print("\n" + "⚡"*25)
print("DASHBOARD SERVER STARTED! Go to: http://<YOUR_IP>:5000 on your phone.")
print("⚡"*25 + "\n")

# --- 3. Main Display Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # --- Drawing the HUD ---
    screen.fill((10, 12, 18)) # Dark slate background

    # Get the color for the current command
    active_color = colors.get(current_command, (255, 255, 255))

    # Draw a decorative scanning box
    pygame.draw.rect(screen, active_color, (50, 50, WIDTH - 100, HEIGHT - 100), 4, border_radius=15)
    
    # Render texts
    header_text = font_small.render("INCOMING COMMAND SIGNAL:", True, (150, 150, 150))
    command_text = font_large.render(f"> {current_command} <", True, active_color)

    # Center the texts
    screen.blit(header_text, (WIDTH // 2 - header_text.get_width() // 2, 100))
    screen.blit(command_text, (WIDTH // 2 - command_text.get_width() // 2, HEIGHT // 2 - 30))

    pygame.display.flip()
    clock.tick(30)