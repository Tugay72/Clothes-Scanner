from flask import Flask, request, jsonify, send_file
import cv2
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array  # type: ignore
import numpy as np
import os
from math import sqrt
from colornamer import get_color_from_rgb
import time
from io import BytesIO
from PIL import Image

app = Flask(__name__)

PROCESSED_IMAGE_DIR = 'images'
os.makedirs(PROCESSED_IMAGE_DIR, exist_ok=True)

# Load pattern recognition model
MODEL_PATH = "pattern_recognition_best_model.keras"
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

model = tf.keras.models.load_model(MODEL_PATH)
classes = ['checkered', 'dotted', 'floral', 'solid', 'striped', 'zigzag']

@app.route('/')
def home():
    return 'Welcome!'

def get_closest_color_name(rgb_color):

    # Check for black
    if all(value <= 60 for value in rgb_color):
        return "black"

    # Check for white
    if all(value >= 240 for value in rgb_color):
        return "white"

    # Get the color info using colornamer for other cases
    color_info = get_color_from_rgb(rgb_color)

    return color_info['color_family']


def predict_pattern(pil_image):
    # Convert PIL Image to NumPy array and preprocess for the model
    img_array = np.array(pil_image.resize((128, 128))) / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    predictions = model.predict(img_array)  # Model prediction
    predicted_class = classes[np.argmax(predictions)]  # Predicted class
    confidence = np.max(predictions) * 100  # Confidence score
    return predicted_class, confidence


@app.route('/process-image', methods=['POST'])
def process_image_route():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    
    # Read the image directly from memory
    image_bytes = BytesIO(image_file.read())
    pil_image = Image.open(image_bytes).convert("RGB")
    
    # Convert PIL image to numpy array for OpenCV processing
    img_rgb = np.array(pil_image)
    
    # Resize for K-Means clustering
    img_resized = cv2.resize(img_rgb, (480, 640))

    # K-Means Clustering to find the dominant color
    pixels = img_resized.reshape(-1, 3)
    k = 5  # Number of clusters
    _, labels, centers = cv2.kmeans(
        pixels.astype(np.float32), k, None, 
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0), 
        10, cv2.KMEANS_RANDOM_CENTERS
    )

    # Get the dominant color
    dominant_color = centers[np.argmax(np.bincount(labels.flatten()))]
    dominant_color_name = get_closest_color_name(tuple(dominant_color.astype(int)))

    # Average color of the cropped center
    h, w, _ = img_rgb.shape
    center_x, center_y = w // 2, h // 2
    size = 100
    cropped_center = img_rgb[center_y - size // 2:center_y + size // 2,
                             center_x - size // 2:center_x + size // 2]
    average_color = cropped_center.mean(axis=(0, 1)).astype(int)
    average_color_name = get_closest_color_name(tuple(average_color))

    # Run pattern recognition on the uploaded image
    pattern, confidence = predict_pattern(pil_image)

    # Return the result
    return jsonify({
        'dominant_color': dominant_color.tolist(),
        'dominant_color_name': dominant_color_name,
        'average_color': average_color.tolist(),
        'average_color_name': average_color_name,
        'pattern': pattern,
        'pattern_confidence': f"{confidence:.2f}%"
    })


@app.route('/processed-image', methods=['GET'])
def get_processed_image():
    processed_image_path = os.path.join(PROCESSED_IMAGE_DIR, 'processed_image.jpg')
    
    # Check if the processed image exists
    if os.path.exists(processed_image_path):
        return send_file(processed_image_path, mimetype='image/jpeg')
    else:
        return jsonify({'error': 'Processed image not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
