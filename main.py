import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import keyboard  # To detect keyboard events
import win32gui  # To get the current window handle
import time

cam = cv2.VideoCapture(0)
capture_hands = mp.solutions.hands.Hands()
drawing_option = mp.solutions.drawing_utils
screen_w, screen_h = pyautogui.size()

def is_touching(landmarks):
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    distance = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5
    return distance < 0.05

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
        key_positions[key] = (j * key_size[0], i * key_size[1])

dragging = False
clicking = False
old_x, old_y = pyautogui.position()
show_keyboard = False
shift_press_count = 0
scrolling = False
last_wrist_y = None
waving = False
wave_direction = None
wave_time = 0

def toggle_keyboard():
    global show_keyboard, shift_press_count
    shift_press_count += 1
    if shift_press_count == 3:
        show_keyboard = not show_keyboard
        shift_press_count = 0

keyboard.on_press_key('shift', lambda _: toggle_keyboard())

while True:
    _, frame = cam.read()
    image_height, image_width, _ = frame.shape
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output_hands = capture_hands.process(rgb_frame)
    all_hands = output_hands.multi_hand_landmarks
    
    if all_hands:
        for hand in all_hands:
            drawing_option.draw_landmarks(frame, hand)
            one_hand_landmarks = hand.landmark
            index_tip = one_hand_landmarks[8]
            x = int(index_tip.x * image_width)
            y = int(index_tip.y * image_height)
            cv2.circle(frame, (x, y), 10, (0, 255, 255), -1)
            screen_x = screen_w / image_width * x
            screen_y = screen_h / image_height * y
            screen_x = smooth_movement(old_x, screen_x)
            screen_y = smooth_movement(old_y, screen_y)
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

            if show_keyboard and y < 300:
                row = y // key_size[1]
                col = x // key_size[0]
                if 0 <= row < len(keys) and 0 <= col < len(keys[row]):
                    key = keys[row][col]
                    if not clicking:
                        pyautogui.typewrite(key)
                        time.sleep(0.1)
                        clicking = True
                else:
                    clicking = False

            if len(one_hand_landmarks) > 9:
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
                            pyautogui.scroll(-1)
                        elif current_wrist_y < last_wrist_y - 0.02:
                            pyautogui.scroll(1)
                        last_wrist_y = current_wrist_y
                else:
                    scrolling = False

            if len(one_hand_landmarks) > 9:
                wrist = one_hand_landmarks[0]
                if wave_direction is None:
                    wave_direction = wrist.y
                elif time.time() - wave_time > 0.5:
                    if wrist.y > wave_direction + 0.1:
                        # pyautogui.press('volumeup')
                        wave_direction = wrist.y
                        wave_time = time.time()
                    elif wrist.y < wave_direction - 0.1:
                        # pyautogui.press('volumedown')
                        wave_direction = wrist.y
                        wave_time = time.time()
    
    cv2.imshow('Hand Control', frame)
    key = cv2.waitKey(10)
    if key == 27:
        break

cam.release()
cv2.destroyAllWindows()
keyboard.unhook_all()
