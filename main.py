import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import keyboard



cam = cv2.VideoCapture(0)
cv2.namedWindow('Hand Control', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Hand Control', 1280, 720)
capture_hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
drawing_option = mp.solutions.drawing_utils
screen_w, screen_h = pyautogui.size()

def is_touching(landmarks):
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    distance = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5
    return distance < 0.05

def is_fist(landmarks):
    return all(landmarks[i].y > landmarks[i + 3].y for i in range(5, 20, 4))

def smooth_movement(old_pos, new_pos, smoothing_factor=0.2):
    return old_pos * (1 - smoothing_factor) + new_pos * smoothing_factor

keys = [
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
    ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
    ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
]
key_size = (60, 60)
key_positions = {}
for i, row in enumerate(keys):
    for j, key in enumerate(row):
        key_positions[key] = (j * key_size[0] + 50, i * key_size[1] + 50)  # Offset to ensure visibility

dragging = False
clicking = False
old_x, old_y = pyautogui.position()
show_keyboard = False
scrolling = False
last_wrist_y = None

last_toggle_time = 0  # To keep track of the last toggle time
TOGGLE_DELAY = 1  # 1 second delay

def toggle_keyboard():
    global show_keyboard
    global last_toggle_time
    current_time = time.time()
    if current_time - last_toggle_time > TOGGLE_DELAY:
        show_keyboard = not show_keyboard
        last_toggle_time = current_time

while True:
    _, frame = cam.read()
    image_height, image_width, _ = frame.shape
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output_hands = capture_hands.process(rgb_frame)
    all_hands = output_hands.multi_hand_landmarks
    
    if all_hands:
        for hand in all_hands:
            drawing_option.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
            one_hand_landmarks = hand.landmark
            index_tip = one_hand_landmarks[8]
            x = int(index_tip.x * image_width)
            y = int(index_tip.y * image_height)
            cv2.circle(frame, (x, y), 10, (0, 255, 255), -1)
            screen_x = smooth_movement(old_x, screen_w / image_width * x)
            screen_y = smooth_movement(old_y, screen_h / image_height * y)
            pyautogui.moveTo(screen_x, screen_y)
            old_x, old_y = screen_x, screen_y

            if is_touching(one_hand_landmarks):
                if not dragging:
                    pyautogui.mouseDown()
                    dragging = True
            else:
                if dragging:
                    pyautogui.mouseUp()
                    dragging = False
            
            index_pip = one_hand_landmarks[6]
            if index_tip.y < index_pip.y and not clicking:
                pyautogui.click()
                clicking = True
            elif index_tip.y >= index_pip.y:
                clicking = False

            if show_keyboard:
                for key, pos in key_positions.items():
                    cv2.rectangle(frame, pos, (pos[0] + key_size[0], pos[1] + key_size[1]), (255, 0, 0), -1)
                    cv2.putText(frame, key, (pos[0] + 10, pos[1] + 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                if y < 300:
                    row = (y - 50) // key_size[1]
                    col = (x - 50) // key_size[0]
                    if 0 <= row < len(keys) and 0 <= col < len(keys[row]):
                        key = keys[row][col]
                        if not clicking:
                            pyautogui.typewrite(key)
                            time.sleep(0.1)
                            clicking = True
                    else:
                        clicking = False

            thumb_cmc = one_hand_landmarks[2]
            pinky_mcp = one_hand_landmarks[17]
            distance = ((thumb_cmc.x - pinky_mcp.x) ** 2 + (thumb_cmc.y - pinky_mcp.y) ** 2) ** 0.5
            if distance < 0.05:
                if not scrolling:
                    scrolling = True
                    last_wrist_y = one_hand_landmarks[0].y
                else:
                    current_wrist_y = one_hand_landmarks[0].y
                    if current_wrist_y > last_wrist_y + 0.02:
                        pyautogui.scroll(1)
                    elif current_wrist_y < last_wrist_y - 0.02:
                        pyautogui.scroll(-1)
                    last_wrist_y = current_wrist_y
            else:
                scrolling = False

            if is_fist(one_hand_landmarks):
                toggle_keyboard()
    
    cv2.imshow('Hand Control', frame)
    key = cv2.waitKey(10)
    if key == 27:
        break

cam.release()
cv2.destroyAllWindows()
keyboard.unhook_all()
