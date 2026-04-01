from flask import Flask, render_template, request, send_file, make_response
import numpy as np
import os
import base64
import sqlite3
import cv2
from datetime import datetime
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from defect_calculator import calculate_defect_density
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import time

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

model = load_model('agri_grade_model.h5')
classes = ['Grade A (Fresh)', 'Grade B (Bruised)', 'Rejected (Rotten)']


# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("inspection.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            grade TEXT,
            confidence REAL,
            defect REAL,
            final_grade TEXT,
            price_per_kg REAL,
            weight REAL,
            batch_value REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()


def save_initial_record(grade, confidence, defect, final_grade, price_per_kg):
    conn = sqlite3.connect("inspection.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO inspections 
        (date, grade, confidence, defect, final_grade, price_per_kg, weight, batch_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        grade,
        confidence,
        defect,
        final_grade,
        price_per_kg,
        0,
        0
    ))
    conn.commit()
    conn.close()


def update_batch_value(weight, batch_value):
    conn = sqlite3.connect("inspection.db")
    c = conn.cursor()
    c.execute("""
        UPDATE inspections 
        SET weight=?, batch_value=? 
        WHERE id = (SELECT MAX(id) FROM inspections)
    """, (weight, batch_value))
    conn.commit()
    conn.close()


def get_dashboard_stats():
    conn = sqlite3.connect("inspection.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM inspections")
    total = c.fetchone()[0]

    c.execute("SELECT SUM(batch_value) FROM inspections")
    total_value = c.fetchone()[0]
    total_value = total_value if total_value else 0

    conn.close()
    return total, round(total_value, 2)


# ================= DAILY REVENUE GRAPH =================
@app.route('/daily_revenue_chart')
def daily_revenue_chart():

    conn = sqlite3.connect("inspection.db")
    c = conn.cursor()

    c.execute("""
        SELECT date(date), SUM(batch_value)
        FROM inspections
        WHERE batch_value > 0
        GROUP BY date(date)
        ORDER BY date(date)
    """)

    data = c.fetchall()
    conn.close()

    dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in data]
    revenues = [row[1] for row in data]

    plt.figure(figsize=(8, 4))
    plt.bar(dates, revenues, color="#34a853", width=0.6)
    plt.title("Daily Revenue", fontsize=16, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Revenue (₹)", fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    response = make_response(send_file(img, mimetype='image/png'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ================= MAIN ROUTE =================
@app.route('/', methods=['GET', 'POST'])
def index():

    try:
        if request.method == 'POST':
            action = request.form.get('action')

            if action == "capture_browser":
                image_data = request.form.get("image_data")

                if image_data:
                    header, encoded = image_data.split(",", 1)
                    data = base64.b64decode(encoded)

                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'browser_capture.jpg')
                    with open(filepath, "wb") as f:
                        f.write(data)

                    return process_image(filepath, live=True)

            if action == "upload":
                file = request.files.get('file')

                if file and file.filename != "":
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filepath)

                    return process_image(filepath, live=False)

            if action == "calculate_upload":
                weight = float(request.form.get('weight', 0))
                price_per_kg = float(request.form.get('price_per_kg', 0))
                profit = round(weight * price_per_kg, 2)

                update_batch_value(weight, profit)

                total, total_value = get_dashboard_stats()

                return render_template(
                    'index.html',
                    image_path=request.form.get('image_path'),
                    ai_grade=request.form.get('ai_grade'),
                    defect=request.form.get('defect'),
                    final_grade=request.form.get('final_grade'),
                    confidence=request.form.get('confidence'),
                    price_per_kg=price_per_kg,
                    weight=weight,
                    profit=profit,
                    total=total,
                    total_value=total_value,
                    cache_buster=int(time.time())
                )

            if action == "calculate_live":
                weight = float(request.form.get('live_weight', 0))
                price_per_kg = float(request.form.get('live_price_per_kg', 0))
                profit = round(weight * price_per_kg, 2)

                update_batch_value(weight, profit)

                total, total_value = get_dashboard_stats()

                return render_template(
                    'index.html',
                    live_image_path=request.form.get('live_image_path'),
                    live_ai_grade=request.form.get('live_ai_grade'),
                    live_confidence=request.form.get('live_confidence'),
                    live_defect=request.form.get('live_defect'),
                    live_final_grade=request.form.get('live_final_grade'),
                    live_price_per_kg=price_per_kg,
                    live_weight=weight,
                    live_profit=profit,
                    total=total,
                    total_value=total_value,
                    cache_buster=int(time.time())
                )

        total, total_value = get_dashboard_stats()

        return render_template(
            'index.html',
            total=total,
            total_value=total_value,
            cache_buster=int(time.time())
        )

    except Exception as e:
        print("ERROR:", e)

        total, total_value = get_dashboard_stats()

        return render_template(
            'index.html',
            total=total,
            total_value=total_value,
            error=str(e),
            cache_buster=int(time.time())
        )


