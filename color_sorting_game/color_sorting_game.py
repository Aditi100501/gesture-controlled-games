import cv2
import mediapipe as mp
import math
import pygame
import sys
from collections import Counter
import random

# --- 1. MediaPipe Setup ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False, max_num_hands=1,
    min_detection_confidence=0.7, min_tracking_confidence=0.7
)
cap = cv2.VideoCapture(0)

def detect_gesture(hand_landmarks):
    # RUN / PICKUP (OK Sign) - Slightly increased distance for easier picking
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    if distance < 0.06: return "PICK"

    # LEFT / RIGHT (Tilt)
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    tilt_x = middle_mcp.x - wrist.x
    if tilt_x > 0.10: return "RIGHT"
    elif tilt_x < -0.10: return "LEFT"

    # STOP / DROP (Open Palm)
    fingers_up = 0
    tips, pips = [8, 12, 16, 20], [6, 10, 14, 18]
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            fingers_up += 1
    if fingers_up >= 3: return "DROP"

    return "IDLE"

# --- 2. Pygame & Game Setup ---
pygame.init()
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Color Sort")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)

# Colors
RED = (220, 50, 50)
GREEN = (50, 220, 50)
BLUE = (50, 150, 255)
BG_COLOR = (30, 30, 40)
TUBE_COLOR = (200, 200, 200)

# Tube Setup
TUBE_W, TUBE_H = 60, 200
BLOCK_H = TUBE_H // 4 # Each tube holds 4 blocks
spacing = (WIDTH - (4 * TUBE_W)) // 5
tube_rects = [pygame.Rect(spacing * (i+1) + TUBE_W * i, HEIGHT // 2 - 50, TUBE_W, TUBE_H) for i in range(4)]

def generate_level():
    """Generates 3 tubes mixed with 4 blocks of Red, Green, and Blue."""
    colors = [RED]*4 + [GREEN]*4 + [BLUE]*4
    random.shuffle(colors)
    return [colors[0:4], colors[4:8], colors[8:12], []]

tubes = generate_level()
selected_tube_idx = 0
held_color = None
source_tube_idx = None # Remembers where the color came from

# Locks and Timers
turn_locked = False
action_locked = False
last_action_time = 0
gesture_buffer = []

def check_win(tubes):
    for t in tubes:
        if len(t) > 0:
            if len(t) != 4 or len(set(t)) != 1:
                return False
    return True

# --- 3. Main Game Loop ---
while True:
    current_time = pygame.time.get_ticks()

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
    # Move Cursor
    if most_common_gesture in ["LEFT", "RIGHT"]:
        if not turn_locked:
            if most_common_gesture == "LEFT":
                selected_tube_idx = max(0, selected_tube_idx - 1)
            elif most_common_gesture == "RIGHT":
                selected_tube_idx = min(3, selected_tube_idx + 1)
            turn_locked = True
    else:
        turn_locked = False

    # Pick / Drop Logic
    if most_common_gesture == "PICK":
        if not action_locked and held_color is None:
            target_tube = tubes[selected_tube_idx]
            if len(target_tube) > 0:
                held_color = target_tube.pop() 
                source_tube_idx = selected_tube_idx # Remember where it came from
                last_action_time = current_time     # Start the cooldown timer
                action_locked = True

    elif most_common_gesture == "DROP":
        if not action_locked and held_color is not None:
            # COOLDOWN: Must wait 700ms after picking to drop again
            if current_time - last_action_time > 700:
                target_tube = tubes[selected_tube_idx]
                
                # Can drop if tube isn't full AND (is empty OR matches color OR is the original tube)
                if len(target_tube) < 4:
                    if len(target_tube) == 0 or target_tube[-1] == held_color or selected_tube_idx == source_tube_idx:
                        target_tube.append(held_color)
                        held_color = None 
                        source_tube_idx = None
                        last_action_time = current_time
                
                action_locked = True
    else:
        # Unlock actions if hand goes back to IDLE
        if most_common_gesture == "IDLE":
            action_locked = False

    won = check_win(tubes)

    # --- Drawing the Screen ---
    screen.fill(BG_COLOR)

    for i, rect in enumerate(tube_rects):
        pygame.draw.rect(screen, TUBE_COLOR, rect, 3, border_radius=10)
        
        for j, color in enumerate(tubes[i]):
            block_y = rect.bottom - ((j + 1) * BLOCK_H)
            block_rect = pygame.Rect(rect.x + 3, block_y, TUBE_W - 6, BLOCK_H)
            
            if j == 0:
                pygame.draw.rect(screen, color, block_rect, border_bottom_left_radius=7, border_bottom_right_radius=7)
            else:
                pygame.draw.rect(screen, color, block_rect)

        if i == selected_tube_idx:
            sel_rect = rect.inflate(20, 20)
            pygame.draw.rect(screen, (255, 255, 255), sel_rect, 4, border_radius=15)

    if held_color:
        sel_rect = tube_rects[selected_tube_idx]
        held_rect = pygame.Rect(sel_rect.x + 3, sel_rect.top - BLOCK_H - 20, TUBE_W - 6, BLOCK_H)
        pygame.draw.rect(screen, held_color, held_rect)

    cmd_text = font.render(f"Command: {most_common_gesture}", True, (0, 255, 0))
    screen.blit(cmd_text, (20, 20))
    
    status_text = font.render("Held: YES" if held_color else "Held: NO", True, (200, 200, 200))
    screen.blit(status_text, (20, 60))

    if won:
        win_text = font.render("YOU WIN! Restarting...", True, (255, 215, 0))
        screen.blit(win_text, (WIDTH//2 - 180, HEIGHT // 4))
        pygame.display.flip()
        pygame.time.wait(3000)
        tubes = generate_level()
        held_color = None
        source_tube_idx = None
        selected_tube_idx = 0
    else:
        pygame.display.flip()
        
    clock.tick(30)