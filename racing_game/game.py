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
    # RUN (OK Sign)
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    if distance < 0.05: return "RUN"

    # LEFT / RIGHT (Tilt)
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    tilt_x = middle_mcp.x - wrist.x
    if tilt_x > 0.15: return "RIGHT"
    elif tilt_x < -0.15: return "LEFT"

    # STOP (Open Palm)
    fingers_up = 0
    tips, pips = [8, 12, 16, 20], [6, 10, 14, 18]
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            fingers_up += 1
    if fingers_up >= 3: return "STOP"

    return "IDLE"

# --- 2. Pygame Setup ---
pygame.init()

# Constants for road design and car size
WIDTH, HEIGHT = 600, 800
ROAD_WIDTH = 420
CAR_WIDTH, CAR_HEIGHT = 60, 100

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Racing Game")
clock = pygame.time.Clock()

# --- LOAD GRAPHICS ---
try:
    player_img = pygame.image.load("car.png").convert_alpha()
    player_img = pygame.transform.scale(player_img, (CAR_WIDTH, CAR_HEIGHT))
except FileNotFoundError:
    print("Warning: car.png not found. Please save the generated car sprite.")
    player_img = pygame.Surface((CAR_WIDTH, CAR_HEIGHT))
    player_img.fill((255, 50, 50))

# We will use forest green boxes for our obstacles for now
obstacle_img = pygame.Surface((CAR_WIDTH, CAR_WIDTH))
obstacle_img.fill((34, 139, 34)) 

# --- PROGRAMMATIC ROAD SETUP ---
COLOR_ROAD_GREY = (51, 51, 62)
COLOR_DASH_WHITE = (220, 220, 220)
COLOR_YELLOW_LINE = (212, 175, 55)
COLOR_PLAIN_GREEN = (90, 150, 60)

road_surface = pygame.Surface((WIDTH, HEIGHT))

def generate_road_surface(offset_y=0):
    """Draws the scrolling, detailed multi-lane road."""
    road_surface.fill(COLOR_PLAIN_GREEN) # Base shoulders

    # Main dark grey road
    road_x_start = (WIDTH - ROAD_WIDTH) // 2
    pygame.draw.rect(road_surface, COLOR_ROAD_GREY, (road_x_start, 0, ROAD_WIDTH, HEIGHT))

    # Center yellow lines
    center_y_x = WIDTH // 2
    pygame.draw.rect(road_surface, COLOR_YELLOW_LINE, (center_y_x - 4, 0, 3, HEIGHT))
    pygame.draw.rect(road_surface, COLOR_YELLOW_LINE, (center_y_x + 4, 0, 3, HEIGHT))

    # Outer white solid lines
    pygame.draw.rect(road_surface, COLOR_DASH_WHITE, (road_x_start, 0, 5, HEIGHT))
    pygame.draw.rect(road_surface, COLOR_DASH_WHITE, (road_x_start + ROAD_WIDTH - 5, 0, 5, HEIGHT))

    # Lane Dividers (Dashed white lines)
    # Positioned halfway between the center and outer edges for 4 lanes
    lane_dividers = [center_y_x - ROAD_WIDTH // 4, center_y_x + ROAD_WIDTH // 4]
    dash_length = 40
    gap_length = 40
    total_segment_length = dash_length + gap_length

    # Smooth scrolling offset calculation
    current_offset = int(offset_y) % total_segment_length

    for divider_x in lane_dividers:
        # Start drawing from above the screen to prevent lines popping in
        for y in range(-total_segment_length, HEIGHT + total_segment_length, total_segment_length):
            pygame.draw.rect(road_surface, COLOR_DASH_WHITE, 
                             (divider_x - 2, y + current_offset, 4, dash_length))

# Game Variables
player = pygame.Rect(WIDTH // 2 - CAR_WIDTH // 2, HEIGHT - 180, CAR_WIDTH, CAR_HEIGHT)
player_speed = 12
obstacles = []
obstacle_speed = 8
score = 0
font = pygame.font.SysFont(None, 48)

# Smoothing Buffer and Road Offset
gesture_buffer = []
road_offset = 0

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
        score += 1
        road_scroll_speed = obstacle_speed * 1.5
        road_offset = (road_offset + road_scroll_speed)

        # Player Movement, limited to the main grey road
        road_min_x = (WIDTH - ROAD_WIDTH) // 2
        road_max_x = road_min_x + ROAD_WIDTH - CAR_WIDTH

        if most_common_gesture == "LEFT" and player.left > road_min_x:
            player.x -= player_speed
        elif most_common_gesture == "RIGHT" and player.right < road_max_x:
            player.x += player_speed

        # Obstacle Generation
        if random.randint(1, 35) == 1: 
            obs_x = random.randint(road_min_x + 10, road_max_x - 10)
            obstacles.append(pygame.Rect(obs_x, -100, CAR_WIDTH, CAR_WIDTH))

        for obs in obstacles[:]:
            obs.y += obstacle_speed
            if obs.top > HEIGHT:
                obstacles.remove(obs)
            
            # Collision Detection
            if player.colliderect(obs):
                print(f"CRASH! Final Score: {score}")
                score = 0
                obstacles.clear()
                player.x = WIDTH // 2 - CAR_WIDTH // 2

    # --- Drawing the Screen ---
    # Draw the dynamic road
    generate_road_surface(road_offset)
    screen.blit(road_surface, (0, 0))

    # Draw Obstacles (Green boxes)
    for obs in obstacles:
        screen.blit(obstacle_img, (obs.x, obs.y))

    # Draw Player Car
    screen.blit(player_img, (player.x, player.y))

    # Draw UI text
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    cmd_text = font.render(f"Command: {most_common_gesture}", True, (0, 255, 0))
    
    # UI Background boxes for better readability
    txt_bg = pygame.Surface((300, 100))
    txt_bg.set_alpha(150)
    txt_bg.fill((0, 0, 0))
    screen.blit(txt_bg, (10, 10))
    screen.blit(score_text, (20, 20))
    screen.blit(cmd_text, (20, 60))

    if is_paused:
        pause_text = font.render("PAUSED - Show 👌🏻 to Run", True, (255, 200, 0))
        txt_bg_pause = pygame.Surface((440, 60))
        txt_bg_pause.set_alpha(200)
        txt_bg_pause.fill((0, 0, 0))
        screen.blit(txt_bg_pause, (WIDTH//2 - 220, HEIGHT//2 - 30))
        screen.blit(pause_text, (WIDTH//2 - 200, HEIGHT//2 - 20))

    pygame.display.flip()
    clock.tick(30)