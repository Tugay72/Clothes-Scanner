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

base_color_mapping = {
    "red": "red",
    "orange": "orange",
    "yellow": "yellow",
    "green": "green",
    "blue": "blue",
    "purple": "purple",
    "pink": "pink",
    "brown": "brown",
    "gray": "gray",
    "black": "black",
    "white": "white",
    "khaki": "brown",
    "red violet": "red",
    "olive green": "green",
    "lavender": "purple",
    "dark orange": "orange",
    "steel blue": "blue",
    "slate gray": "gray",
    "peru": "brown",
    "light coral": "pink",
    "misty rose": "pink",
    "chocolate": "brown",
    "lime green": "green",
    "firebrick": "red",
    "medium orchid": "purple",
    "dark sea green": "green",
    "green blue": "blue",
    "violet blue": "purple",
    "yellow green": "yellow",
    "olive": "black",
    "sienna": "brown",
    "yellow orange": "yellow",
    "orange yellow": "orange",
    "blue green": "blue",
    "red orange": "red",
    "green yellow": "green",
    "violet red": "red",
    "grey": "gray",
    "blue violet": "purple",
    "orange red": "orange",
    "yellow ochre": "yellow"
}


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
    # Get the base color from the color family
    color_family = color_info['color_family'].lower()  # Convert to lowercase for consistency
    base_color = base_color_mapping.get(color_family, color_family)  # Default to original if no match

    return base_color;


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

    # Get the first dominant color (most frequent cluster center)
    dominant_color = centers[np.argmax(np.bincount(labels.flatten()))]
    dominant_color_name = get_closest_color_name(tuple(dominant_color.astype(int)))

    # Get the second dominant color (second most frequent cluster center)

    # Sort the cluster centers by frequency
    color_counts = np.bincount(labels.flatten())
    sorted_indices = np.argsort(color_counts)[::-1]  # Sort descending by frequency
    second_dominant_color = centers[sorted_indices[1]]  # Second most frequent color
    second_dominant_color_name = get_closest_color_name(tuple(second_dominant_color.astype(int)))

    third_dominant_color = centers[sorted_indices[2]]  # Third most frequent color
    third_dominant_color_name = get_closest_color_name(tuple(third_dominant_color.astype(int)))

    # Print out the dominant and second dominant color details
    print("Dominant color:", dominant_color_name)
    print("Second dominant color:", second_dominant_color_name)
    print("Second dominant color:", third_dominant_color_name)

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


    dominant_colors_list = []
    if pattern == 'solid':
        dominant_colors_list.append(dominant_color_name)
    elif pattern == 'floral':
        dominant_colors_list.extend([dominant_color_name, second_dominant_color_name, third_dominant_color_name])
    else:
        if dominant_color_name == second_dominant_color_name:
            dominant_colors_list.extend([dominant_color_name, third_dominant_color_name])
        else:
            dominant_colors_list.extend([dominant_color_name, second_dominant_color_name])

    dominant_colors_list = list(dict.fromkeys(dominant_colors_list))
    str_dominant_colors_list = ", ".join(dominant_colors_list)

    print(str_dominant_colors_list)

    # Return the result
    return jsonify({
        'dominant_color': dominant_color.tolist(),
        'dominant_color_name': str_dominant_colors_list,
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
    app.run(host='0.0.0.0', port=5000, debug=True)
