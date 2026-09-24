import cv2
import mediapipe as mp
import math
import pygame
import random
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
    # REEL IN (OK Sign)
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    if distance < 0.06: return "REEL"

    # LEFT / RIGHT (Tilt)
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    tilt_x = middle_mcp.x - wrist.x
    if tilt_x > 0.10: return "RIGHT"
    elif tilt_x < -0.10: return "LEFT"

    # DROP LINE (Open Palm)
    fingers_up = 0
    tips, pips = [8, 12, 16, 20], [6, 10, 14, 18]
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            fingers_up += 1
    if fingers_up >= 3: return "DROP"

    return "IDLE"

# --- 2. Pygame & Game Variables ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Deep Sea Fishing")
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
caught_fish = None # Holds data if a fish is on the line

# Aquatic Life List: [x, y, speed, type (1=Fish, -1=Jellyfish), color]
fishes = []
score = 0
gesture_buffer = []

def spawn_fish():
    is_jelly = random.randint(1, 4) == 1 # 25% chance of jellyfish
    start_x = -50 if random.choice([True, False]) else WIDTH + 50
    depth_y = random.randint(200, HEIGHT - 50)
    speed = random.randint(3, 7)
    if start_x > 0: speed = -speed # Move left if starting on the right
    
    if is_jelly:
        fishes.append([start_x, depth_y, speed, -1, (255, 100, 150)]) # Pink Jellyfish
    else:
        fishes.append([start_x, depth_y, speed, 1, (50, 200, 255)]) # Blue Fish

# Populate starting fish
for _ in range(5): spawn_fish()

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
    # Boat Movement
    if most_common_gesture == "LEFT" and boat_x > boat_width // 2:
        boat_x -= boat_speed
    elif most_common_gesture == "RIGHT" and boat_x < WIDTH - boat_width // 2:
        boat_x += boat_speed

    # Hook Movement
    if most_common_gesture == "DROP" and hook_y < HEIGHT - 20:
        hook_y += hook_speed
    elif most_common_gesture == "REEL" and hook_y > boat_y + 20:
        hook_y -= hook_speed

    # Update Fish
    if random.randint(1, 40) == 1: spawn_fish() # Spawn new fish randomly

    hook_rect = pygame.Rect(boat_x - hook_radius, hook_y - hook_radius, hook_radius*2, hook_radius*2)

    for f in fishes[:]:
        f[0] += f[2] # Move by speed
        
        # Remove if off-screen
        if f[0] < -100 or f[0] > WIDTH + 100:
            fishes.remove(f)
            continue
            
        # Check Collision if hook is empty
        if caught_fish is None:
            fish_rect = pygame.Rect(f[0] - 20, f[1] - 15, 40, 30)
            if hook_rect.colliderect(fish_rect):
                caught_fish = f
                fishes.remove(f)

    # Process Caught Fish
    if caught_fish:
        caught_fish[0] = boat_x # Fish follows hook X
        caught_fish[1] = hook_y # Fish follows hook Y
        
        # If reeled all the way up to the boat
        if hook_y <= boat_y + 30:
            if caught_fish[3] == 1:
                score += 10 # Good fish
            else:
                score -= 10 # Bad jellyfish
            caught_fish = None

    # --- Drawing the Screen ---
    # Draw Sky and Water
    pygame.draw.rect(screen, (135, 206, 235), (0, 0, WIDTH, 120)) # Sky
    pygame.draw.rect(screen, (10, 50, 100), (0, 120, WIDTH, HEIGHT - 120)) # Deep Water

    # Draw Fishing Line
    pygame.draw.line(screen, (200, 200, 200), (boat_x, boat_y), (boat_x, hook_y), 2)

    # Draw Hook
    pygame.draw.circle(screen, (220, 220, 220), (boat_x, int(hook_y)), hook_radius)

    # Draw Fishes (Free swimming)
    for f in fishes:
        color = f[4]
        pygame.draw.ellipse(screen, color, (int(f[0]) - 20, int(f[1]) - 15, 40, 30))
        # Draw a little tail
        tail_x = int(f[0]) + 20 if f[2] < 0 else int(f[0]) - 20
        pygame.draw.polygon(screen, color, [(tail_x, int(f[1])), (tail_x + (10 if f[2] < 0 else -10), int(f[1]) - 10), (tail_x + (10 if f[2] < 0 else -10), int(f[1]) + 10)])

    # Draw Caught Fish on the hook
    if caught_fish:
        color = caught_fish[4]
        pygame.draw.ellipse(screen, color, (int(caught_fish[0]) - 15, int(caught_fish[1]) - 10, 30, 20))

    # Draw Boat
    pygame.draw.rect(screen, (139, 69, 19), (boat_x - boat_width//2, boat_y - boat_height//2, boat_width, boat_height), border_radius=5)

    # UI Text
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    cmd_text = font.render(f"Action: {most_common_gesture}", True, (0, 255, 0))
    
    screen.blit(score_text, (20, 20))
    screen.blit(cmd_text, (20, 60))

    pygame.display.flip()
    clock.tick(30)