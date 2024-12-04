import tensorflow as tf
import numpy as np
import os
import cv2
from tensorflow.keras.preprocessing.image import load_img, img_to_array # type: ignore
from colornamer import get_color_from_rgb  # Assuming this is installed
from math import sqrt

# Path to the model
model_path = "backend\\pattern_recognition_best_model.keras"

# Check if the model file exists
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found: {model_path}. Please ensure the file is in the correct location.")

# Load the trained model
try:
    model = tf.keras.models.load_model(model_path)
except ValueError as e:
    raise ValueError(f"Error loading model: {e}. Ensure the file is a valid .keras model.")

# Class labels
classes = ['checkered', 'dotted', 'floral', 'solid', 'striped', 'zigzag']

# Function to predict pattern from image
def predict_pattern(image_path):
    # Check if the image file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}. Please provide a valid image path.")

    # Load and preprocess the image
    try:
        img = load_img(image_path, target_size=(128, 128))
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
    except Exception as e:
        raise ValueError(f"Error processing image: {e}")

    # Make prediction
    try:
        predictions = model.predict(img_array)
        predicted_class = classes[np.argmax(predictions)]
        confidence = np.max(predictions) * 100
    except Exception as e:
        raise RuntimeError(f"Error during prediction: {e}")

    return predicted_class, confidence


# Function to find closest color name based on RGB values
def get_closest_color_name(rgb_color):
    color_info = get_color_from_rgb(rgb_color)
    return color_info['color_family']


# Function to process image and find dominant/average color
def process_image_and_colors(image_path):
    # Read the image using OpenCV
    img = cv2.imread(image_path)
    
    # Check if the image was loaded correctly
    if img is None:
        raise ValueError("Failed to load image.")

    # Convert image from BGR to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Resize the image for faster processing
    img_resized = cv2.resize(img_rgb, (480, 640))  # Resize for faster processing

    # K-Means Clustering to find the dominant color
    pixels = img_resized.reshape(-1, 3)  # Reshape the image to a list of pixels
    k = 5  # Number of clusters
    _, labels, centers = cv2.kmeans(pixels.astype(np.float32), k, None, 
                                     (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0), 
                                     10, cv2.KMEANS_RANDOM_CENTERS)

    # Get the dominant color (the one with the highest frequency)
    dominant_color = centers[np.argmax(np.bincount(labels.flatten()))]
    dominant_color_name = get_closest_color_name(tuple(dominant_color.astype(int)))

    # Calculate center of the image
    h, w, _ = img_resized.shape
    center_x, center_y = w // 2, h // 2
    size = 100
    cropped_center = img_rgb[center_y - size // 2:center_y + size // 2,
                             center_x - size // 2:center_x + size // 2]

    # Average color of the cropped center
    average_color = cropped_center.mean(axis=(0, 1)).astype(int)
    average_color_name = get_closest_color_name(tuple(average_color))

    return dominant_color, dominant_color_name, average_color, average_color_name


# Main function to process images in folder and display results
def process_images_in_folder():
    # Get the current folder where the script is located
    folder_path = os.path.dirname(os.path.abspath(__file__))

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        
        # Check if it's a file and has a valid image extension
        if os.path.isfile(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                # Process the image and find colors
                dominant_color, dominant_color_name, average_color, average_color_name = process_image_and_colors(file_path)
                
                # Get the pattern prediction
                pattern, confidence = predict_pattern(file_path)

                print(f"File: {file_name}")
                print(f"Pattern: {pattern}, Confidence: {confidence:.2f}%")
                print(f"Dominant Color (RGB): {dominant_color}, Name: {dominant_color_name}")
                print(f"Average Color (RGB): {average_color}, Name: {average_color_name}")
                print("-" * 50)
            except Exception as e:
                print(f"An error occurred for {file_name}: {e}")


# Run the processing function for images in the folder
process_images_in_folder()
