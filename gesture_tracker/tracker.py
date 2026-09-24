import cv2
import mediapipe as mp
import math

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# We only need 1 hand for these controls
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

def detect_gesture(hand_landmarks):
    """Analyzes hand landmarks to return 'RUN', 'STOP', 'LEFT', 'RIGHT', or 'IDLE'."""
    
    # 1. Calculate distance between Thumb Tip (4) and Index Tip (8) for the "RUN" (OK) gesture
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    
    if distance < 0.05: # Threshold for fingers touching
        return "RUN"

    # 2. Check for "LEFT" or "RIGHT" by seeing if the hand is tilted significantly
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    tilt_x = middle_mcp.x - wrist.x
    
    if tilt_x > 0.15:
        return "RIGHT"
    elif tilt_x < -0.15:
        return "LEFT"

    # 3. Check for "STOP" (Open Palm)
    # We check if the tips of the Index, Middle, Ring, and Pinky are above their PIP joints
    fingers_up = 0
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            fingers_up += 1
            
    if fingers_up >= 3: # If 3 or 4 fingers are up, count it as a Stop
        return "STOP"

    return "IDLE"

print("Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        continue

    # Flip horizontally so left is left and right is right
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    current_gesture = "IDLE"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Detect the gesture for the visible hand
            current_gesture = detect_gesture(hand_landmarks)

    # Display the detected gesture on the screen
    cv2.putText(frame, f"Command: {current_gesture}", (20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    cv2.imshow('Gesture Controls', frame)

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()