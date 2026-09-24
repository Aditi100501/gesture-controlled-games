import cv2
import mediapipe as mp
import math
import pygame
import sys
from collections import Counter

# --- 1. MediaPipe Setup ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False, max_num_hands=1,
    min_detection_confidence=0.7, min_tracking_confidence=0.7
)
cap = cv2.VideoCapture(0)

def detect_gesture(hand_landmarks):
    # RUN (OK Sign) - Moves forward
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    if distance < 0.05: return "RUN"

    # LEFT / RIGHT (Tilt) 
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    tilt_x = middle_mcp.x - wrist.x
    
    if tilt_x > 0.08: return "RIGHT"
    elif tilt_x < -0.08: return "LEFT"

    # STOP (Open Palm) - Pauses
    fingers_up = 0
    tips, pips = [8, 12, 16, 20], [6, 10, 14, 18]
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            fingers_up += 1
    if fingers_up >= 3: return "STOP"

    return "IDLE"

# --- 2. Pygame & Game Variables ---
pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Maze Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# LOAD IMAGE (Updated to maze.jpg)
try:
    maze_img = pygame.image.load("maze.jpg").convert()
    maze_img = pygame.transform.scale(maze_img, (WIDTH, HEIGHT))
except FileNotFoundError:
    print("Error: Could not find 'maze.jpg'. Please ensure it's in the same folder.")
    sys.exit()

# FORGIVING HITBOX & SPEED
player_pos = [80, 520] 
player_radius = 5  # Smaller dot to fit through easily
player_speed = 3   # Slower speed for better corner control

directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
current_dir_idx = 1 # Start facing RIGHT

gesture_buffer = []
turn_locked = False 

# --- 3. Main Game Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            cap.release()
            sys.exit()

    # --- Vision Processing ---
    success, frame = cap.read()
    if not success: continue
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    raw_gesture = "IDLE"
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            raw_gesture = detect_gesture(hand_landmarks)

    gesture_buffer.append(raw_gesture)
    if len(gesture_buffer) > 5:
        gesture_buffer.pop(0)

    most_common_gesture = Counter(gesture_buffer).most_common(1)[0][0]

    cv2.imshow('Debug Camera', frame)
    cv2.waitKey(1)

    # --- Game Logic ---
    is_paused = (most_common_gesture == "STOP")

    if not is_paused:
        # Handle Turning
        if most_common_gesture in ["LEFT", "RIGHT"]:
            if not turn_locked:
                if most_common_gesture == "LEFT":
                    current_dir_idx = (current_dir_idx - 1) % 4
                elif most_common_gesture == "RIGHT":
                    current_dir_idx = (current_dir_idx + 1) % 4
                turn_locked = True
        else:
            turn_locked = False

        # Handle Moving Forward
        if most_common_gesture == "RUN":
            dx, dy = directions[current_dir_idx]
            
            # Look slightly ahead based only on speed, not radius, to avoid false wall hits
            check_x = int(player_pos[0] + dx * (player_speed + 2))
            check_y = int(player_pos[1] + dy * (player_speed + 2))
            
            if 0 <= check_x < WIDTH and 0 <= check_y < HEIGHT:
                target_color = maze_img.get_at((check_x, check_y))
                
                # MUCH FORGIVING COLLISION: Checks if pixel is generally light-colored
                if target_color.r > 130 and target_color.g > 130 and target_color.b > 130:
                    player_pos[0] += dx * player_speed
                    player_pos[1] += dy * player_speed

    # --- Drawing the Screen ---
    screen.blit(maze_img, (0, 0))

    pygame.draw.circle(screen, (255, 0, 0), (int(player_pos[0]), int(player_pos[1])), player_radius)
    face_dx, face_dy = directions[current_dir_idx]
    end_pos = (int(player_pos[0] + face_dx * 12), int(player_pos[1] + face_dy * 12))
    pygame.draw.line(screen, (0, 0, 255), (int(player_pos[0]), int(player_pos[1])), end_pos, 2)

    cmd_text = font.render(f"Command: {most_common_gesture}", True, (0, 255, 0))
    txt_bg = pygame.Surface((300, 50))
    txt_bg.set_alpha(180)
    txt_bg.fill((0, 0, 0))
    screen.blit(txt_bg, (10, 10))
    screen.blit(cmd_text, (20, 20))

    if is_paused:
        pause_text = font.render("PAUSED - Show 👌🏻 to Move", True, (255, 200, 0))
        screen.blit(pause_text, (WIDTH//2 - 150, HEIGHT//2))

    pygame.display.flip()
    clock.tick(30)