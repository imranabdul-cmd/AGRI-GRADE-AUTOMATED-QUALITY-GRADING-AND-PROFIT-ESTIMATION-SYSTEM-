import cv2
import numpy as np

def calculate_defect_density(image_path):
    img = cv2.imread(image_path)
    if img is None: return 0.0
    img = cv2.resize(img, (200, 200))
    
    # 1. Focus ONLY on the center of the screen (The "Industrial Gate")
    # This creates a virtual box to ignore the rest of your room
    mask_gate = np.zeros((200, 200), dtype="uint8")
    cv2.rectangle(mask_gate, (40, 40), (160, 160), 255, -1)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 2. Strict Fruit Detection (Filters out the background)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask_fruit = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Combine Gate and Fruit Mask
    active_search_area = cv2.bitwise_and(mask_fruit, mask_gate)

    # 3. Defect Detection (Brown/Black spots)
    lower_defect = np.array([0, 0, 0])
    upper_defect = np.array([180, 255, 40]) # Strictly looks for dark rot
    mask_defect = cv2.inRange(hsv, lower_defect, upper_defect)

    # 4. Final Clean Calculation
    final_defects = cv2.bitwise_and(mask_defect, active_search_area)
    
    fruit_pixels = cv2.countNonZero(active_search_area)
    defect_pixels = cv2.countNonZero(final_defects)

    if fruit_pixels == 0: return 0.0
    return round((defect_pixels / fruit_pixels) * 100, 2)