# ================= UI TEST ROUTE =================
@app.route('/ui')
def ui_test():
    total, total_value = get_dashboard_stats()
    return render_template(
        "ui_test.html",
        total=total,
        total_value=total_value
    )


# ================= NEW EXTRA PAGES =================
@app.route('/history')
def history():

    conn = sqlite3.connect("inspection.db")
    c = conn.cursor()

    c.execute("""
        SELECT date, grade, confidence, defect, final_grade, batch_value
        FROM inspections
        ORDER BY id DESC
    """)

    data = c.fetchall()
    conn.close()

    return render_template("history.html", data=data)


@app.route('/analytics')
def analytics():

    conn = sqlite3.connect("inspection.db")
    c = conn.cursor()

    c.execute("""
        SELECT final_grade, COUNT(*)
        FROM inspections
        GROUP BY final_grade
    """)

    grade_data = c.fetchall()
    conn.close()

    return render_template("analytics.html", grade_data=grade_data)


@app.route('/about')
def about():
    return render_template("about.html")


# ================= IMAGE PREPROCESSING =================
def preprocess_image_for_prediction(filepath):
    """
    Advanced preprocessing for camera images to improve prediction accuracy:
    1. Read image with OpenCV
    2. Convert to grayscale
    3. Apply Gaussian blur to remove noise
    4. Detect the largest object using contours
    5. Crop the fruit region from background
    6. Resize to (150, 150)
    7. Normalize pixel values (0-1)
    8. Expand dimensions for model prediction
    
    Args:
        filepath: Path to the image file
    
    Returns:
        img_arr: Preprocessed image array ready for model.predict()
    """
    # Step 1: Read image using OpenCV
    img_cv = cv2.imread(filepath)
    
    if img_cv is None:
        raise ValueError(f"Unable to read image from {filepath}")
    
    original_img = img_cv.copy()
    height, width = img_cv.shape[:2]
    
    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Step 3: Apply Gaussian blur to remove noise
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Step 4: Detect the largest object using contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        # If no contours found, use center crop as fallback
        crop_size = min(height, width)
        x_start = (width - crop_size) // 2
        y_start = (height - crop_size) // 2
        x_end = x_start + crop_size
        y_end = y_start + crop_size
        cropped_img = original_img[y_start:y_end, x_start:x_end]
    else:
        # Find the largest contour (the fruit)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Add padding to crop region (10% on each side)
        padding = 0.1
        x_pad = int(w * padding)
        y_pad = int(h * padding)
        
        # Ensure crop region is within image bounds
        x1 = max(0, x - x_pad)
        y1 = max(0, y - y_pad)
        x2 = min(width, x + w + x_pad)
        y2 = min(height, y + h + y_pad)
        
        # Step 5: Crop the fruit region from background
        cropped_img = original_img[y1:y2, x1:x2]
    
    # Convert BGR to RGB for consistency with training data
    cropped_img_rgb = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)
    
    # Step 6: Resize to model input size (150, 150)
    resized_img = cv2.resize(cropped_img_rgb, (150, 150), interpolation=cv2.INTER_AREA)
    
    # Step 7: Normalize pixel values (divide by 255 to get 0-1 range)
    img_arr = resized_img.astype('float32') / 255.0
    
    # Step 8: Expand dimensions for batch prediction
    img_arr = np.expand_dims(img_arr, axis=0)
    
    return img_arr


# ================= IMAGE PROCESSING =================
def process_image(filepath, live=False):

    img_arr = preprocess_image_for_prediction(filepath)

    prediction = model.predict(img_arr, verbose=0)
    idx = np.argmax(prediction)
    confidence = round(float(np.max(prediction)) * 100, 2)

    defect = calculate_defect_density(filepath)

    image_cv = cv2.imread(filepath)

    blur_warning = False
    if image_cv is not None:
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        blur_value = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_warning = blur_value < 100

    if confidence < 60:
        final_grade = "Uncertain - Manual Inspection Required"
        price_per_kg = 0
    elif idx == 2:
        final_grade = "Rejected (Not for Sale)"
        price_per_kg = 0
    elif defect < 5:
        final_grade = "Grade A (Export Quality)"
        price_per_kg = 80
    else:
        final_grade = "Grade B (Local Market)"
        price_per_kg = 30

    save_initial_record(classes[idx], confidence, defect, final_grade, price_per_kg)

    total, total_value = get_dashboard_stats()

    if live:
        return render_template(
            'index.html',
            live_image_path=filepath,
            live_ai_grade=classes[idx],
            live_confidence=confidence,
            live_defect=defect,
            live_final_grade=final_grade,
            live_price_per_kg=price_per_kg,
            blur_warning=blur_warning,
            total=total,
            total_value=total_value
        )

    else:
        return render_template(
            'index.html',
            image_path=filepath,
            ai_grade=classes[idx],
            defect=defect,
            final_grade=final_grade,
            confidence=confidence,
            price_per_kg=price_per_kg,
            blur_warning=blur_warning,
            total=total,
            total_value=total_value
        )


if __name__ == '__main__':
    app.run(debug=True, threaded=True)