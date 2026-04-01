import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
import os

# 1. Setup Data Path
dataset_path = 'dataset'
img_size = (150, 150)

print("Reading the images from your folders...")

# 2. Prepare the images (with data augmentation to handle 6 different fruits)
datagen = ImageDataGenerator(
    rescale=1./255, 
    validation_split=0.2,
    rotation_range=20,
    zoom_range=0.2,
    horizontal_flip=True
)

train_data = datagen.flow_from_directory(
    dataset_path,
    target_size=img_size,
    batch_size=16,
    class_mode='categorical',
    subset='training'
)

val_data = datagen.flow_from_directory(
    dataset_path,
    target_size=img_size,
    batch_size=16,
    class_mode='categorical',
    subset='validation'
)

# Print the class order so we know what the AI is thinking
print("AI Classes Learned:", train_data.class_indices)

# 3. Build the Universal CNN
print("Building the AI Model...")
model = Sequential([
    Conv2D(32, (3,3), activation='relu', input_shape=(150, 150, 3)),
    MaxPooling2D(2,2),
    
    Conv2D(64, (3,3), activation='relu'),
    MaxPooling2D(2,2),
    
    Conv2D(128, (3,3), activation='relu'),
    MaxPooling2D(2,2),
    
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(3, activation='softmax') # 3 outputs: Grade A, Grade B, Rejected
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# 4. Train the AI 
print("Training started! Please wait...")
model.fit(train_data, validation_data=val_data, epochs=10)

# 5. Save the brain
model.save('agri_grade_model.h5')
print("Success! Model saved as 'agri_grade_model.h5'.")