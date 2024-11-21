import os
from PIL import Image
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator # type: ignore

# Set a random seed for reproducibility
tf.random.set_seed(42)

# Define image size and paths
image_size = (128, 128)
train_data_dir = 'backend\\datasets\\train'
validation_data_dir = 'backend\\datasets\\validate'

# Step 0: Remove transparency from images
def remove_transparency(image_path, output_path):
    """Removes transparency from an image and saves it to the output path."""
    img = Image.open(image_path).convert("RGBA")
    # Create a white background
    background = Image.new("RGBA", img.size, (255, 255, 255))
    # Merge the image with the background
    img = Image.alpha_composite(background, img).convert("RGB")
    img.save(output_path)

def preprocess_images(directory):
    """Iterates over all images in a directory, removing transparency if present."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('png', 'jpg', 'jpeg')):
                file_path = os.path.join(root, file)
                try:
                    # Create a temporary output file
                    temp_path = file_path
                    remove_transparency(file_path, temp_path)
                    # Replace the original file with the processed file
                    os.replace(temp_path, file_path)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

# Preprocess train and validation images
print("Preprocessing training images...")
preprocess_images(train_data_dir)
print("Preprocessing validation images...")
preprocess_images(validation_data_dir)

# Step 1: Preprocess the images using ImageDataGenerator
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255,
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'  # Avoid artifacts when transforming images
)

validation_datagen = ImageDataGenerator(rescale=1.0 / 255)

# Load the images from the directories
train_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=image_size,
    batch_size=32,
    class_mode='categorical',
    shuffle=True  # Shuffle data for better generalization
)

print(f"Found {train_generator.samples} training images")

validation_generator = validation_datagen.flow_from_directory(
    validation_data_dir,
    target_size=image_size,
    batch_size=32,
    class_mode='categorical',
    shuffle=False  # Keep validation data order consistent
)

print(f"Found {validation_generator.samples} validation images")

# Step 2: Convert to tf.data.Dataset for using repeat()
train_dataset = tf.data.Dataset.from_generator(
    lambda: train_generator, 
    output_signature=(
        tf.TensorSpec(shape=(None, *image_size, 3), dtype=tf.float32),
        tf.TensorSpec(shape=(None, len(train_generator.class_indices)), dtype=tf.float32)
    )
).repeat()  # Repeat the dataset indefinitely

validation_dataset = tf.data.Dataset.from_generator(
    lambda: validation_generator, 
    output_signature=(
        tf.TensorSpec(shape=(None, *image_size, 3), dtype=tf.float32),
        tf.TensorSpec(shape=(None, len(validation_generator.class_indices)), dtype=tf.float32)
    )
)

# Step 3: Define the model
model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 3)),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Conv2D(128, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dropout(0.5),  # Dropout to prevent overfitting
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dropout(0.5),  # Additional dropout for better generalization
    tf.keras.layers.Dense(len(train_generator.class_indices), activation='softmax')
])

# Step 4: Compile the model
model.compile(
    loss='categorical_crossentropy',
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),  # Explicit learning rate
    metrics=['accuracy']
)

# Add callbacks for dynamic learning rate adjustment and early stopping
callbacks = [
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6, verbose=1
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=5, restore_best_weights=True, verbose=1
    ),
    tf.keras.callbacks.ModelCheckpoint(
        'backend/pattern_recognition_best_model.keras', save_best_only=True, verbose=1
    )
]

# Step 5: Train the model using the tf.data.Dataset with repeat()
history = model.fit(
    train_dataset,
    steps_per_epoch=train_generator.samples // train_generator.batch_size,
    epochs=50,  # Increased epochs for better training
    validation_data=validation_dataset,
    validation_steps=validation_generator.samples // validation_generator.batch_size,
    callbacks=callbacks
)

# Step 6: Save the final model
model.save('backend/pattern_recognition_model.keras')

# Step 7: Plot training history (Optional)
import matplotlib.pyplot as plt

# Plot accuracy
plt.figure(figsize=(10, 5))
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.grid()
plt.show()

# Plot loss
plt.figure(figsize=(10, 5))
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.grid()
plt.show()
