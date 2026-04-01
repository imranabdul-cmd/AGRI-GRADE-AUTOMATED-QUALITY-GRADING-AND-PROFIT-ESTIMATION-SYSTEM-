import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from defect_calculator import calculate_defect_density
import os

# 1. Load the brain you just trained
model = load_model('agri_grade_model.h5')
classes = ['Grade A (Fresh)', 'Grade B (Bruised)', 'Rejected (Rotten)']

# 2. Start the Camera (0 is usually the built-in webcam)
cap = cv2.VideoCapture(0)

print("Starting Live Agri-Grade Scanner... Press 'q' to exit.")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        break

    # Create a temporary file to run the OpenCV defect scanner
    temp_path = "live_temp.jpg"
    cv2.imwrite(temp_path, frame)

    # 3. Prepare frame for AI Prediction
    img_for_ai = cv2.resize(frame, (150, 150))
    img_array = img_for_ai / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # 4. Run AI and OpenCV simultaneously
    prediction = model.predict(img_array, verbose=0)
    class_idx = np.argmax(prediction)
    ai_grade = classes[class_idx]
    defect_percentage = calculate_defect_density(temp_path)

    # 5. Visual Feedback on Screen
    # Change box color based on grade
    color = (0, 255, 0) if class_idx == 0 else (0, 165, 255) if class_idx == 1 else (0, 0, 255)
    
    cv2.putText(frame, f"AI Grade: {ai_grade}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.putText(frame, f"Defect: {defect_percentage}%", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    
    # Draw a scanning box
    cv2.rectangle(frame, (100, 100), (500, 400), color, 2)
    
    # Display the resulting frame
    cv2.imshow('Agri-Grade Live Industrial Scanner', frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
if os.path.exists(temp_path):
    os.remove(temp_path)