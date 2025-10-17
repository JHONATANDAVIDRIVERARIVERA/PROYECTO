# ==========================================
#  PROYECTO: CLASIFICACIÓN DE BASURA
#  Autor: Jhonatan David Rivera
#  Descripción: Entrena un modelo CNN con TensorFlow/Keras
# ==========================================

import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt

# ========================
# CONFIGURACIÓN DE RUTAS
# ========================
BASE_DIR = "dataset"  # <-- asegúrate de que esta carpeta contiene las clases (cardboard, glass, etc.)

if not os.path.exists(BASE_DIR):
    raise FileNotFoundError(f"No se encontró la carpeta {BASE_DIR}. Verifica la ruta.")

# ========================
# PREPARACIÓN DE DATOS
# ========================
datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2  # 80% entrenamiento, 20% validación
)

train_data = datagen.flow_from_directory(
    BASE_DIR,
    target_size=(128, 128),
    batch_size=32,
    class_mode='categorical',
    subset='training'
)

val_data = datagen.flow_from_directory(
    BASE_DIR,
    target_size=(128, 128),
    batch_size=32,
    class_mode='categorical',
    subset='validation'
)

print("\n✅ Clases detectadas:", train_data.class_indices)

# ========================
# DEFINICIÓN DEL MODELO CNN
# ========================
model = models.Sequential([
    layers.Input(shape=(128, 128, 3)),

    layers.Conv2D(32, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),

    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),

    layers.Conv2D(128, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),

    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(train_data.num_classes, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# ========================
# ENTRENAMIENTO
# ========================
EPOCHS = 10
history = model.fit(train_data, validation_data=val_data, epochs=EPOCHS)

# ========================
# GUARDAR EL MODELO
# ========================
model.save("garbage_model.h5")
print("\n✅ Modelo guardado como garbage_model.h5")

# ========================
# VISUALIZAR RESULTADOS
# ========================
plt.figure(figsize=(8, 4))
plt.plot(history.history['accuracy'], label='Entrenamiento')
plt.plot(history.history['val_accuracy'], label='Validación')
plt.title('Precisión del modelo')
plt.xlabel('Época')
plt.ylabel('Precisión')
plt.legend()
plt.show()

