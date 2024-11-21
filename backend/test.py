import tensorflow as tf
import numpy as np
import os
from tensorflow.keras.preprocessing.image import load_img, img_to_array  # type: ignore

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

# Test the model
image_path = r"backend\test_image1.jpg"
image_path2 = r"backend\test_image2.jpg"
image_path3 = r"backend\test_image3.jpg"
image_path5 = r"backend\test_image5.jpg"
image_path6 = r"backend\test_image6.jpg"
image_path7 = r"backend\test_image7.jpg"
image_path8 = r"backend\test_image8.jpg"

try:
    pattern, confidence = predict_pattern(image_path)
    print(f"Pattern: {pattern}, Confidence: {confidence:.2f}%")
    pattern, confidence = predict_pattern(image_path2)
    print(f"Pattern: {pattern}, Confidence: {confidence:.2f}%")
    pattern, confidence = predict_pattern(image_path3)
    print(f"Pattern: {pattern}, Confidence: {confidence:.2f}%")
    pattern, confidence = predict_pattern(image_path5)
    print(f"Pattern: {pattern}, Confidence: {confidence:.2f}%")
    pattern, confidence = predict_pattern(image_path6)
    print(f"Pattern: {pattern}, Confidence: {confidence:.2f}%")
    pattern, confidence = predict_pattern(image_path7)
    print(f"Pattern: {pattern}, Confidence: {confidence:.2f}%")
    pattern, confidence = predict_pattern(image_path8)
    print(f"Pattern: {pattern}, Confidence: {confidence:.2f}%")
except Exception as e:
    print(f"An error occurred: {e}")
