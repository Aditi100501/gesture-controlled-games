# Gesture-Controlled Games

A collection of interactive games controlled using hand gestures through a webcam.

This project combines **Computer Vision, Hand Gesture Recognition, and Game Development** to create controller-free gaming experiences.

## Technologies Used

- Python
- OpenCV
- MediaPipe
- Pygame

## Games

### 1. Gesture Tracker

A basic hand gesture recognition program that detects hand movements using MediaPipe.

**Controls:**
- 👌 OK gesture → RUN
- Tilt hand left → LEFT
- Tilt hand right → RIGHT
- Open palm → STOP

---

### 2. Gesture Maze Game

Navigate through a maze using hand gestures.

**Controls:**
- 👌 OK gesture → Move forward
- Tilt hand left → Turn left
- Tilt hand right → Turn right
- Open palm → Pause

The maze uses an image-based environment and collision detection to keep the player within the maze paths.

---

### 3. Gesture Racing Game

Control a racing car using hand gestures.

**Controls:**
- 👌 OK gesture → Run
- Tilt hand left → Move left
- Tilt hand right → Move right
- Open palm → Pause

The game includes a scrolling road, obstacles, collision detection, and a score system.

---

### 4. Gesture Deep Sea Fishing

Catch fish using hand gestures.

**Controls:**
- 👌 OK gesture → Reel
- Tilt hand left → Move boat left
- Tilt hand right → Move boat right
- Open palm → Drop the hook

Players earn points for catching fish and lose points when catching jellyfish.

---

### 5. Gesture Color Sort

Sort colored blocks into the correct tubes using hand gestures.

**Controls:**
- Tilt hand left → Select previous tube
- Tilt hand right → Select next tube
- 👌 OK gesture → Pick a block
- Open palm → Drop a block

The game detects when all colored blocks have been correctly sorted.

## 📁 Project Structure

```text
gesture-controlled-games/
│
├── README.md
│
├── gesture_tracker/
│   └── tracker.py
│
├── maze_game/
│   ├── maze.jpg
│   └── maze_game.py
│
├── racing_game/
│   ├── car.png
│   ├── game.py
│   └── road.jpg
│
├── fishing_game/
│   └── fishing_game.py
│
└── color_sorting_game/
    └── color_sorting_game.py
