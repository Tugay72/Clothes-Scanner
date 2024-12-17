import tensorflow as tf

# Load the original model
keras_model = tf.keras.models.load_model("pattern_recognition_best_model.keras")

# Convert the model to TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(keras_model)
tflite_model = converter.convert()

# Save the TFLite model to a file
with open("pattern_recognition_model.tflite", "wb") as f:
    f.write(tflite_model)

print("Model converted to TensorFlow Lite!")